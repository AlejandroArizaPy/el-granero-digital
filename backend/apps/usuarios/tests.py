from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse


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
