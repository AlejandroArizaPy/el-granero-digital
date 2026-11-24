from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.productos.models import Producto
from apps.usuarios.models import Roles
from .models import DetallePedido, EstadoPedido, Pedido
from .permissions import PermisoPedidos
from .serializers import PedidoSerializer


class PedidoViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = PedidoSerializer
    permission_classes = [PermisoPedidos]

    def get_queryset(self):
        usuario = self.request.user
        pedidos = Pedido.objects.prefetch_related("detalles__producto")

        if not usuario.is_authenticated:
            return pedidos.none()
        if usuario.rol == Roles.COMPRADOR:
            return pedidos.filter(comprador=usuario)
        if usuario.rol == Roles.CAMPESINO:
            return pedidos.filter(vendedor=usuario)
        if usuario.rol == Roles.ADMIN:
            return pedidos
        return pedidos.none()

    def _pedido_bloqueado(self):
        # Bloquea y vuelve a autorizar el pedido dentro de la transacción.
        pedido = get_object_or_404(
            self.get_queryset().select_for_update(),
            pk=self.kwargs["pk"],
        )
        self.check_object_permissions(self.request, pedido)
        return pedido

    def _cambiar_estado(self, pedido, estado_anterior, estado_nuevo):
        # El filtro por estado anterior evita procesar dos veces la misma transición.
        cambiado = Pedido.objects.filter(
            pk=pedido.pk,
            vendedor=self.request.user,
            estado=estado_anterior,
        ).update(estado=estado_nuevo)
        if cambiado != 1:
            raise ValidationError("El pedido ya cambió de estado o no permite esta operación.")

    def _respuesta_pedido(self, pedido):
        # Devuelve el estado persistido después de la operación.
        pedido.refresh_from_db()
        return Response(self.get_serializer(pedido).data)

    @action(detail=True, methods=["post"])
    def confirmar(self, request, pk=None):
        with transaction.atomic():
            pedido = self._pedido_bloqueado()
            if pedido.estado != EstadoPedido.PENDIENTE:
                raise ValidationError("Solo se pueden confirmar pedidos pendientes.")

            # El cambio condicionado reclama la transición; cualquier fallo posterior
            # revierte también este cambio de estado y los descuentos ya aplicados.
            self._cambiar_estado(
                pedido,
                EstadoPedido.PENDIENTE,
                EstadoPedido.EN_PREPARACION,
            )

            # El inventario solo se descuenta al confirmar, dentro de la misma transacción.
            detalles = DetallePedido.objects.filter(pedido=pedido).order_by("producto_id")
            for detalle in detalles:
                actualizado = Producto.objects.filter(
                    pk=detalle.producto_id,
                    activo=True,
                    stock__gte=detalle.cantidad,
                ).update(stock=F("stock") - detalle.cantidad)
                if actualizado != 1:
                    raise ValidationError(
                        {"stock": f"Stock insuficiente o producto inactivo: {detalle.producto_id}."}
                    )

        return self._respuesta_pedido(pedido)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        with transaction.atomic():
            pedido = self._pedido_bloqueado()
            if pedido.estado == EstadoPedido.PENDIENTE:
                estado_anterior = EstadoPedido.PENDIENTE
            elif pedido.estado == EstadoPedido.EN_PREPARACION:
                estado_anterior = EstadoPedido.EN_PREPARACION
            else:
                raise ValidationError("Solo se pueden cancelar pedidos pendientes o en preparación.")

            self._cambiar_estado(pedido, estado_anterior, EstadoPedido.CANCELADO)

            # Solo en preparación hubo descuento que deba restaurarse.
            if estado_anterior == EstadoPedido.EN_PREPARACION:
                detalles = DetallePedido.objects.filter(pedido=pedido).order_by("producto_id")
                for detalle in detalles:
                    actualizado = Producto.objects.filter(pk=detalle.producto_id).update(
                        stock=F("stock") + detalle.cantidad
                    )
                    if actualizado != 1:
                        raise ValidationError(
                            {"stock": f"No se pudo restaurar el producto {detalle.producto_id}."}
                        )

        return self._respuesta_pedido(pedido)

    @action(detail=True, methods=["post"])
    def completar(self, request, pk=None):
        with transaction.atomic():
            pedido = self._pedido_bloqueado()
            if pedido.estado != EstadoPedido.EN_PREPARACION:
                raise ValidationError("Solo se pueden completar pedidos en preparación.")

            self._cambiar_estado(
                pedido,
                EstadoPedido.EN_PREPARACION,
                EstadoPedido.COMPLETADO,
            )

        return self._respuesta_pedido(pedido)
