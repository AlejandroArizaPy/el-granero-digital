from django.db import models
from apps.usuarios.models import Usuario, Roles
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator


# Centraliza las categorías disponibles para clasificar los productos
# y evita utilizar valores diferentes para una misma categoría.
class TipoCategoria(models.TextChoices):
    PERECEDEROS_GRANOS_Y_CEREALES = "PGC", "Perecederos, granos y cereales"
    FRUTAS_Y_VERDURAS = "FYV", "Frutas y verduras"
    LACTEOS_Y_DERIVADOS = "LYD", "Lácteos y derivados"
    HUEVOS_Y_PROTEINAS = "HYP", "Huevos y proteínas"
    DERIVADOS_Y_PANADERIA = "DYP", "Derivados y panadería"
    DESPENSAS_Y_CONSERVAS = "DYC", "Despensas y conservas"
    BEBIDAS_Y_AROMATICAS = "BYA", "Bebidas y aromáticas"
    SEMILLAS = "SMS", "Semillas"


# Representa las categorías utilizadas para organizar los productos publicados.
class Categoria(models.Model):
    nombre = models.CharField(
        max_length=3,
        choices=TipoCategoria.choices,
        unique=True
    )

    def __str__(self):
        return self.get_nombre_display()

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["nombre"]


# Representa los productos publicados por los campesinos dentro de la plataforma.
class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    detalle = models.TextField()
    precio = models.DecimalField(
    max_digits=8,
    decimal_places=2,
    validators=[MinValueValidator(0.01)]
    )
    stock = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)
    peso = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        help_text="Peso en kilogramos",
        validators=[MinValueValidator(0.01)]
    )
    imagen = models.ImageField(
        upload_to="productos/img/",
        blank=False,
        null=False
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos"
    )
    
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="productos_publicados"
    )
    
    # Valida una regla de negocio fundamental: únicamente los usuarios
    # con rol campesino pueden publicar productos.
    def clean(self):
        if self.usuario_id is not None:
            if self.usuario.rol != Roles.CAMPESINO:
                raise ValidationError(
                    "Solo los usuarios con rol campesino pueden publicar productos."
                )
    
    
    # Ejecuta las validaciones del modelo antes de guardar el producto,
    # garantizando que las reglas de negocio también se apliquen fuera de la API.    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["nombre"]
        