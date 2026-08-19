from django.db import models
from apps.usuarios.models import Usuario
from django.core.exceptions import ValidationError

class TipoCategoria(models.TextChoices):
    PERECEDEROS_GRANOS_Y_CEREALES = "PGC", "Perecederos, granos y cereales"
    FRUTAS_Y_VERDURAS = "FYV", "Frutas y verduras"
    LACTEOS_Y_DERIVADOS = "LYD", "Lácteos y derivados"
    HUEVOS_Y_PROTEINAS = "HYP", "Huevos y proteínas"
    DERIVADOS_Y_PANADERIA = "DYP", "Derivados y panadería"
    DESPENSAS_Y_CONSERVAS = "DYC", "Despensas y conservas"
    BEBIDAS_Y_AROMATICAS = "BYA", "Bebidas y aromáticas"
    SEMILLAS = "SMS", "Semillas"


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


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    detalle = models.TextField()
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)
    peso = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        help_text="Peso en kilogramos"
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
    
    def clean(self):
        if self.usuario.rol != "campesino":
            raise ValidationError(
                "Solo los usuarios con rol campesino pueden publicar productos."
                )
        
    def save(self):
        self.full_clean()
        super().save()

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["nombre"]
        
        




