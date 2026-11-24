from django.db import models
from apps.usuarios.models import Usuario
from apps.productos.models import Producto
from django.core.validators import MinValueValidator
from decimal import Decimal


class EstadoPedido(models.TextChoices):
    # El código se guarda en la base; la etiqueta se muestra a las personas.
    PENDIENTE = "PDT", "Pendiente"
    EN_PREPARACION = "ENP", "En preparación"
    COMPLETADO = "CPO", "Completado"
    CANCELADO = "CLO", "Cancelado"
    

class MetodoPago(models.TextChoices):
    EFECTIVO = "EFO", "Efectivo contraentrega"
    TRANSFERENCIA = "TRF", "Transferencia bancaria"
 
    

class Pedido(models.Model):
    # En el flujo de pedidos, el comprador compra a un único campesino vendedor.
    comprador = models.ForeignKey(Usuario,
                                on_delete=models.PROTECT,
                                related_name="pedidos_realizados")
    vendedor = models.ForeignKey(Usuario,
                                on_delete=models.PROTECT,
                                related_name="pedidos_recibidos") 
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=3,
        choices = EstadoPedido.choices,
        default=EstadoPedido.PENDIENTE
    )
    direccion_entrega = models.CharField(max_length=120)
    # Se conserva el total del pedido para consultar el valor confirmado.
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    
    def recalcular_total(self):
        # El total se suma desde los detalles y sus precios históricos.
        sum_subtotales = Decimal("0.00")
        for detalle in self.detalles.all():
            sum_subtotales += (detalle.cantidad * detalle.precio_unitario)
        
        self.total = sum_subtotales
        self.save(update_fields=["total"])
        
    ciudad = models.CharField(max_length=100)
    metodo_pago = models.CharField(
        max_length=3,
        choices = MetodoPago.choices
    )
    
class DetallePedido(models.Model):
    # El detalle conserva cantidad y precio al momento de crear el pedido.
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE,related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=10,
                                          decimal_places=2,
                                          validators=[MinValueValidator(0.01)]
                                          )
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['pedido', 'producto'], 
                name='unique_producto_por_pedido'
            )
        ]