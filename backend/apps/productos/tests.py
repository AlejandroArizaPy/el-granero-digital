from io import BytesIO
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from apps.productos.models import Categoria, Producto, TipoCategoria
from apps.usuarios.models import Roles


Usuario = get_user_model()


class VistasWebProductosPermisosTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.media_settings = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.media_settings.enable()

        self.categoria = Categoria.objects.create(nombre=TipoCategoria.FRUTAS_Y_VERDURAS)
        self.campesino = self.crear_usuario("campesino", Roles.CAMPESINO)
        self.otro_campesino = self.crear_usuario("otro_campesino", Roles.CAMPESINO)
        self.comprador = self.crear_usuario("comprador", Roles.COMPRADOR)
        self.producto = self.crear_producto(self.campesino, "Producto original")

        self.url_crear = reverse("crear_producto")
        self.url_editar = reverse("editar_producto", args=[self.producto.pk])
        self.url_eliminar = reverse("eliminar_producto", args=[self.producto.pk])

    def tearDown(self):
        self.media_settings.disable()
        self.media_dir.cleanup()
        super().tearDown()

    def crear_usuario(self, username, rol):
        return Usuario.objects.create_user(
            username=username,
            password="ClaveSegura-2026!",
            documento=f"doc-{username}",
            celular=f"cel-{username}",
            rol=rol,
        )

    def archivo_imagen(self):
        buffer = BytesIO()
        Image.new("RGB", (1, 1), color="green").save(buffer, format="PNG")
        return SimpleUploadedFile(
            "producto.png", buffer.getvalue(), content_type="image/png"
        )

    def crear_producto(self, usuario, nombre):
        return Producto.objects.create(
            nombre=nombre,
            detalle="Producto de prueba",
            precio="2500.00",
            stock=10,
            peso="1.000",
            imagen=self.archivo_imagen(),
            categoria=self.categoria,
            usuario=usuario,
        )

    def datos_producto(self, nombre="Producto actualizado"):
        return {
            "nombre": nombre,
            "detalle": "Detalle actualizado",
            "precio": "3000.00",
            "stock": "8",
            "peso": "1.200",
            "categoria": str(self.categoria.pk),
        }

    def test_usuario_anonimo_no_puede_crear_editar_ni_eliminar(self):
        respuestas = [
            self.client.get(self.url_crear),
            self.client.post(
                self.url_crear,
                self.datos_producto() | {"imagen": self.archivo_imagen()},
            ),
            self.client.get(self.url_editar),
            self.client.post(self.url_editar, self.datos_producto()),
            self.client.get(self.url_eliminar),
            self.client.post(self.url_eliminar),
        ]

        self.assertTrue(all(respuesta.status_code == 302 for respuesta in respuestas))
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.nombre, "Producto original")
        self.assertTrue(self.producto.activo)
        self.assertEqual(Producto.objects.count(), 1)

    def test_comprador_no_puede_crear_editar_ni_eliminar(self):
        self.client.force_login(self.comprador)
        respuestas = [
            self.client.get(self.url_crear),
            self.client.post(
                self.url_crear,
                self.datos_producto() | {"imagen": self.archivo_imagen()},
            ),
            self.client.get(self.url_editar),
            self.client.post(self.url_editar, self.datos_producto()),
            self.client.get(self.url_eliminar),
            self.client.post(self.url_eliminar),
        ]

        self.assertTrue(all(respuesta.status_code == 403 for respuesta in respuestas))
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.nombre, "Producto original")
        self.assertTrue(self.producto.activo)
        self.assertEqual(Producto.objects.count(), 1)

    def test_campesino_puede_crear_producto(self):
        self.client.force_login(self.campesino)

        respuesta = self.client.post(
            self.url_crear,
            self.datos_producto("Producto nuevo") | {"imagen": self.archivo_imagen()},
        )

        self.assertRedirects(respuesta, reverse("lista_productos"))
        producto = Producto.objects.get(nombre="Producto nuevo")
        self.assertEqual(producto.usuario, self.campesino)

    def test_campesino_propietario_puede_editar_producto(self):
        self.client.force_login(self.campesino)

        respuesta = self.client.post(self.url_editar, self.datos_producto())

        self.assertRedirects(respuesta, reverse("lista_productos"))
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.nombre, "Producto actualizado")
        self.assertEqual(self.producto.usuario, self.campesino)

    def test_campesino_propietario_puede_desactivar_producto(self):
        self.client.force_login(self.campesino)

        respuesta = self.client.post(self.url_eliminar)

        self.assertRedirects(respuesta, reverse("lista_productos"))
        self.producto.refresh_from_db()
        self.assertFalse(self.producto.activo)

    def test_campesino_no_propietario_no_puede_editar_ni_eliminar(self):
        self.client.force_login(self.otro_campesino)

        respuesta_editar_get = self.client.get(self.url_editar)
        respuesta_editar = self.client.post(self.url_editar, self.datos_producto())
        respuesta_eliminar_get = self.client.get(self.url_eliminar)
        respuesta_eliminar = self.client.post(self.url_eliminar)

        self.assertEqual(respuesta_editar_get.status_code, 404)
        self.assertEqual(respuesta_editar.status_code, 404)
        self.assertEqual(respuesta_eliminar_get.status_code, 404)
        self.assertEqual(respuesta_eliminar.status_code, 404)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.nombre, "Producto original")
        self.assertTrue(self.producto.activo)

