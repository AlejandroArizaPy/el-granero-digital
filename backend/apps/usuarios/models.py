from django.db import models
from django.contrib.auth.models import AbstractUser

# Datos para la db
# Centraliza los roles válidos del sistema para evitar valores inconsistentes en diferentes módulos.
class Roles(models.TextChoices):
    ADMIN = "admin", "Administrador"
    CAMPESINO = "campesino", "Campesino"
    COMPRADOR = "comprador", "Comprador"

# Create your models here.
# Extiende el modelo de usuario de Django con los datos y roles específicos del proyecto.
class Usuario(AbstractUser):
    documento = models.CharField(max_length=20, unique=True)
    celular = models.CharField(max_length=20, unique=True)
    rol = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.COMPRADOR
    )
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_rol_display()})"

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"