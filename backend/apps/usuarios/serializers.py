from rest_framework import serializers
from .models import Usuario, Roles


# Define los datos que pueden ser consultados de un usuario en las operaciones generales.
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id','rol','first_name','last_name','celular', 'email']


# Controla el registro de nuevos usuarios y transforma el tipo de registro
# recibido en el rol que será almacenado en el modelo Usuario.
class RegistroUsuarioSerializer(serializers.ModelSerializer):
    
    # Se utiliza únicamente durante el registro para indicar si la persona
    # desea registrarse como campesino o comprador.
    tipo_registro = serializers.CharField(write_only=True)
    
    class Meta:
        model = Usuario
        fields = ['password','username','first_name','last_name',
                  'email','documento','celular','tipo_registro']
        
    def create(self, validated_data):
        password = validated_data.pop('password')
        tipo_registro = validated_data.pop('tipo_registro')
        
        # Convierte el tipo de registro recibido en uno de los roles válidos del sistema.
        if tipo_registro == Roles.CAMPESINO:
            rol = Roles.CAMPESINO
        elif tipo_registro == Roles.COMPRADOR:
            rol = Roles.COMPRADOR
        
        # Se utiliza create_user() para que la contraseña sea almacenada
        # mediante el mecanismo de hash proporcionado por Django.
        usuario = Usuario.objects.create_user(
            password = password,
            rol = rol,
            **validated_data
        ) 
        return usuario
    
    
    # Restringe el registro público a los roles que pueden crear cuentas
    # desde este flujo, evitando que un usuario se registre como administrador.
    def validate_tipo_registro(self, tipo_registro):
        if tipo_registro != Roles.CAMPESINO and tipo_registro != Roles.COMPRADOR:
            raise serializers.ValidationError("Rol no válido.")
        
        return tipo_registro


# Limita la información mostrada en el listado general de usuarios,
# evitando exponer datos personales innecesarios como documento y celular.
class ConsultarUsuariosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["id", "rol", "first_name", "last_name"]


# Define la información completa que puede consultarse al visualizar
# el detalle de un usuario autorizado.        
class DetalleUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["id", "rol", "first_name", "last_name",
                  "documento", "celular", "email"]


# Controla los campos que un usuario puede modificar sobre su propia información,
# evitando que pueda modificar directamente su rol.        
class ActualizarUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["first_name", "last_name", "documento", "celular", "email"]


# Permite al administrador modificar los datos del usuario incluyendo su rol,
# manteniendo esta capacidad separada de la actualización realizada por usuarios normales.
class ActualizarUsuarioAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["rol", "first_name", "last_name", "documento", "celular", "email"]