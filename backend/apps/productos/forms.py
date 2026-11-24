from django import forms
from .models import Producto


class ProductoForm(forms.ModelForm):
    # El formulario reutiliza los campos y validaciones declarados en Producto.
    class Meta:
        model = Producto
        fields = [
            "nombre",
            "detalle",
            "precio",
            "stock",
            "peso",
            "imagen",
            "categoria",
        ]
