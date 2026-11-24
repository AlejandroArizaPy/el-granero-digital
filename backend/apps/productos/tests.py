from io import BytesIO
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image
from rest_framework.test import APIClient

from apps.ordenes.models import DetallePedido, Pedido
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
        self.admin = self.crear_usuario("admin", Roles.ADMIN)
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

    def test_api_catalogo_incluye_id_del_campesino_propietario(self):
        api_client = APIClient()
        api_client.force_authenticate(self.campesino)

        respuesta = api_client.get(reverse("producto-list"))

        self.assertEqual(respuesta.status_code, 200)
        producto = next(
            producto for producto in respuesta.data
            if producto["id"] == self.producto.pk
        )
        self.assertEqual(producto["usuario"]["id"], self.campesino.pk)
        self.assertEqual(
            producto["categoria_nombre"],
            self.categoria.get_nombre_display(),
        )

    def test_api_campesino_crea_producto_y_aparece_en_catalogo(self):
        api_client = APIClient()
        api_client.force_authenticate(self.campesino)

        respuesta = api_client.post(
            reverse("producto-list"),
            {
                "nombre": "Producto publicado por API",
                "detalle": "Descripción del producto",
                "precio": "4200.00",
                "stock": 12,
                "peso": "1.250",
                "categoria": self.categoria.pk,
                "imagen": self.archivo_imagen(),
            },
            format="multipart",
        )

        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        producto_id = respuesta.data["id"]
        producto = Producto.objects.get(pk=producto_id)
        self.assertEqual(producto.usuario, self.campesino)
        self.assertTrue(producto.activo)

        catalogo = api_client.get(reverse("producto-list"))
        self.assertEqual(catalogo.status_code, 200)
        self.assertTrue(any(item["id"] == producto_id for item in catalogo.data))

    def test_comprador_no_puede_publicar_producto_por_api(self):
        api_client = APIClient()
        api_client.force_authenticate(self.comprador)

        respuesta = api_client.post(
            reverse("producto-list"),
            {
                "nombre": "Producto no autorizado",
                "detalle": "Descripción",
                "precio": "100.00",
                "stock": 1,
                "peso": "1.000",
                "categoria": self.categoria.pk,
                "imagen": self.archivo_imagen(),
            },
            format="multipart",
        )

        self.assertEqual(respuesta.status_code, 403)
        self.assertFalse(Producto.objects.filter(nombre="Producto no autorizado").exists())

    def test_categorias_api_es_solo_lectura_y_requiere_autenticacion(self):
        url = reverse("categoria-list")
        respuesta_anonima = APIClient().get(url)
        self.assertEqual(respuesta_anonima.status_code, 401)

        api_client = APIClient()
        api_client.force_authenticate(self.campesino)
        respuesta = api_client.get(url)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data, [{
            "id": self.categoria.pk,
            "nombre": self.categoria.nombre,
            "nombre_display": self.categoria.get_nombre_display(),
        }])
        respuesta_post = api_client.post(url, {"nombre": "PGC"})
        self.assertEqual(respuesta_post.status_code, 405)

    def test_admin_lista_productos_activos_e_inactivos_sin_cambiar_su_contenido(self):
        inactivo = self.crear_producto(self.otro_campesino, "Producto inactivo")
        Producto.objects.filter(pk=inactivo.pk).update(activo=False)
        api_client = self.api_as(self.admin)

        respuesta = api_client.get(reverse("producto-administracion"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual({item["id"] for item in respuesta.data}, {self.producto.pk, inactivo.pk})
        self.assertFalse(next(item for item in respuesta.data if item["id"] == inactivo.pk)["activo"])

    def test_comprador_y_campesino_no_acceden_a_consulta_administrativa(self):
        for usuario in (self.comprador, self.campesino):
            with self.subTest(rol=usuario.rol):
                api_client = self.api_as(usuario)
                respuesta = api_client.get(reverse("producto-administracion"))
                self.assertEqual(respuesta.status_code, 403)

    def test_admin_puede_activar_y_desactivar_sin_editar_el_producto(self):
        api_client = self.api_as(self.admin)
        campos_originales = (
            self.producto.nombre,
            self.producto.detalle,
            self.producto.usuario_id,
            self.producto.precio,
            self.producto.stock,
            self.producto.imagen.name,
        )

        respuesta_desactivar = api_client.post(
            reverse("producto-desactivar", args=[self.producto.pk])
        )
        respuesta_repetida = api_client.post(
            reverse("producto-desactivar", args=[self.producto.pk])
        )
        self.producto.refresh_from_db()
        self.assertEqual(respuesta_desactivar.status_code, 200)
        self.assertFalse(respuesta_desactivar.data["activo"])
        self.assertEqual(respuesta_repetida.status_code, 200)
        self.assertEqual(
            (
                self.producto.nombre,
                self.producto.detalle,
                self.producto.usuario_id,
                self.producto.precio,
                self.producto.stock,
                self.producto.imagen.name,
            ),
            campos_originales,
        )

        respuesta_activar = api_client.post(
            reverse("producto-activar", args=[self.producto.pk])
        )
        self.producto.refresh_from_db()
        self.assertEqual(respuesta_activar.status_code, 200)
        self.assertTrue(self.producto.activo)
        self.assertEqual(
            (
                self.producto.nombre,
                self.producto.detalle,
                self.producto.usuario_id,
                self.producto.precio,
                self.producto.stock,
                self.producto.imagen.name,
            ),
            campos_originales,
        )

    def test_admin_no_puede_cambiar_contenido_o_propietario_del_producto(self):
        api_client = self.api_as(self.admin)

        respuesta = api_client.patch(
            reverse("producto-detail", args=[self.producto.pk]),
            {"nombre": "Alterado", "usuario": self.otro_campesino.pk},
            format="json",
        )
        respuesta_delete = api_client.delete(
            reverse("producto-detail", args=[self.producto.pk])
        )

        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(respuesta_delete.status_code, 403)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.nombre, "Producto original")
        self.assertEqual(self.producto.usuario, self.campesino)

    def test_comprador_y_campesino_no_pueden_cambiar_estado_administrativo(self):
        Producto.objects.filter(pk=self.producto.pk).update(activo=False)
        for usuario in (self.comprador, self.campesino):
            with self.subTest(rol=usuario.rol):
                api_client = self.api_as(usuario)
                respuesta_desactivar = api_client.post(
                    reverse("producto-desactivar", args=[self.producto.pk])
                )
                respuesta_activar = api_client.post(
                    reverse("producto-activar", args=[self.producto.pk])
                )
                self.assertEqual(respuesta_desactivar.status_code, 403)
                self.assertEqual(respuesta_activar.status_code, 403)

        self.producto.refresh_from_db()
        self.assertFalse(self.producto.activo)

    def api_as(self, usuario):
        client = APIClient()
        client.force_authenticate(usuario)
        return client

