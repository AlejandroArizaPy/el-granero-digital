from rest_framework.permissions import BasePermission

from apps.usuarios.models import Roles


class PermisoPedidos(BasePermission):
    """Limita lectura y gestión de pedidos a sus comprador y vendedor."""

    # Estas acciones modifican el pedido y solo las puede ejecutar el campesino.
    acciones_vendedor = {"confirmar", "cancelar", "completar"}

    def has_permission(self, request, view):
        # Primero valida sesión y rol; después se revisa la propiedad del pedido.
        if not request.user.is_authenticated:
            return False

        if view.action == "create":
            return request.user.rol == Roles.COMPRADOR

        if view.action in ("list", "retrieve"):
            return request.user.rol in (Roles.ADMIN, Roles.COMPRADOR, Roles.CAMPESINO)

        if view.action in self.acciones_vendedor:
            return request.user.rol == Roles.CAMPESINO

        return False

    def has_object_permission(self, request, view, obj):
        # El queryset también se filtra por propietario; esta verificación protege el objeto puntual.
        if view.action in self.acciones_vendedor:
            return obj.vendedor_id == request.user.pk

        if view.action in ("list", "retrieve"):
            if request.user.rol == Roles.ADMIN:
                return True
            if request.user.rol == Roles.COMPRADOR:
                return obj.comprador_id == request.user.pk
            if request.user.rol == Roles.CAMPESINO:
                return obj.vendedor_id == request.user.pk

        return False
