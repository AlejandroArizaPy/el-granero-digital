from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# Registrar la ruta fija antes de `api/<pk>/` evita que "categorias" se
# interprete como el identificador de un producto.
router.register(r"api/categorias", views.CategoriaViewSet, basename="categoria")
router.register(r"api", views.ProductoViewSet, basename="producto")

urlpatterns = [
    path("crear/", views.crear_producto, name="crear_producto"),
    path("", views.lista_productos, name="lista_productos"),
    path("editar/<int:id>/", views.editar_producto, name="editar_producto"),
    path("eliminar/<int:id>/", views.eliminar_producto, name="eliminar_producto"),
    
    path("", include(router.urls)),
]
