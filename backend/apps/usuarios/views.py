from rest_framework import viewsets
from apps.usuarios.serializers import (
    UsuarioSerializer,
    RegistroUsuarioSerializer,
    ConsultarUsuariosSerializer,
    DetalleUsuarioSerializer,
    ActualizarUsuarioAdminSerializer,
    ActualizarUsuarioSerializer
    )
from apps.usuarios.models import Usuario, Roles
from apps.usuarios.permissions import PermisoUsuarios


# Define las operaciones de la API de usuarios y aplica las reglas de acceso
# y representación de datos según la acción y el rol del usuario.
class UsuarioViewSet(viewsets.ModelViewSet):
    
    serializer_class = UsuarioSerializer
    permission_classes = [PermisoUsuarios]
    
    
    # Limita los usuarios que pueden ser consultados según el rol,
    # evitando que usuarios normales accedan a información de otras cuentas.
    def get_queryset(self):
        
        # Los administradores pueden consultar todos los usuarios para labores de gestión y supervisión.
        if self.request.user.rol == Roles.ADMIN:
            return Usuario.objects.all()
        
        # Por seguridad y privacidad, los usuarios no administradores solo pueden consultar su propia información.
        else:
            return Usuario.objects.filter(id=self.request.user.id)
    
    
    # Selecciona el serializer adecuado para cada acción,
    # permitiendo controlar los datos que se muestran o modifican según la operación y el rol.
    def get_serializer_class(self):
        
        if self.action == "create":
            return RegistroUsuarioSerializer
        
        elif self.action == "list":
            return ConsultarUsuariosSerializer
        
        elif self.action == "retrieve":
            return DetalleUsuarioSerializer
        
        elif self.action == "update" or self.action == "partial_update":
            if self.request.user.rol == Roles.ADMIN:
                return ActualizarUsuarioAdminSerializer
            else:
                return ActualizarUsuarioSerializer
        
        return UsuarioSerializer