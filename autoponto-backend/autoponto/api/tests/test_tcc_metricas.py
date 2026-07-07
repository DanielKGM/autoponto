import csv
import tempfile

from django.test import SimpleTestCase, override_settings
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView


class TccMetricasColetorTests(SimpleTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_coletor_desativado_nao_cria_arquivos(self):
        from api.services.tcc_metricas import registrar_tempo

        with override_settings(
            TCC_EVIDENCIAS_ENABLED=False,
            TCC_EVIDENCIAS_DIR=self.tmp.name,
        ):
            registrar_tempo(
                "endpoint_me_ms",
                12.5,
                servico="servidor-principal",
                origem="teste",
            )

        self.assertFalse((self.tmp_path / "metricas_amostras.csv").exists())
        self.assertFalse((self.tmp_path / "metricas_resumo.txt").exists())

    def test_coletor_ativado_registra_csv_e_resumo(self):
        from api.services.tcc_metricas import registrar_evento, registrar_tempo

        with override_settings(
            TCC_EVIDENCIAS_ENABLED=True,
            TCC_EVIDENCIAS_DIR=self.tmp.name,
        ):
            registrar_tempo(
                "endpoint_me_ms",
                10,
                servico="servidor-principal",
                origem="teste",
            )
            registrar_tempo(
                "endpoint_me_ms",
                14,
                servico="servidor-principal",
                status="falha",
                origem="teste",
            )
            registrar_evento(
                "interscity_falha_total",
                servico="servidor-principal",
                status="falha_timeout",
                origem="teste",
            )

        amostras = self.tmp_path / "metricas_amostras.csv"
        resumo = self.tmp_path / "metricas_resumo.txt"
        self.assertTrue(amostras.exists())
        self.assertTrue(resumo.exists())

        with amostras.open(encoding="utf-8", newline="") as arquivo:
            linhas = list(csv.DictReader(arquivo))

        self.assertEqual(len(linhas), 3)
        self.assertEqual(linhas[0]["metrica"], "endpoint_me_ms")
        self.assertEqual(linhas[0]["valor"], "10")
        self.assertEqual(linhas[2]["unidade"], "evento")

        conteudo_resumo = resumo.read_text(encoding="utf-8")
        self.assertIn(
            "endpoint_me_ms|servidor-principal|ms|2|12.000|2.828|1|1|0",
            conteudo_resumo,
        )
        self.assertIn(
            "interscity_falha_total|servidor-principal|evento|1|||0|1|0",
            conteudo_resumo,
        )

    def test_criptografia_registra_metricas_sem_vazar_vetor(self):
        from api.services.crypto_biometria import criptografar_vetor, descriptografar_vetor

        with override_settings(
            TCC_EVIDENCIAS_ENABLED=True,
            TCC_EVIDENCIAS_DIR=self.tmp.name,
            FACE_EMBEDDING_ENCRYPTION_KEY="v7nWfK7qM5Pq8HNjKkNPF4I2kGMbYd3ga6g3TzldnNk=",
        ):
            payload = criptografar_vetor([1.0, 2.0])
            vetor = descriptografar_vetor(payload)

        self.assertEqual(vetor, [1.0, 2.0])

        with (self.tmp_path / "metricas_amostras.csv").open(
            encoding="utf-8",
            newline="",
        ) as arquivo:
            linhas = list(csv.DictReader(arquivo))

        self.assertEqual(
            [linha["metrica"] for linha in linhas],
            ["embedding_criptografia_ms", "embedding_descriptografia_ms"],
        )
        self.assertEqual(linhas[0]["detalhes"], '{"dimensoes":2}')
        self.assertEqual(linhas[1]["detalhes"], '{"dimensoes":2}')

    @property
    def tmp_path(self):
        from pathlib import Path

        return Path(self.tmp.name)


class MetricasEndpointMixinTests(SimpleTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_mixin_registra_tempo_do_endpoint(self):
        from api.views.mixins import MetricasEndpointMixin

        class DummyView(MetricasEndpointMixin, APIView):
            authentication_classes = ()
            permission_classes = ()
            metrica_endpoint = "endpoint_me_ms"

            def get(self, request):
                return Response({"ok": True})

        request = APIRequestFactory().get("/api/me/")

        with override_settings(
            TCC_EVIDENCIAS_ENABLED=True,
            TCC_EVIDENCIAS_DIR=self.tmp.name,
        ):
            response = DummyView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        amostras = self.tmp_path / "metricas_amostras.csv"
        with amostras.open(encoding="utf-8", newline="") as arquivo:
            linhas = list(csv.DictReader(arquivo))

        self.assertEqual(len(linhas), 1)
        self.assertEqual(linhas[0]["metrica"], "endpoint_me_ms")
        self.assertEqual(linhas[0]["servico"], "servidor-principal")
        self.assertEqual(linhas[0]["status"], "sucesso")

    @property
    def tmp_path(self):
        from pathlib import Path

        return Path(self.tmp.name)
