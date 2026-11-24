from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse

from apps.usuarios.models import Roles


Usuario = get_user_model()


class RegistroUsuarioTests(APITestCase):
    def setUp(self):
        self.url = reverse("usuario-list")
        self.password = "ClaveSegura-2026!"
        self.datos_registro = {
            "password": self.password,
            "username": "comprador_prueba",
            "first_name": "Ana",
            "last_name": "Prueba",
            "email": "ana@example.com",
            "documento": "123456789",
            "celular": "3001234567",
            "tipo_registro": "comprador",
        }

    def test_registro_responde_correctamente_y_no_expone_password(self):
        respuesta = self.client.post(self.url, self.datos_registro, format="json")

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", respuesta.json())

    def test_registro_guarda_password_con_hash_verificable(self):
        respuesta = self.client.post(self.url, self.datos_registro, format="json")

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        usuario = Usuario.objects.get(username=self.datos_registro["username"])
        self.assertNotEqual(usuario.password, self.password)
        self.assertTrue(usuario.check_password(self.password))

    def test_perfil_propio_devuelve_id_y_rol(self):
        usuario = Usuario.objects.create_user(
            username="perfil_comprador",
            password="ClaveSegura-2026!",
            documento="doc-perfil",
            celular="cel-perfil",
            rol=Roles.COMPRADOR,
        )
        self.client.force_authenticate(usuario)

        respuesta = self.client.get(reverse("usuario-me"))

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["id"], usuario.pk)
        self.assertEqual(respuesta.data["rol"], Roles.COMPRADOR)

    def test_perfil_propio_requiere_autenticacion(self):
        respuesta = self.client.get(reverse("usuario-me"))

        self.assertIn(
            respuesta.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )


class AdministracionUsuariosTests(APITestCase):
    def setUp(self):
        self.admin = self.crear_usuario("admin_negocio", Roles.ADMIN)
        self.comprador = self.crear_usuario("comprador_admin_test", Roles.COMPRADOR)
        self.campesino = self.crear_usuario("campesino_admin_test", Roles.CAMPESINO)

    def crear_usuario(self, username, rol):
        return Usuario.objects.create_user(
            username=username,
            password="ClaveSegura-2026!",
            documento=f"doc-{username}",
            celular=f"cel-{username}",
            rol=rol,
        )

    def test_admin_lista_y_consulta_usuarios_con_datos_minimos(self):
        self.assertFalse(self.admin.is_staff)
        self.assertFalse(self.admin.is_superuser)
        self.client.force_authenticate(self.admin)

        respuesta_lista = self.client.get(reverse("usuario-list"))
        respuesta_detalle = self.client.get(
            reverse("usuario-detail", args=[self.campesino.pk])
        )

        self.assertEqual(respuesta_lista.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta_detalle.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(respuesta_detalle.data),
            {"id", "username", "first_name", "last_name", "rol", "is_active"},
        )
        self.assertNotIn("documento", respuesta_detalle.data)
        self.assertNotIn("celular", respuesta_detalle.data)
        self.assertNotIn("email", respuesta_detalle.data)
        self.assertNotIn("is_staff", respuesta_detalle.data)
        self.assertNotIn("is_superuser", respuesta_detalle.data)

    def test_listado_administrativo_incluye_usuarios_inactivos(self):
        self.comprador.is_active = False
        self.comprador.save(update_fields=["is_active"])
        self.client.force_authenticate(self.admin)

        respuesta = self.client.get(reverse("usuario-list"))
        comprador = next(
            usuario for usuario in respuesta.data
            if usuario["id"] == self.comprador.pk
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertFalse(comprador["is_active"])

    def test_usuario_inactivo_no_puede_autenticarse_ni_usar_la_api(self):
        token = self.client.post(
            reverse("token_obtain_pair"),
            {"username": self.comprador.username, "password": "ClaveSegura-2026!"},
            format="json",
        )
        self.assertEqual(token.status_code, status.HTTP_200_OK)

        self.comprador.is_active = False
        self.comprador.save(update_fields=["is_active"])
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.data['access']}")
        respuesta_api = self.client.get(reverse("usuario-me"))
        respuesta_login = self.client.post(
            reverse("token_obtain_pair"),
            {"username": self.comprador.username, "password": "ClaveSegura-2026!"},
            format="json",
        )

        self.assertEqual(respuesta_api.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(respuesta_login.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_comprador_y_campesino_no_acceden_a_gestion_global_ni_acciones(self):
        for usuario in (self.comprador, self.campesino):
            with self.subTest(rol=usuario.rol):
                self.client.force_authenticate(usuario)
                respuesta_lista = self.client.get(reverse("usuario-list"))
                respuesta_desactivar = self.client.post(
                    reverse("usuario-desactivar", args=[self.comprador.pk])
                )
                respuesta_activar = self.client.post(
                    reverse("usuario-activar", args=[self.comprador.pk])
                )
                self.assertEqual(
                    respuesta_lista.status_code,
                    status.HTTP_403_FORBIDDEN,
                )
                self.assertEqual(
                    respuesta_desactivar.status_code,
                    status.HTTP_403_FORBIDDEN,
                )
                self.assertEqual(
                    respuesta_activar.status_code,
                    status.HTTP_403_FORBIDDEN,
                )

        self.comprador.refresh_from_db()
        self.assertTrue(self.comprador.is_active)

    def test_admin_activa_y_desactiva_usuarios_sin_cambiar_flags_privilegiados(self):
        self.client.force_authenticate(self.admin)
        self.comprador.is_active = False
        self.comprador.save(update_fields=["is_active"])

        respuesta_activar = self.client.post(
            reverse("usuario-activar", args=[self.comprador.pk])
        )
        respuesta_desactivar = self.client.post(
            reverse("usuario-desactivar", args=[self.comprador.pk])
        )

        self.comprador.refresh_from_db()
        self.assertEqual(respuesta_activar.status_code, status.HTTP_200_OK)
        self.assertTrue(respuesta_activar.data["is_active"])
        self.assertEqual(respuesta_desactivar.status_code, status.HTTP_200_OK)
        self.assertFalse(respuesta_desactivar.data["is_active"])
        self.assertFalse(self.comprador.is_active)
        self.assertFalse(self.comprador.is_staff)
        self.assertFalse(self.comprador.is_superuser)
        self.assertEqual(self.comprador.rol, Roles.COMPRADOR)

    def test_admin_no_puede_auto_desactivarse_ni_eliminar_usuarios(self):
        self.client.force_authenticate(self.admin)

        respuesta_desactivar = self.client.post(
            reverse("usuario-desactivar", args=[self.admin.pk])
        )
        respuesta_eliminar = self.client.delete(
            reverse("usuario-detail", args=[self.comprador.pk])
        )

        self.assertEqual(respuesta_desactivar.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(respuesta_eliminar.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Usuario.objects.filter(pk=self.comprador.pk).exists())
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_campos_privilegiados_se_rechazan_y_no_se_modifican(self):
        self.client.force_authenticate(self.admin)

        for metodo in ("put", "patch"):
            for campo, valor in (
                ("rol", Roles.ADMIN),
                ("is_active", False),
                ("is_staff", True),
                ("is_superuser", True),
            ):
                with self.subTest(metodo=metodo, campo=campo):
                    respuesta = getattr(self.client, metodo)(
                        reverse("usuario-detail", args=[self.comprador.pk]),
                        {campo: valor},
                        format="json",
                    )
                    self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

        self.comprador.refresh_from_db()
        self.assertEqual(self.comprador.rol, Roles.COMPRADOR)
        self.assertTrue(self.comprador.is_active)
        self.assertFalse(self.comprador.is_staff)
        self.assertFalse(self.comprador.is_superuser)

    def test_respuesta_de_actualizacion_admin_no_expone_datos_personales(self):
        self.client.force_authenticate(self.admin)

        respuesta = self.client.patch(
            reverse("usuario-detail", args=[self.comprador.pk]),
            {"email": "nuevo@example.com"},
            format="json",
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(respuesta.data),
            {"id", "username", "first_name", "last_name", "rol", "is_active"},
        )
        for campo in ("documento", "celular", "email", "password", "is_staff", "is_superuser"):
            self.assertNotIn(campo, respuesta.data)
        self.comprador.refresh_from_db()
        self.assertEqual(self.comprador.email, "nuevo@example.com")

    def test_no_se_puede_desactivar_al_ultimo_admin_activo(self):
        otro_admin = self.crear_usuario("ultimo_admin", Roles.ADMIN)
        self.admin.is_active = False
        self.admin.save(update_fields=["is_active"])
        self.client.force_authenticate(self.admin)

        respuesta = self.client.post(
            reverse("usuario-desactivar", args=[otro_admin.pk])
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        otro_admin.refresh_from_db()
        self.assertTrue(otro_admin.is_active)

    def test_puede_desactivar_otro_admin_si_queda_uno_activo(self):
        otro_admin = self.crear_usuario("admin_secundario", Roles.ADMIN)
        self.client.force_authenticate(self.admin)

        respuesta = self.client.post(
            reverse("usuario-desactivar", args=[otro_admin.pk])
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        otro_admin.refresh_from_db()
        self.admin.refresh_from_db()
        self.assertFalse(otro_admin.is_active)
        self.assertTrue(self.admin.is_active)

    def test_registro_publico_no_permite_crear_admin(self):
        data = {
            "password": "ClaveSegura-2026!",
            "username": "admin_publico",
            "first_name": "Admin",
            "last_name": "No permitido",
            "email": "admin@example.com",
            "documento": "doc-admin-publico",
            "celular": "cel-admin-publico",
            "tipo_registro": Roles.ADMIN,
        }

        respuesta = self.client.post(reverse("usuario-list"), data, format="json")

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Usuario.objects.filter(username="admin_publico").exists())
