from django.contrib import admin
from .models import Usuario


# Permite gestionar los usuarios desde el panel administrativo de Django.
admin.site.register(Usuario)