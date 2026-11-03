from rest_framework.permissions import BasePermission
from apps.usuarios.models import Roles


class PermisoProductos(BasePermission):
    """
    Controla el acceso a los productos según el rol del usuario
    y la propiedad del producto.
    """

    def has_permission(self, request, view):
        # Solo usuarios autenticados pueden acceder a la API.
        if not request.user.is_authenticated:
            return False

        # Únicamente los campesinos pueden publicar productos.
        if view.action == "create":
            return request.user.rol == Roles.CAMPESINO

        # Los usuarios autenticados pueden consultar el catálogo.
        if view.action == "list":
            return True

        # Las demás acciones pasan a la validación del objeto,
        # cuando corresponda.
        return True

    def has_object_permission(self, request, view, obj):
        # Todos los usuarios autenticados pueden consultar productos.
        if view.action == "retrieve":
            return True

        # Solo el campesino propietario puede modificar su producto.
        if view.action in ("update", "partial_update", "destroy"):
            return (
                request.user.rol == Roles.CAMPESINO
                and request.user.id == obj.usuario_id
            )

        # Rechaza cualquier acción no contemplada.
        return False