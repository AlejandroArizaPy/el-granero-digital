from django.db import transaction
from rest_framework import serializers

from apps.productos.models import Producto
from apps.usuarios.models import Roles
from .models import DetallePedido, EstadoPedido, Pedido


class DetallePedidoSerializer(serializers.ModelSerializer):
    producto = serializers.PrimaryKeyRelatedField(queryset=Producto.objects.all())
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)
    cantidad = serializers.IntegerField(min_value=1)
    precio_unitario = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = DetallePedido
        fields = [
            "producto",
            "producto_nombre",
            "cantidad",
            "precio_unitario",
            "subtotal",
        ]

    def validate_producto(self, producto):
        if not producto.activo:
            raise serializers.ValidationError("El producto no está activo.")
        return producto

    def get_subtotal(self, obj):
        # Usa el precio guardado en el detalle, no el precio actual del catálogo.
        return obj.cantidad * obj.precio_unitario


class PedidoSerializer(serializers.ModelSerializer):
    comprador = serializers.PrimaryKeyRelatedField(read_only=True)
    comprador_nombre = serializers.SerializerMethodField()
    vendedor = serializers.PrimaryKeyRelatedField(read_only=True)
    fecha = serializers.DateTimeField(read_only=True)
    estado = serializers.ChoiceField(choices=EstadoPedido.choices, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    detalles = DetallePedidoSerializer(many=True, allow_empty=False)

    class Meta:
        model = Pedido
        fields = [
            "id",
            "comprador",
            "comprador_nombre",
            "vendedor",
            "fecha",
            "estado",
            "direccion_entrega",
            "total",
            "ciudad",
            "metodo_pago",
            "detalles",
        ]

    def get_comprador_nombre(self, obj):
        # Solo se comparte el nombre; no se exponen correo, documento ni celular.
        nombre = obj.comprador.get_full_name().strip()
        return nombre or f"Comprador #{obj.comprador_id}"

    def validate(self, attrs):
        # Antes de crear, comprueba rol, productos únicos y un único vendedor.
        comprador = self.context["request"].user
        detalles = attrs.get("detalles", [])

        if comprador.rol != Roles.COMPRADOR:
            raise serializers.ValidationError("Solo un comprador puede crear pedidos.")

        producto_ids = [detalle["producto"].pk for detalle in detalles]
        if len(producto_ids) != len(set(producto_ids)):
            raise serializers.ValidationError(
                {"detalles": "No repitas un producto en el mismo pedido."}
            )

        vendedores = {detalle["producto"].usuario_id for detalle in detalles}
        if len(vendedores) != 1:
            raise serializers.ValidationError(
                {"detalles": "Todos los productos deben pertenecer al mismo vendedor."}
            )

        vendedor = detalles[0]["producto"].usuario
        if comprador.pk == vendedor.pk:
            raise serializers.ValidationError("El comprador no puede ser el vendedor.")
        if vendedor.rol != Roles.CAMPESINO:
            raise serializers.ValidationError(
                "Los productos deben pertenecer a un campesino."
            )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # Si falla cualquier inserción, Django revierte el pedido completo.
        comprador = self.context["request"].user
        detalles_data = validated_data.pop("detalles")
        producto_ids = [detalle["producto"].pk for detalle in detalles_data]

        # Se vuelven a bloquear y comprobar productos para guardar precios vigentes.
        productos = {
            producto.pk: producto
            for producto in Producto.objects.select_for_update().filter(
                pk__in=producto_ids,
                activo=True,
            )
        }
        if len(productos) != len(producto_ids):
            raise serializers.ValidationError(
                {"detalles": "Todos los productos deben seguir activos."}
            )

        vendedor_ids = {producto.usuario_id for producto in productos.values()}
        if len(vendedor_ids) != 1:
            raise serializers.ValidationError(
                {"detalles": "Todos los productos deben pertenecer al mismo vendedor."}
            )

        vendedor = next(iter(productos.values())).usuario
        if vendedor.rol != Roles.CAMPESINO or vendedor.pk == comprador.pk:
            raise serializers.ValidationError("El vendedor no es válido para este pedido.")

        pedido = Pedido.objects.create(
            comprador=comprador,
            vendedor=vendedor,
            estado=EstadoPedido.PENDIENTE,
            **validated_data,
        )

        # Crear el pedido no cambia el stock; el descuento ocurre al confirmar.
        for detalle_data in detalles_data:
            producto = productos[detalle_data["producto"].pk]
            DetallePedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=detalle_data["cantidad"],
                precio_unitario=producto.precio,
            )

        # El modelo calcula el total desde los precios históricos guardados.
        pedido.recalcular_total()
        return pedido
