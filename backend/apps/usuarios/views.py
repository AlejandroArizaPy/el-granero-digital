from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.db import connection, transaction
from django.db.models import Exists, Q
from apps.usuarios.serializers import (
    UsuarioSerializer,
    RegistroUsuarioSerializer,
    AdministrarUsuarioSerializer,
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

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """Devuelve el perfil del usuario autenticado sin requerir su ID en la URL."""
        serializer = DetalleUsuarioSerializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def activar(self, request, pk=None):
        """Activa una cuenta sin exponer campos de permisos Django."""
        usuario = self.get_object()
        if not usuario.is_active:
            usuario.is_active = True
            usuario.save(update_fields=["is_active"])
        return Response(AdministrarUsuarioSerializer(usuario).data)

    @action(detail=True, methods=["post"])
    def desactivar(self, request, pk=None):
        """Desactiva otra cuenta; un administrador no puede desactivarse."""
        usuario = self.get_object()
        if usuario.pk == request.user.pk:
            raise ValidationError("No puedes desactivar tu propia cuenta.")

        with transaction.atomic():
            if connection.features.has_select_for_update:
                # Bloquear todos los ADMIN activos en orden estable serializa
                # desactivaciones concurrentes en bases con bloqueo de filas.
                admins_activos = list(
                    Usuario.objects.select_for_update()
                    .filter(rol=Roles.ADMIN, is_active=True)
                    .order_by("pk")
                    .values_list("pk", flat=True)
                )
                usuario = Usuario.objects.select_for_update().get(pk=usuario.pk)

                if usuario.is_active and usuario.rol == Roles.ADMIN and len(admins_activos) <= 1:
                    raise ValidationError("No se puede desactivar al último administrador activo.")

                if usuario.is_active:
                    usuario.is_active = False
                    usuario.save(update_fields=["is_active"])
            else:
                # SQLite no implementa SELECT FOR UPDATE. Una sola sentencia
                # condicional serializa la escritura y verifica que quede otro ADMIN.
                otros_admins_activos = Usuario.objects.filter(
                    rol=Roles.ADMIN,
                    is_active=True,
                ).exclude(pk=usuario.pk)
                puede_desactivar = ~Q(rol=Roles.ADMIN) | Exists(otros_admins_activos)
                actualizado = Usuario.objects.filter(
                    pk=usuario.pk,
                    is_active=True,
                ).filter(puede_desactivar).update(is_active=False)

                if actualizado == 0:
                    usuario.refresh_from_db()
                    if usuario.is_active and usuario.rol == Roles.ADMIN:
                        raise ValidationError(
                            "No se puede desactivar al último administrador activo."
                        )

            usuario.refresh_from_db()
        return Response(AdministrarUsuarioSerializer(usuario).data)
    
    
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
        
        elif self.action == "list" and self.request.user.rol == Roles.ADMIN:
            return AdministrarUsuarioSerializer

        elif self.action == "retrieve" and self.request.user.rol == Roles.ADMIN:
            return AdministrarUsuarioSerializer

        elif self.action in ("activar", "desactivar"):
            return AdministrarUsuarioSerializer

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
