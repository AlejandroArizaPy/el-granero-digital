from django.db import models


# Create your models here.

class TipoCategoria(models.TextChoices):
    PERECEDEROS_GRANOS_Y_CEREALES = "PGC", "Perecederos, granos y cereales"
    FRUTAS_Y_VERDURAS = "FYV", "Frutas y verduras"
    LACTEOS_Y_DERIVADOS = "LYD", "Lácteos y derivados"
    HUEVOS_Y_PROTEINAS = "HYP", "Huevos y proteínas"
    DERIVADOS_Y_PANADERIA = "DYP", "Derivados y panadería"
    DESPENSAS_Y_CONSERVAS = "DYC", "Despensas y conservas"
    BEBIDAS_Y_AROMATICAS = "BYA", "Bebidas y aromáticas"
    SEMILLAS = "SMS", "Semillas"
    

class Producto(models.Model):
    nombre_producto = models.CharField(max_length=100)
    detalle_producto = models.TextField()
    valor = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField()
    peso = models.DecimalField(max_digits=8, decimal_places=3)
    imagen = models.ImageField(upload_to='productos/img/', blank=False, null=False)
    categoria = models.CharField(
        max_length = 3,
        choices = TipoCategoria.choices
    )
    
    

    


    