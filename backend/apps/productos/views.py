from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from .forms import ProductoForm
from apps.usuarios.models import Roles
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from .serializers import (
    AdministrarProductoSerializer,
    CategoriaSerializer,
    ProductoSerializer,
)
from apps.productos.models import Categoria, Producto
from apps.productos.permissions import PermisoProductos


@login_required
def crear_producto(request):
    # La vista HTML solo permite crear productos a campesinos autenticados.
    if request.user.rol != Roles.CAMPESINO:
        return HttpResponseForbidden()

    if request.method == "POST":
        formulario = ProductoForm(request.POST, request.FILES)

        if formulario.is_valid():
            producto = formulario.save(commit=False)
            producto.usuario = request.user
            producto.save()

            return redirect("lista_productos")

    else:
        formulario = ProductoForm()

    return render(request, "productos/crear_producto.html", {
        "formulario": formulario
    })
    
def lista_productos(request):
    # No se muestran productos que el vendedor haya desactivado.
    productos = Producto.objects.filter(activo=True)

    return render(request, "productos/lista_productos.html", {
        "productos": productos
    })

@login_required
def editar_producto(request, id):
    if request.user.rol != Roles.CAMPESINO:
        return HttpResponseForbidden()

    # Buscar por dueño evita que un campesino edite productos ajenos.
    producto = get_object_or_404(Producto, id=id, usuario=request.user)

    if request.method == "POST":
        formulario = ProductoForm(
            request.POST,
            request.FILES,
            instance=producto
        )

        if formulario.is_valid():
            formulario.save()
            return redirect("lista_productos")

    else:
        formulario = ProductoForm(instance=producto)

    return render(request, "productos/editar_producto.html", {
        "formulario": formulario,
        "producto": producto
    })
    
@login_required
def eliminar_producto(request, id):
    if request.user.rol != Roles.CAMPESINO:
        return HttpResponseForbidden()

    # La eliminación es lógica: conserva el registro y lo oculta del catálogo.
    producto = get_object_or_404(Producto, id=id, usuario=request.user)

    if request.method == "POST":
        producto.activo = False
        producto.save()
        return redirect("lista_productos")

    return render(request, "productos/eliminar_producto.html", {
        "producto": producto
    })
    
class ProductoViewSet(viewsets.ModelViewSet):
    # Solo expone productos activos en la API.
    queryset = Producto.objects.filter(activo=True)

    # Define el serializer encargado de convertir productos a JSON
    # y validar los datos recibidos.
    serializer_class = ProductoSerializer

    # Aplica las reglas de acceso según el rol y propietario.
    permission_classes = [PermisoProductos]

    def get_serializer_class(self):
        if self.action in ("administracion", "activar", "desactivar"):
            return AdministrarProductoSerializer
        return ProductoSerializer

    def get_queryset(self):
        # Las rutas administrativas también deben localizar productos inactivos.

        if self.action in ("administracion", "activar", "desactivar"):
            return Producto.objects.all()
        return Producto.objects.filter(activo=True)

    @action(detail=False, methods=["get"])
    def administracion(self, request):
        """Lista productos activos e inactivos solo para ADMIN."""
        productos = self.filter_queryset(self.get_queryset())
        return Response(self.get_serializer(productos, many=True).data)

    @action(detail=True, methods=["post"])
    def activar(self, request, pk=None):
        """Reactiva una publicación sin cambiar contenido ni propietario."""
        producto = self.get_object()
        if not producto.activo:
            producto.activo = True
            producto.save(update_fields=["activo"])
        return Response(self.get_serializer(producto).data)

    @action(detail=True, methods=["post"])
    def desactivar(self, request, pk=None):
        """Desactiva una publicación sin cambiar contenido ni propietario."""
        producto = self.get_object()
        if producto.activo:
            producto.activo = False
            producto.save(update_fields=["activo"])
        return Response(self.get_serializer(producto).data)

    def perform_create(self, serializer):
        # Asigna automáticamente el campesino autenticado como propietario.
        # El cliente no puede elegir quién publica el producto.
        serializer.save(usuario=self.request.user)

    def destroy(self, request, *args, **kwargs):
        # Obtiene el producto y verifica los permisos correspondientes.
        producto = self.get_object()

        # Eliminación lógica: conserva el registro, pero lo desactiva.
        producto.activo = False
        producto.save()

        # Confirma la eliminación sin devolver contenido.
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoriaViewSet(viewsets.ReadOnlyModelViewSet):
    """Expone las categorías existentes sin permitir modificarlas por la API."""

    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAuthenticated]
