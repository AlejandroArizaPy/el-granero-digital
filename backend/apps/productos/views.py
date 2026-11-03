from django.shortcuts import render, redirect
from .forms import ProductoForm
from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from .serializers import ProductoSerializer
from apps.productos.models import Producto
from apps.productos.permissions import PermisoProductos


def crear_producto(request):
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
    productos = Producto.objects.filter(activo=True)

    return render(request, "productos/lista_productos.html", {
        "productos": productos
    })

def editar_producto(request, id):
    producto = Producto.objects.get(id=id)

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
    
def eliminar_producto(request, id):
    producto = Producto.objects.get(id=id)

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