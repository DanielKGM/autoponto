from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from .helpers import criar_contexto_academico


class FluxoApiTests(APITestCase):
    def setUp(self):
        self.contexto = criar_contexto_academico()

    def autenticar_admin(self):
        resposta = self.client.post(
            "/api/auth/token/",
            {"username": "admin", "password": "password123"},
            format="json",
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {resposta.data['access']}")

    def test_swagger_e_schema_estao_disponiveis(self):
        self.assertEqual(self.client.get("/api/schema/").status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get("/api/docs/").status_code, status.HTTP_200_OK)

    def test_jwt_permite_acessar_endpoint_protegido_em_portugues(self):
        self.autenticar_admin()
        resposta = self.client.get("/api/usuarios/")
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data["count"], 3)

    @patch("api.services.biometria.GeradorEmbeddingVisao")
    def test_fluxo_de_matricula_biometrica(self, gerador_cls):
        gerador_cls.return_value.gerar_embedding.return_value = ([0.1, 0.2, 0.3], {"quantidade_faces": 1})
        self.autenticar_admin()
        resposta = self.client.post(
            "/api/perfis-biometricos/matricular/",
            {
                "aluno_id": str(self.contexto["aluno"].id),
                "capturas": ["ZnJhbWUtMQ==", "ZnJhbWUtMg=="],
                "versao_modelo": "sface-v1",
            },
            format="json",
        )
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        embedding_id = resposta.data["embedding"]["id"]

        lista = self.client.get("/api/embeddings-faciais/")
        self.assertEqual(lista.status_code, status.HTTP_200_OK)
        self.assertEqual(lista.data["results"][0]["id"], embedding_id)
