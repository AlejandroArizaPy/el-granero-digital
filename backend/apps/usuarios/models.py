from django.db import models
from django.contrib.auth.models import AbstractUser

# Datos para la db
ROLES = [
    ("admin","Administrador"),
    ("campesino","Campesino"),
    ("comprador","Comprador"),
]

# Create your models here.
class Usuario(AbstractUser):
    documento = models.CharField(max_length=20, unique=True)
    celular = models.CharField(max_length=20, unique=True)
    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        default="comprador"
    )
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_rol_display()})"

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"