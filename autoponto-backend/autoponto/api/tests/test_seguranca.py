from datetime import date, time, timedelta
from unittest.mock import patch

from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import (
    ComandoBorda,
    DispositivoEsp32,
    EmbeddingFacial,
    HorarioAula,
    MatriculaTurma,
    NoBorda,
    PapelUsuario,
    PerfilBiometrico,
    RegistroPresenca,
    Sala,
    TokenNoBorda,
    Turma,
    Usuario,
)
from api.services import obter_ou_criar_aula
from .helpers import criar_contexto_academico


class SegurancaApiTests(APITestCase):
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
        return resposta

    def criar_turma_alheia(self):
        professor = Usuario.objects.create_user(
            username="professor2",
            password="password123",
            email="professor2@example.com",
            papel=PapelUsuario.PROFESSOR,
            nome_completo="Professor Dois",
        )
        aluno = Usuario.objects.create_user(
            username="aluno2",
            password="password123",
            email="aluno2@example.com",
            papel=PapelUsuario.ALUNO,
            nome_completo="Aluno Dois",
            matricula="20260002",
        )
        sala = Sala.objects.create(
            predio=self.contexto["predio"],
            nome="Laboratorio 102",
            codigo="LAB102",
        )
        turma = Turma.objects.create(
            periodo_letivo=self.contexto["periodo"],
            disciplina=self.contexto["disciplina"],
            codigo="B",
        )
        turma.professores.add(professor)
        MatriculaTurma.objects.create(turma=turma, aluno=aluno)
        horario = HorarioAula.objects.create(
            turma=turma,
            sala=sala,
            dia_semana=0,
            horario_inicio=time(10, 0),
            horario_fim=time(11, 40),
        )
        aula, _ = obter_ou_criar_aula(horario, date(2026, 4, 20))
        return professor, aluno, turma, aula

    def test_node_token_nao_autentica_endpoints_administrativos(self):
        no = NoBorda.objects.create(codigo="NO-SEG", nome="No de Seguranca")
        _, token_bruto = TokenNoBorda.emitir_token(no, nome="seguranca")
        self.client.credentials(HTTP_AUTHORIZATION=f"NodeToken {token_bruto}")

        resposta = self.client.get("/api/campi/")

        self.assertIn(resposta.status_code, {status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN})

    def test_node_token_de_no_inativo_nao_acessa_edge(self):
        no = NoBorda.objects.create(codigo="NO-INATIVO", nome="No Inativo", ativo=False)
        _, token_bruto = TokenNoBorda.emitir_token(no, nome="seguranca")
        self.client.credentials(HTTP_AUTHORIZATION=f"NodeToken {token_bruto}")

        resposta = self.client.get("/api/edge/pull", {"node_id": no.codigo})

        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_professor_nao_lista_presencas_de_turma_alheia(self):
        _, aluno, _, aula = self.criar_turma_alheia()
        RegistroPresenca.objects.create(aula=aula, aluno=aluno)
        self.autenticar("professor")

        resposta = self.client.get("/api/presencas/")

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data["count"], 0)

    def test_professor_nao_cria_presenca_em_turma_alheia(self):
        _, aluno, _, aula = self.criar_turma_alheia()
        self.autenticar("professor")

        resposta = self.client.post(
            "/api/presencas/",
            {"aula": str(aula.id), "aluno": str(aluno.id), "status": "PRESENTE"},
            format="json",
        )

        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(RegistroPresenca.objects.count(), 0)

    def test_professor_sem_turma_filtrada_ve_historico_apenas_das_suas_turmas(self):
        aula_propria, _ = obter_ou_criar_aula(self.contexto["horario"], self.contexto["data_aula"])
        RegistroPresenca.objects.create(aula=aula_propria, aluno=self.contexto["aluno"])
        professor2, _, _, aula_alheia = self.criar_turma_alheia()
        aula_alheia.horario.turma.matriculas.create(aluno=self.contexto["aluno"])
        RegistroPresenca.objects.create(aula=aula_alheia, aluno=self.contexto["aluno"])
        self.assertNotEqual(professor2, self.contexto["professor"])
        self.autenticar("professor")

        resposta = self.client.get(f"/api/relatorios/alunos/{self.contexto['aluno'].id}/presencas/")

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data["presencas"]), 1)
        self.assertEqual(resposta.data["presencas"][0]["turma_id"], str(self.contexto["turma"].id))

    def test_professor_nao_acessa_embeddings_faciais(self):
        perfil = PerfilBiometrico.objects.create(aluno=self.contexto["aluno"], status="ATIVO")
        EmbeddingFacial.objects.create(
            perfil=perfil,
            versao_modelo="sface",
            vetor=[0.1, 0.2],
            status="ATIVO",
            ativo=True,
        )
        self.autenticar("professor")

        resposta = self.client.get("/api/embeddings-faciais/")

        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(INTERSCITY_ENABLED=True, INTERSCITY_WEBHOOK_SECRET="segredo")
    def test_webhook_interscity_exige_segredo(self):
        self.contexto["dispositivo"].interscity_uuid = "uuid-seguro"
        self.contexto["dispositivo"].no = NoBorda.objects.create(codigo="NO-SEG", nome="No Seguro")
        self.contexto["dispositivo"].save(update_fields=["interscity_uuid", "no", "atualizado_em"])
        payload = {
            "action": "actuator_command",
            "command": {
                "_id": {"$oid": "cmd-seguro-1"},
                "uuid": "uuid-seguro",
                "capability": "autoponto_edge_command",
                "value": {"type": "display_message", "payload": {"message": "ok"}},
            },
        }

        sem_token = self.client.post("/api/interscity/webhooks/actuator/", payload, format="json")
        errado = self.client.post(
            "/api/interscity/webhooks/actuator/",
            payload,
            format="json",
            HTTP_X_AUTO_PONTO_WEBHOOK_TOKEN="errado",
        )
        correto = self.client.post(
            "/api/interscity/webhooks/actuator/",
            payload,
            format="json",
            HTTP_X_AUTO_PONTO_WEBHOOK_TOKEN="segredo",
        )

        self.assertEqual(sem_token.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(errado.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(correto.status_code, status.HTTP_202_ACCEPTED)

    @override_settings(INTERSCITY_ENABLED=True, INTERSCITY_WEBHOOK_SECRET="segredo")
    def test_webhook_interscity_nao_reabre_comando_entregue_por_replay(self):
        no = NoBorda.objects.create(codigo="NO-REPLAY", nome="No Replay")
        self.contexto["dispositivo"].no = no
        self.contexto["dispositivo"].interscity_uuid = "uuid-replay"
        self.contexto["dispositivo"].save(update_fields=["no", "interscity_uuid", "atualizado_em"])
        payload = {
            "action": "actuator_command",
            "command": {
                "_id": {"$oid": "cmd-replay-1"},
                "uuid": "uuid-replay",
                "capability": "autoponto_edge_command",
                "value": {"type": "display_message", "payload": {"message": "ok"}},
            },
        }
        headers = {"HTTP_X_AUTO_PONTO_WEBHOOK_TOKEN": "segredo"}

        primeira = self.client.post("/api/interscity/webhooks/actuator/", payload, format="json", **headers)
        comando = ComandoBorda.objects.get()
        comando.marcar_status("DELIVERED")
        replay = self.client.post("/api/interscity/webhooks/actuator/", payload, format="json", **headers)

        self.assertEqual(primeira.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(replay.status_code, status.HTTP_202_ACCEPTED)
        comando.refresh_from_db()
        self.assertEqual(comando.status, ComandoBorda.STATUS_ENTREGUE)

    @override_settings(FACE_MAX_CAPTURAS=1)
    @patch("api.services.biometria.GeradorEmbeddingVisao")
    def test_biometria_rejeita_excesso_de_capturas_antes_de_processar_imagem(self, gerador_cls):
        self.autenticar("aluno")

        resposta = self.client.post(
            "/api/me/biometria/",
            {"capturas": ["a", "b"], "versao_modelo": "sface"},
            format="json",
        )

        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        gerador_cls.assert_not_called()

    @override_settings(FACE_MAX_IMAGE_BYTES=4)
    @patch("api.services.biometria.GeradorEmbeddingVisao")
    def test_biometria_rejeita_base64_maior_que_limite(self, gerador_cls):
        self.autenticar("aluno")

        resposta = self.client.post(
            "/api/me/biometria/",
            {"capturas": ["MTIzNDU="], "versao_modelo": "sface"},
            format="json",
        )

        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        gerador_cls.assert_not_called()

    def test_login_envia_refresh_em_cookie_httponly_sem_expor_no_json(self):
        resposta = self.client.post(
            "/api/auth/token/",
            {"username": "aluno", "password": "password123"},
            format="json",
        )

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertIn("access", resposta.data)
        self.assertNotIn("refresh", resposta.data)
        self.assertIn("autoponto_refresh", resposta.cookies)
        self.assertTrue(resposta.cookies["autoponto_refresh"]["httponly"])

    def test_refresh_usa_cookie_httponly(self):
        login = self.client.post(
            "/api/auth/token/",
            {"username": "aluno", "password": "password123"},
            format="json",
        )
        self.client.cookies["autoponto_refresh"] = login.cookies["autoponto_refresh"].value

        resposta = self.client.post("/api/auth/token/refresh/", {}, format="json")

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertIn("access", resposta.data)
        self.assertNotIn("refresh", resposta.data)
