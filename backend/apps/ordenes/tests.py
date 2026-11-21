from decimal import Decimal
from io import BytesIO
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from apps.ordenes.models import DetallePedido, EstadoPedido, Pedido
from apps.productos.models import Categoria, Producto, TipoCategoria
from apps.usuarios.models import Roles


Usuario = get_user_model()


class PedidoAPITests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.media_settings = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.media_settings.enable()

        self.client = APIClient()
        self.categoria = Categoria.objects.create(nombre=TipoCategoria.FRUTAS_Y_VERDURAS)
        self.comprador = self.crear_usuario("comprador", Roles.COMPRADOR)
        self.otro_comprador = self.crear_usuario("otro_comprador", Roles.COMPRADOR)
        self.vendedor = self.crear_usuario("vendedor", Roles.CAMPESINO)
        self.otro_vendedor = self.crear_usuario("otro_vendedor", Roles.CAMPESINO)

        self.producto_a = self.crear_producto(
            self.vendedor, "Tomate", "2.50", stock=10
        )
        self.producto_b = self.crear_producto(
            self.vendedor, "Papa", "3.25", stock=5
        )
        self.producto_otro_vendedor = self.crear_producto(
            self.otro_vendedor, "Yuca", "4.00", stock=8
        )
        self.producto_inactivo = self.crear_producto(
            self.vendedor, "Cebolla", "1.50", stock=7
        )
        Producto.objects.filter(pk=self.producto_inactivo.pk).update(activo=False)

        self.url_lista = reverse("pedido-list")

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

    def imagen(self):
        buffer = BytesIO()
        Image.new("RGB", (1, 1), color="green").save(buffer, format="PNG")
        return SimpleUploadedFile(
            "producto.png", buffer.getvalue(), content_type="image/png"
        )

    def crear_producto(self, vendedor, nombre, precio, stock):
        return Producto.objects.create(
            nombre=nombre,
            detalle="Producto para pruebas",
            precio=precio,
            stock=stock,
            peso="1.000",
            imagen=self.imagen(),
            categoria=self.categoria,
            usuario=vendedor,
        )

    def datos_pedido(self, detalles=None):
        return {
            "direccion_entrega": "Finca La Esperanza",
            "ciudad": "Bogotá",
            "metodo_pago": "EFO",
            "detalles": detalles
            if detalles is not None
            else [
                {"producto": self.producto_a.pk, "cantidad": 2},
                {"producto": self.producto_b.pk, "cantidad": 1},
            ],
        }

    def crear_pedido(self, detalles=None, comprador=None):
        comprador = comprador or self.comprador
        self.client.force_authenticate(comprador)
        respuesta = self.client.post(
            self.url_lista,
            self.datos_pedido(detalles),
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED, respuesta.data)
        return respuesta.data["id"], respuesta.data

    def url_accion(self, accion, pedido_id):
        return reverse(f"pedido-{accion}", args=[pedido_id])

    def test_creacion_guarda_precios_historicos_total_y_no_descuenta_stock(self):
        self.client.force_authenticate(self.comprador)

        respuesta = self.client.post(self.url_lista, self.datos_pedido(), format="json")

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED, respuesta.data)
        pedido = Pedido.objects.get(pk=respuesta.data["id"])
        detalles = list(pedido.detalles.order_by("producto_id"))
        self.assertEqual(pedido.comprador, self.comprador)
        self.assertEqual(pedido.vendedor, self.vendedor)
        self.assertEqual(pedido.estado, EstadoPedido.PENDIENTE)
        self.assertEqual([detalle.precio_unitario for detalle in detalles], [
            Decimal("2.50"), Decimal("3.25")
        ])
        self.assertEqual(pedido.total, Decimal("8.25"))
        self.assertEqual(respuesta.data["detalles"][0]["subtotal"], Decimal("5.00"))
        self.assertEqual(respuesta.data["detalles"][1]["subtotal"], Decimal("3.25"))
        self.assertEqual(respuesta.data["total"], "8.25")
        self.producto_a.refresh_from_db()
        self.producto_b.refresh_from_db()
        self.assertEqual(self.producto_a.stock, 10)
        self.assertEqual(self.producto_b.stock, 5)

        self.producto_a.precio = Decimal("9.99")
        self.producto_a.save()
        detalle_historico = pedido.detalles.get(producto=self.producto_a)
        self.assertEqual(detalle_historico.precio_unitario, Decimal("2.50"))
        self.assertEqual(pedido.total, Decimal("8.25"))

    def test_solo_compradores_pueden_crear_pedidos(self):
        self.client.force_authenticate(self.vendedor)

        respuesta = self.client.post(self.url_lista, self.datos_pedido(), format="json")

        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Pedido.objects.count(), 0)

    def test_comprador_no_puede_hacer_pedido_de_un_producto_propio(self):
        Producto.objects.filter(pk=self.producto_a.pk).update(usuario=self.comprador)
        self.client.force_authenticate(self.comprador)

        respuesta = self.client.post(
            self.url_lista,
            self.datos_pedido([{"producto": self.producto_a.pk, "cantidad": 1}]),
            format="json",
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Pedido.objects.count(), 0)

    def test_rechaza_productos_inactivos_de_vendedores_distintos_y_repetidos(self):
        self.client.force_authenticate(self.comprador)
        casos = [
            [{"producto": self.producto_inactivo.pk, "cantidad": 1}],
            [
                {"producto": self.producto_a.pk, "cantidad": 1},
                {"producto": self.producto_otro_vendedor.pk, "cantidad": 1},
            ],
            [
                {"producto": self.producto_a.pk, "cantidad": 1},
                {"producto": self.producto_a.pk, "cantidad": 2},
            ],
            [],
        ]

        for detalles in casos:
            with self.subTest(detalles=detalles):
                respuesta = self.client.post(
                    self.url_lista,
                    self.datos_pedido(detalles),
                    format="json",
                )
                self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(Pedido.objects.count(), 0)

    def test_confirmar_descuenta_todo_el_stock_y_no_permite_doble_descuento(self):
        pedido_id, _ = self.crear_pedido()
        self.client.force_authenticate(self.vendedor)

        respuesta = self.client.post(self.url_accion("confirmar", pedido_id))
        respuesta_repetida = self.client.post(self.url_accion("confirmar", pedido_id))

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)
        self.assertEqual(respuesta.data["estado"], EstadoPedido.EN_PREPARACION)
        self.assertEqual(respuesta_repetida.status_code, status.HTTP_400_BAD_REQUEST)
        self.producto_a.refresh_from_db()
        self.producto_b.refresh_from_db()
        self.assertEqual(self.producto_a.stock, 8)
        self.assertEqual(self.producto_b.stock, 4)

    def test_stock_insuficiente_revierte_estado_y_todos_los_descuentos(self):
        pedido_id, _ = self.crear_pedido([
            {"producto": self.producto_a.pk, "cantidad": 2},
            {"producto": self.producto_b.pk, "cantidad": 4},
        ])
        Producto.objects.filter(pk=self.producto_b.pk).update(stock=3)
        self.client.force_authenticate(self.vendedor)

        respuesta = self.client.post(self.url_accion("confirmar", pedido_id))

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.producto_a.refresh_from_db()
        self.producto_b.refresh_from_db()
        pedido = Pedido.objects.get(pk=pedido_id)
        self.assertEqual(self.producto_a.stock, 10)
        self.assertEqual(self.producto_b.stock, 3)
        self.assertEqual(pedido.estado, EstadoPedido.PENDIENTE)

    def test_cancelar_pendiente_no_modifica_stock_y_no_es_repetible(self):
        pedido_id, _ = self.crear_pedido()
        self.client.force_authenticate(self.vendedor)

        respuesta = self.client.post(self.url_accion("cancelar", pedido_id))
        respuesta_repetida = self.client.post(self.url_accion("cancelar", pedido_id))

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)
        self.assertEqual(respuesta.data["estado"], EstadoPedido.CANCELADO)
        self.assertEqual(respuesta_repetida.status_code, status.HTTP_400_BAD_REQUEST)
        self.producto_a.refresh_from_db()
        self.producto_b.refresh_from_db()
        self.assertEqual(self.producto_a.stock, 10)
        self.assertEqual(self.producto_b.stock, 5)

    def test_cancelar_en_preparacion_restaura_stock_una_sola_vez(self):
        pedido_id, _ = self.crear_pedido()
        self.client.force_authenticate(self.vendedor)
        self.client.post(self.url_accion("confirmar", pedido_id))

        respuesta = self.client.post(self.url_accion("cancelar", pedido_id))
        respuesta_repetida = self.client.post(self.url_accion("cancelar", pedido_id))

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)
        self.assertEqual(respuesta.data["estado"], EstadoPedido.CANCELADO)
        self.assertEqual(respuesta_repetida.status_code, status.HTTP_400_BAD_REQUEST)
        self.producto_a.refresh_from_db()
        self.producto_b.refresh_from_db()
        self.assertEqual(self.producto_a.stock, 10)
        self.assertEqual(self.producto_b.stock, 5)

    def test_completar_solo_desde_preparacion(self):
        pedido_id, _ = self.crear_pedido()
        self.client.force_authenticate(self.vendedor)

        respuesta_pendiente = self.client.post(self.url_accion("completar", pedido_id))
        self.assertEqual(respuesta_pendiente.status_code, status.HTTP_400_BAD_REQUEST)
        self.client.post(self.url_accion("confirmar", pedido_id))
        respuesta_completar = self.client.post(self.url_accion("completar", pedido_id))
        respuesta_repetida = self.client.post(self.url_accion("completar", pedido_id))

        self.assertEqual(respuesta_completar.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta_completar.data["estado"], EstadoPedido.COMPLETADO)
        self.assertEqual(respuesta_repetida.status_code, status.HTTP_400_BAD_REQUEST)
        self.producto_a.refresh_from_db()
        self.producto_b.refresh_from_db()
        self.assertEqual(self.producto_a.stock, 8)
        self.assertEqual(self.producto_b.stock, 4)

    def test_solo_el_vendedor_propietario_puede_gestionar_el_pedido(self):
        pedido_id, _ = self.crear_pedido()

        self.client.force_authenticate(self.otro_vendedor)
        for accion in ("confirmar", "cancelar", "completar"):
            with self.subTest(usuario="otro vendedor", accion=accion):
                respuesta = self.client.post(self.url_accion(accion, pedido_id))
                self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

        self.client.force_authenticate(self.comprador)
        for accion in ("confirmar", "cancelar", "completar"):
            with self.subTest(usuario="comprador", accion=accion):
                respuesta = self.client.post(self.url_accion(accion, pedido_id))
                self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

        self.producto_a.refresh_from_db()
        self.assertEqual(self.producto_a.stock, 10)
        self.assertEqual(Pedido.objects.get(pk=pedido_id).estado, EstadoPedido.PENDIENTE)

    def test_usuario_no_autenticado_no_puede_crear_ni_listar_pedidos(self):
        respuesta_crear = self.client.post(
            self.url_lista,
            self.datos_pedido(),
            format="json",
        )
        respuesta_listar = self.client.get(self.url_lista)

        self.assertIn(
            respuesta_crear.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )
        self.assertIn(
            respuesta_listar.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )
        self.assertEqual(Pedido.objects.count(), 0)

    def test_compradores_solo_pueden_listar_y_consultar_sus_pedidos(self):
        pedido_propio_id, _ = self.crear_pedido()
        pedido_ajeno_id, _ = self.crear_pedido(
            [{"producto": self.producto_a.pk, "cantidad": 1}],
            comprador=self.otro_comprador,
        )

        self.client.force_authenticate(self.comprador)
        respuesta_lista = self.client.get(self.url_lista)
        respuesta_propio = self.client.get(
            reverse("pedido-detail", args=[pedido_propio_id])
        )
        respuesta_ajeno = self.client.get(
            reverse("pedido-detail", args=[pedido_ajeno_id])
        )

        self.assertEqual(respuesta_lista.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [pedido["id"] for pedido in respuesta_lista.data],
            [pedido_propio_id],
        )
        self.assertEqual(respuesta_propio.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta_ajeno.status_code, status.HTTP_404_NOT_FOUND)

        self.client.force_authenticate(self.otro_comprador)
        respuesta_otra_lista = self.client.get(self.url_lista)
        self.assertEqual(
            [pedido["id"] for pedido in respuesta_otra_lista.data],
            [pedido_ajeno_id],
        )

    def test_campesinos_solo_pueden_listar_y_consultar_pedidos_recibidos(self):
        pedido_vendedor_id, _ = self.crear_pedido(
            [{"producto": self.producto_a.pk, "cantidad": 1}]
        )
        pedido_otro_vendedor_id, _ = self.crear_pedido(
            [{"producto": self.producto_otro_vendedor.pk, "cantidad": 1}]
        )

        self.client.force_authenticate(self.vendedor)
        respuesta_lista = self.client.get(self.url_lista)
        respuesta_propio = self.client.get(
            reverse("pedido-detail", args=[pedido_vendedor_id])
        )
        respuesta_ajeno = self.client.get(
            reverse("pedido-detail", args=[pedido_otro_vendedor_id])
        )

        self.assertEqual(respuesta_lista.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [pedido["id"] for pedido in respuesta_lista.data],
            [pedido_vendedor_id],
        )
        self.assertEqual(respuesta_propio.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta_ajeno.status_code, status.HTTP_404_NOT_FOUND)

        self.client.force_authenticate(self.otro_vendedor)
        respuesta_otra_lista = self.client.get(self.url_lista)
        self.assertEqual(
            [pedido["id"] for pedido in respuesta_otra_lista.data],
            [pedido_otro_vendedor_id],
        )
