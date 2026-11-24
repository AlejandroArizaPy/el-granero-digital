from io import StringIO
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from apps.productos.management.commands.cargar_productos_demo import PRODUCTOS_DEMO
from apps.productos.models import Categoria, Producto, TipoCategoria
from apps.usuarios.models import Roles


Usuario = get_user_model()


class CargarProductosDemoCommandTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.media_settings = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.media_settings.enable()
        self.addCleanup(self.media_dir.cleanup)
        self.addCleanup(self.media_settings.disable)

        self.categoria_fyv = Categoria.objects.create(
            nombre=TipoCategoria.FRUTAS_Y_VERDURAS
        )
        self.categoria_lyd = Categoria.objects.create(
            nombre=TipoCategoria.LACTEOS_Y_DERIVADOS
        )
        self.campesino = Usuario.objects.create_user(
            username="campesino_demo",
            password="no-se-usa-en-el-comando",
            documento="doc-campesino-demo",
            celular="cel-campesino-demo",
            rol=Roles.CAMPESINO,
        )

    def test_simulacion_muestra_categorias_y_productos_sin_escribir(self):
        output = StringIO()
        call_command(
            "cargar_productos_demo",
            username=self.campesino.username,
            stdout=output,
        )

        for code, _label in TipoCategoria.choices:
            self.assertIn(code, output.getvalue())
        self.assertIn("por crear", output.getvalue())
        self.assertEqual(Categoria.objects.count(), 2)
        self.assertEqual(Producto.objects.count(), 0)
        self.assertEqual(list(Path(self.media_dir.name).rglob("*")), [])

    def test_apply_crea_categorias_actualiza_demos_y_es_idempotente(self):
        tomate = Producto.objects.create(
            nombre="Tomate chonto de temporada",
            detalle="Detalle anterior",
            precio="1999.00",
            stock=7,
            peso="1.000",
            imagen=self._imagen_temporal("tomate.png"),
            categoria=self.categoria_fyv,
            usuario=self.campesino,
        )
        papa = Producto.objects.create(
            nombre="Papa criolla seleccionada",
            detalle="Papa ya publicada",
            precio="3800.00",
            stock=9,
            peso="1.000",
            imagen=self._imagen_temporal("papa.png"),
            categoria=self.categoria_fyv,
            usuario=self.campesino,
        )
        tomate_id, papa_id = tomate.pk, papa.pk
        fyv_id, lyd_id = self.categoria_fyv.pk, self.categoria_lyd.pk
        ajeno = Producto.objects.create(
            nombre="Producto ajeno a la carga",
            detalle="Debe permanecer igual",
            precio="2000.00",
            stock=5,
            peso="1.000",
            imagen=self._imagen_temporal("ajeno.png"),
            categoria=self.categoria_fyv,
            usuario=self.campesino,
        )

        call_command(
            "cargar_productos_demo",
            username=self.campesino.username,
            apply=True,
        )

        tomate.refresh_from_db()
        papa.refresh_from_db()
        ajeno.refresh_from_db()
        self.assertEqual(tomate.pk, tomate_id)
        self.assertEqual(papa.pk, papa_id)
        self.assertEqual(tomate.stock, 7)
        self.assertEqual(papa.stock, 9)
        self.assertEqual(papa.nombre, next(
            demo.nombre for demo in PRODUCTOS_DEMO
            if demo.categoria == TipoCategoria.PERECEDEROS_GRANOS_Y_CEREALES
        ))
        self.assertEqual(ajeno.nombre, "Producto ajeno a la carga")
        self.assertEqual(ajeno.stock, 5)

        categories = {category.nombre: category for category in Categoria.objects.all()}
        self.assertEqual(set(categories), set(TipoCategoria.values))
        self.assertEqual(categories[TipoCategoria.FRUTAS_Y_VERDURAS].pk, fyv_id)
        self.assertEqual(categories[TipoCategoria.LACTEOS_Y_DERIVADOS].pk, lyd_id)

        demo_names = {demo.nombre for demo in PRODUCTOS_DEMO}
        demo_products = Producto.objects.filter(
            usuario=self.campesino,
            nombre__in=demo_names,
        )
        self.assertEqual(demo_products.count(), 8)
        expected_categories = {
            demo.categoria: categories[demo.categoria].pk
            for demo in PRODUCTOS_DEMO
        }
        self.assertEqual(
            dict(demo_products.values_list("categoria__nombre", "categoria_id")),
            expected_categories,
        )

        call_command(
            "cargar_productos_demo",
            username=self.campesino.username,
            apply=True,
        )
        self.assertEqual(Categoria.objects.count(), 8)
        self.assertEqual(demo_products.count(), 8)
        papa.refresh_from_db()
        self.assertEqual(papa.pk, papa_id)
        self.assertEqual(papa.stock, 9)

    def test_usuario_que_no_es_campesino_no_crea_categorias(self):
        comprador = Usuario.objects.create_user(
            username="comprador_demo",
            password="no-se-usa-en-el-comando",
            documento="doc-comprador-demo",
            celular="cel-comprador-demo",
            rol=Roles.COMPRADOR,
        )

        with self.assertRaises(CommandError):
            call_command("cargar_productos_demo", username=comprador.username)

        self.assertEqual(Categoria.objects.count(), 2)
        self.assertEqual(Producto.objects.count(), 0)

    def _imagen_temporal(self, name):
        from io import BytesIO

        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image

        buffer = BytesIO()
        Image.new("RGB", (1, 1), color="red").save(buffer, format="PNG")
        return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")
