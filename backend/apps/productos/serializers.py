from rest_framework import serializers
from apps.productos.models import Categoria, Producto
from apps.usuarios.models import Usuario


class CampesinoProductoSerializer(serializers.ModelSerializer):
    """Expone el nombre y apellido del campesino propietario."""

    class Meta:
        model = Usuario
        fields = ["id", "first_name", "last_name"]


class CategoriaSerializer(serializers.ModelSerializer):
    # Devuelve el texto legible de la opción guardada en `nombre`.
    nombre_display = serializers.CharField(source="get_nombre_display", read_only=True)

    class Meta:
        model = Categoria
        fields = ["id", "nombre", "nombre_display"]


class ProductoSerializer(serializers.ModelSerializer):
    """
    Define la representación y validación de los productos
    intercambiados mediante la API.
    """

    # Información pública del propietario; no puede modificarse desde la API.
    usuario = CampesinoProductoSerializer(read_only=True)
    categoria_nombre = serializers.CharField(
        source="categoria.get_nombre_display",
        read_only=True,
    )

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
            "categoria_nombre",
            "usuario",
        ]


class AdministrarProductoSerializer(ProductoSerializer):
    """Añade el estado de publicación a las respuestas administrativas."""

    class Meta(ProductoSerializer.Meta):
        fields = ProductoSerializer.Meta.fields + ["activo"]
