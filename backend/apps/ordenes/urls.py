from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PedidoViewSet


router = DefaultRouter()
# El router crea listado, detalle y acciones de estado para PedidoViewSet.
router.register("api", PedidoViewSet, basename="pedido")

urlpatterns = [
    path("", include(router.urls)),
]
