from datetime import date
from unittest.mock import patch
from urllib.error import URLError

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import (
    EmbeddingFacial,
    MatriculaTurma,
    PapelUsuario,
    PerfilBiometrico,
    RegistroPresenca,
    Usuario,
)
from api.services import obter_ou_criar_aula
from .helpers import criar_contexto_academico


class FrontendApiTests(APITestCase):
    def setUp(self):
        self.contexto = criar_contexto_academico()

    def autenticar(self, usuario: str):
        resposta = self.client.post(
            "/api/auth/token/",
            {"username": usuario, "password": "password123"},
            format="json",
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {resposta.data['access']}")

    def test_me_retorna_usuario_e_permissoes_de_tela(self):
        self.autenticar("aluno")

        resposta = self.client.get("/api/me/")

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data["usuario"]["papel"], "ALUNO")
        self.assertIn("aluno", resposta.data["permissoes"]["areas"])
        self.assertNotIn("admin", resposta.data["permissoes"]["areas"])

    def test_aluno_lista_apenas_suas_turmas_e_presencas(self):
        aula, _ = obter_ou_criar_aula(self.contexto["horario"], self.contexto["data_aula"])
        RegistroPresenca.objects.create(aula=aula, aluno=self.contexto["aluno"])
        self.autenticar("aluno")

        turmas = self.client.get("/api/me/turmas/")
        presencas = self.client.get("/api/me/presencas/")

        self.assertEqual(turmas.status_code, status.HTTP_200_OK)
        self.assertEqual(turmas.data[0]["turma_id"], str(self.contexto["turma"].id))
        self.assertEqual(presencas.status_code, status.HTTP_200_OK)
        self.assertEqual(presencas.data[0]["status"], "PRESENTE")
        self.assertEqual(presencas.data[0]["disciplina"], self.contexto["disciplina"].nome)

    @override_settings(FACE_DUPLICATE_THRESHOLD=0.90)
    @patch("api.services.biometria.GeradorEmbeddingVisao")
    def test_aluno_nao_cadastra_rosto_igual_a_outro_aluno(self, gerador_cls):
        outro = Usuario.objects.create_user(
            username="outro-aluno",
            password="password123",
            email="outro@example.com",
            papel=PapelUsuario.ALUNO,
            nome_completo="Outro Aluno",
            matricula="20260002",
        )
        perfil = PerfilBiometrico.objects.create(aluno=outro, status="ATIVO")
        EmbeddingFacial.objects.create(
            perfil=perfil,
            versao_modelo="sface-v1",
            vetor=[1.0, 0.0, 0.0],
            status="ATIVO",
            ativo=True,
        )
        gerador_cls.return_value.gerar_embedding.return_value = ([1.0, 0.0, 0.0], {"quantidade_faces": 1})
        self.autenticar("aluno")

        resposta = self.client.post(
            "/api/me/biometria/",
            {
                "capturas": ["ZnJhbWUtMQ=="],
                "versao_modelo": "sface-v1",
            },
            format="json",
        )

        self.assertEqual(resposta.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("rosto", resposta.data["detail"].lower())

    def test_professor_relatorio_presencas_da_turma_por_data(self):
        segundo_aluno = Usuario.objects.create_user(
            username="aluno2",
            password="password123",
            email="aluno2@example.com",
            papel=PapelUsuario.ALUNO,
            nome_completo="Aluno Dois",
            matricula="20260003",
        )
        MatriculaTurma.objects.create(turma=self.contexto["turma"], aluno=segundo_aluno)
        aula, _ = obter_ou_criar_aula(self.contexto["horario"], self.contexto["data_aula"])
        RegistroPresenca.objects.create(aula=aula, aluno=self.contexto["aluno"])
        self.autenticar("professor")

        resposta = self.client.get(
            f"/api/relatorios/turmas/{self.contexto['turma'].id}/presencas/",
            {"data": "2026-04-20"},
        )

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data["turma_id"], str(self.contexto["turma"].id))
        self.assertEqual(resposta.data["totais"], {"presentes": 1, "ausentes": 1, "matriculados": 2})
        presentes = [item for item in resposta.data["alunos"] if item["status"] == "PRESENTE"]
        ausentes = [item for item in resposta.data["alunos"] if item["status"] == "AUSENTE"]
        self.assertEqual(presentes[0]["aluno_id"], str(self.contexto["aluno"].id))
        self.assertEqual(ausentes[0]["aluno_id"], str(segundo_aluno.id))

    def test_professor_nao_acessa_relatorio_de_turma_de_outro_professor(self):
        outro_professor = Usuario.objects.create_user(
            username="professor2",
            password="password123",
            email="professor2@example.com",
            papel=PapelUsuario.PROFESSOR,
        )
        self.contexto["turma"].professores.clear()
        self.contexto["turma"].professores.add(outro_professor)
        self.autenticar("professor")

        resposta = self.client.get(
            f"/api/relatorios/turmas/{self.contexto['turma'].id}/presencas/",
            {"data": "2026-04-20"},
        )

        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_relatorio_resumo_da_turma(self):
        aula, _ = obter_ou_criar_aula(self.contexto["horario"], self.contexto["data_aula"])
        RegistroPresenca.objects.create(aula=aula, aluno=self.contexto["aluno"])
        self.autenticar("admin")

        resposta = self.client.get(
            f"/api/relatorios/turmas/{self.contexto['turma'].id}/resumo/",
            {"inicio": "2026-04-20", "fim": "2026-04-20"},
        )

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data["total_aulas"], 1)
        self.assertEqual(resposta.data["alunos"][0]["percentual_presenca"], 100.0)

    def test_professor_fecha_chamada_da_propria_aula(self):
        aula, _ = obter_ou_criar_aula(self.contexto["horario"], self.contexto["data_aula"])
        fim_original = aula.fim
        self.autenticar("professor")

        resposta = self.client.post(f"/api/aulas/{aula.id}/fechar-chamada/")

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        aula.refresh_from_db()
        self.assertEqual(aula.status, "FECHADA")
        self.assertEqual(aula.fechada_por, self.contexto["professor"])
        self.assertEqual(aula.fim, fim_original)

    def test_professor_nao_fecha_chamada_de_turma_alheia(self):
        outro_professor = Usuario.objects.create_user(
            username="professor2",
            password="password123",
            email="professor2@example.com",
            papel=PapelUsuario.PROFESSOR,
        )
        self.contexto["turma"].professores.clear()
        self.contexto["turma"].professores.add(outro_professor)
        aula, _ = obter_ou_criar_aula(self.contexto["horario"], self.contexto["data_aula"])
        self.autenticar("professor")

        resposta = self.client.post(f"/api/aulas/{aula.id}/fechar-chamada/")

        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(INTERSCITY_ENABLED=True)
    @patch("api.services.interscity.urlopen", side_effect=URLError("collector offline"))
    def test_admin_lista_status_dispositivos_com_fallback_local_quando_collector_falha(self, urlopen):
        self.contexto["dispositivo"].status = "idle"
        self.contexto["dispositivo"].interscity_uuid = "uuid-esp32"
        self.contexto["dispositivo"].save(update_fields=["status", "interscity_uuid", "atualizado_em"])
        self.autenticar("admin")

        resposta = self.client.get("/api/dispositivos-esp32/status-dashboard/", {"incluir_interscity": "true"})

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data[0]["id"], str(self.contexto["dispositivo"].id))
        self.assertEqual(resposta.data[0]["status"], "idle")
        self.assertEqual(resposta.data[0]["status_efetivo"], "offline")
        self.assertEqual(resposta.data[0]["origem_status"], "local")
        urlopen.assert_called()

    def test_admin_pesquisa_historico_de_presencas_do_aluno(self):
        aula, _ = obter_ou_criar_aula(self.contexto["horario"], self.contexto["data_aula"])
        RegistroPresenca.objects.create(aula=aula, aluno=self.contexto["aluno"])
        self.autenticar("admin")

        resposta = self.client.get(
            f"/api/relatorios/alunos/{self.contexto['aluno'].id}/presencas/",
            {"turma": str(self.contexto["turma"].id), "periodo_letivo": str(self.contexto["periodo"].id)},
        )

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data["aluno_id"], str(self.contexto["aluno"].id))
        self.assertEqual(resposta.data["presencas"][0]["data"], date(2026, 4, 20).isoformat())
