from rest_framework.permissions import BasePermission
from apps.usuarios.models import Roles


# Define las reglas de acceso del módulo de usuarios según la autenticación,
# el rol del usuario y la relación con el recurso solicitado.
class PermisoUsuarios(BasePermission):
    
    # Controla el acceso general a las acciones del ViewSet antes de consultar un objeto específico.
    def has_permission(self, request, view):
        
        # Permite el registro de nuevos usuarios sin necesidad de autenticación.
        if view.action == 'create':
            return True
        
        # Las demás operaciones requieren que el usuario tenga una sesión autenticada mediante JWT.
        elif not request.user.is_authenticated:
            return False  
        
        # El listado completo de usuarios está reservado para administradores.
        elif view.action == 'list': 
            if request.user.rol == Roles.ADMIN:
                return True
            else:
                return False  

        # Las acciones para cambiar el estado de una cuenta son administrativas.
        elif view.action in ('activar', 'desactivar'):
            return request.user.rol == Roles.ADMIN

        # Un administrador no elimina cuentas desde esta API.
        elif view.action == 'destroy' and request.user.rol == Roles.ADMIN:
            return False
        
        # Las demás acciones autenticadas pasan a la validación sobre el objeto específico.
        else:
            return True
    
    
    # Controla las acciones permitidas sobre cada usuario según el rol
    # y la relación del usuario autenticado con el objeto solicitado.
    def has_object_permission(self, request, view, obj):
        
        # ADMIN consulta y actualiza perfiles ajenos; las acciones de estado se
        # autorizan aparte y la API no permite que ADMIN elimine cuentas.
        if request.user.rol == Roles.ADMIN:
            if view.action in ('retrieve', 'update', 'partial_update'):
                return True
            if view.action in ('activar', 'desactivar'):
                return True
            return False
        
        # Los usuarios normales únicamente pueden operar sobre su propia cuenta.
        elif request.user.id == obj.id:
            return True
        
        # Cualquier intento de acceder a otro usuario es rechazado.
        else:
            return False
