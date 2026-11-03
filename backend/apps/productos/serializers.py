from rest_framework import serializers
from apps.productos.models import Producto
from apps.usuarios.models import Usuario


class CampesinoProductoSerializer(serializers.ModelSerializer):
    """Expone el nombre y apellido del campesino propietario."""

    class Meta:
        model = Usuario
        fields = ["first_name", "last_name"]


class ProductoSerializer(serializers.ModelSerializer):
    """
    Define la representación y validación de los productos
    intercambiados mediante la API.
    """

    # Información pública del propietario; no puede modificarse desde la API.
    usuario = CampesinoProductoSerializer(read_only=True)

    class Meta:
        model = Producto
        fields = [
            "id",
            "nombre",
            "detalle",
            "precio",
            "stock",
            "peso",
            "imagen",
            "categoria",
            "usuario",
        ]