from django.shortcuts import render, redirect
from .forms import ProductoForm
from rest_framework import viewsets
from .serializers import ProductoSerializer
from apps.productos.models import Producto


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
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer