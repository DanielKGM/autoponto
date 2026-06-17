from django.core.management import call_command
from django.test import TestCase

from api.models import (
    Campus,
    Curso,
    Disciplina,
    DispositivoEsp32,
    HorarioAula,
    HorarioPadraoUFMA,
    MatriculaTurma,
    NoBorda,
    PapelUsuario,
    PeriodoLetivo,
    Predio,
    Sala,
    Turma,
    Usuario,
)


class SeedDadosUFMATests(TestCase):
    def test_seed_tcc_cria_cenario_base_sem_matricular_alunos(self):
        call_command("seed_dados_ufma")
        call_command("seed_dados_ufma")

        self.assertEqual(Campus.objects.filter(nome="Cidade Universitaria Dom Delgado - Sao Luis").count(), 1)
        self.assertTrue(Predio.objects.filter(nome="Paulo Freire").exists())
        self.assertTrue(Predio.objects.filter(nome="BICT").exists())
        self.assertTrue(Sala.objects.filter(codigo="105N", nome="105 Norte").exists())
        self.assertTrue(PeriodoLetivo.objects.filter(nome="2026.1", ativo=True).exists())
        self.assertTrue(Curso.objects.filter(nome="Engenharia da Computacao").exists())
        self.assertTrue(Disciplina.objects.filter(codigo="EECP0021", nome="SISTEMAS DISTRIBUIDOS").exists())

        professor = Usuario.objects.get(username="luiz.henrique", papel=PapelUsuario.PROFESSOR)
        turma = Turma.objects.get(codigo="20261EECP0021")
        self.assertIn(professor, turma.professores.all())
        self.assertEqual(Usuario.objects.filter(papel=PapelUsuario.ALUNO).count(), 150)
        self.assertEqual(MatriculaTurma.objects.count(), 0)

        self.assertTrue(HorarioPadraoUFMA.objects.filter(codigo="2N34").exists())
        self.assertTrue(HorarioPadraoUFMA.objects.filter(codigo="4N34").exists())
        self.assertEqual(HorarioAula.objects.filter(turma=turma).count(), 2)

        no = NoBorda.objects.get(codigo="88A29E606012")
        self.assertEqual(no.nome, "raspberry-tcc")
        self.assertEqual(no.interscity_uuid, "91723758-5fe0-4a76-8f1a-6aaf97463d66")
        dispositivo = DispositivoEsp32.objects.get(codigo="9084CED6CDC0")
        self.assertEqual(dispositivo.nome, "esp32-tcc")
        self.assertEqual(dispositivo.no, no)
        self.assertEqual(dispositivo.interscity_uuid, "8cf4ce45-3aff-4aa2-81e0-27a2fc361f09")

    def test_seed_gera_usernames_sem_email_obrigatorio(self):
        call_command("seed_dados_ufma")

        daniel = Usuario.objects.get(matricula="20250013659")
        self.assertEqual(daniel.username, "daniel.campos")
        self.assertEqual(daniel.email, "")
        self.assertTrue(Usuario.objects.filter(username="daniel.lucas").exists())
        self.assertTrue(Usuario.objects.filter(username="daniel.nunes").exists())

