from django.db import models
from apps.usuarios.models import Usuario
from apps.productos.models import Producto

# Create your models here.
class EstadoPedido(models.TextChoices):
    PENDIENTE = "PDT", "Pendiente"
    EN_PREPARACION = "ENP", "En preparación"
    COMPLETADO = "CPO", "Completado"
    CANCELADO = "CLO", "Cancelado"
    
    
class Ciudad(models.TextChoices):
    BOGOTA = "BGT", "Bogotá"
    CALI = "CAL", "Cali"
    MEDELLIN = "MDN", "Medellín"
    BARRANQUILLA = "BQA", "Barranquilla"
    MANIZALES = "MNS" , "Manizales"
    

class MetodoPago(models.TextChoices):
    EFECTIVO = "EFO", "Efectivo"
    TRANSFERENCIA = "TRF", "Transferencia"
    PSE = "PSE", "PSE (Pagos en línea)"
    BILLETERAS_DIGITALES = "BDS", "Billeteras dígitales"    
    

class Pedido(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=3,
        choices = EstadoPedido.choices
    )
    direccion_entrega = models.CharField(max_length=120)
    total = models.DecimalField(max_digits=8, decimal_places=2)
    ciudad = models.CharField(
        max_length=3,
        choices = Ciudad.choices
    )
    metodo_pago = models.CharField(
        max_length=3,
        choices = MetodoPago.choices
    )
    
class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)