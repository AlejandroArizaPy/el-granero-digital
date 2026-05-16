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
    documento = models.CharField(max_length=20)
    celular = models.CharField(max_length=20)
    rol = models.CharField(
        max_length=20,
        choices=ROLES
    )