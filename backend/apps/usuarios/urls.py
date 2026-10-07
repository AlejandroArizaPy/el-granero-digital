from django.urls import path, include

from rest_framework.routers import DefaultRouter

from . import views


# Genera automáticamente las rutas REST correspondientes al UsuarioViewSet.
router = DefaultRouter()

router.register(
    "api",
    views.UsuarioViewSet,
    basename="usuario"
)


# Incluye en este módulo las rutas generadas por el router.
urlpatterns = [
    path("", include(router.urls)),
]