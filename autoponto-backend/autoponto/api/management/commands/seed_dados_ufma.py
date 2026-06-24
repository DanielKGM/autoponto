from datetime import date, time

from django.core.management.base import BaseCommand
from django.utils import timezone

from api.models import (
    Campus,
    Curso,
    Disciplina,
    DispositivoEsp32,
    HorarioPadraoUFMA,
    NoBorda,
    PeriodoLetivo,
    Predio,
    Sala,
    TokenNoBorda,
    Turma,
)
from api.services.aulas import sincronizar_aulas_da_turma

SLOTS_UFMA = {
    "M": {
        "1": (time(7, 30), time(8, 20)),
        "2": (time(8, 20), time(9, 10)),
        "3": (time(9, 20), time(10, 10)),
        "4": (time(10, 10), time(11, 0)),
        "5": (time(11, 10), time(12, 0)),
        "6": (time(12, 0), time(12, 50)),
    },
    "T": {
        "1": (time(13, 10), time(14, 0)),
        "2": (time(14, 0), time(14, 50)),
        "3": (time(14, 50), time(15, 40)),
        "4": (time(15, 50), time(16, 40)),
        "5": (time(16, 40), time(17, 30)),
        "6": (time(17, 30), time(18, 30)),
    },
    "N": {
        "1": (time(18, 30), time(19, 20)),
        "2": (time(19, 20), time(20, 10)),
        "3": (time(20, 20), time(21, 10)),
        "4": (time(21, 10), time(22, 0)),
    },
}

TOKEN_SEED_NOME = "seed-edge"
CODIGOS_DEV_24H = tuple(f"{dia}M123456" for dia in range(2, 9))


class Command(BaseCommand):
    help = "Cria/atualiza o cenario de seed do TCC AutoPonto na UFMA."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dev",
            action="store_true",
            help="Cria horarios 24h de segunda a domingo para desenvolvimento local.",
        )

    def handle(self, *args, **options):
        usar_horarios_dev_24h = options["dev"]
        campus = self._criar_topologia_academica()
        curso, disciplina, periodo, sala = self._criar_oferta_academica(campus)
        turma = self._criar_turma(periodo, disciplina)
        self._criar_horarios_ufma()
        if usar_horarios_dev_24h:
            self._criar_horarios_dev_24h()
        self._criar_horarios_aula(turma, sala, usar_horarios_dev_24h)
        no = self._criar_infraestrutura_iot(sala)
        self._emitir_token_no_borda(no)
        self.stdout.write(self.style.SUCCESS("Seed UFMA/TCC criado ou atualizado."))

    def _criar_topologia_academica(self):
        campus, _ = Campus.objects.update_or_create(
            nome="Cidade Universitaria Dom Delgado - Sao Luis",
            defaults={"ativo": True},
        )
        Predio.objects.update_or_create(
            campus=campus,
            nome="BICT",
            defaults={"ativo": True},
        )
        predio_paulo_freire, _ = Predio.objects.update_or_create(
            campus=campus,
            nome="Paulo Freire",
            defaults={"ativo": True},
        )
        Sala.objects.update_or_create(
            predio=predio_paulo_freire,
            codigo="105N",
            defaults={"nome": "105 Norte", "ativo": True},
        )
        return campus

    def _criar_oferta_academica(self, campus):
        periodo, _ = PeriodoLetivo.objects.update_or_create(
            nome="2026.1",
            defaults={
                "data_inicio": date(2026, 3, 16),
                "data_fim": date(2026, 7, 18),
                "ativo": True,
            },
        )
        curso, _ = Curso.objects.update_or_create(
            campus=campus,
            nome="Engenharia da Computacao",
            defaults={"ativo": True},
        )
        disciplina, _ = Disciplina.objects.update_or_create(
            curso=curso,
            codigo="EECP0021",
            defaults={"nome": "SISTEMAS DISTRIBUIDOS", "ativo": True},
        )
        sala = Sala.objects.get(predio__campus=campus, codigo="105N")
        return curso, disciplina, periodo, sala

    def _criar_turma(self, periodo, disciplina):
        turma, _ = Turma.objects.update_or_create(
            periodo_letivo=periodo,
            disciplina=disciplina,
            codigo="20261EECP0021",
            defaults={"ativo": True},
        )
        return turma

    def _criar_horarios_ufma(self):
        for dia in range(2, 8):
            for turno, slots in SLOTS_UFMA.items():
                for numero in slots:
                    self._criar_horario_padrao(f"{dia}{turno}{numero}")
        self._criar_horario_padrao("2N34")
        self._criar_horario_padrao("4N34")

    def _criar_horarios_dev_24h(self):
        for dia, codigo in enumerate(CODIGOS_DEV_24H, start=2):
            HorarioPadraoUFMA.objects.update_or_create(
                codigo=codigo,
                defaults={
                    "dia_semana": dia,
                    "horario_inicio": time(0, 0),
                    "horario_fim": time(23, 59),
                    "ativo": True,
                },
            )

    def _criar_horarios_aula(self, turma, sala, usar_horarios_dev_24h):
        codigos = CODIGOS_DEV_24H if usar_horarios_dev_24h else ("2N34", "4N34")
        sincronizar_aulas_da_turma(
            turma,
            [
                {
                    "sala": sala,
                    "horario_padrao": HorarioPadraoUFMA.objects.get(codigo=codigo),
                }
                for codigo in codigos
            ],
        )

    def _criar_infraestrutura_iot(self, sala):
        no, _ = NoBorda.objects.update_or_create(
            codigo="88A29E606012",
            defaults={
                "nome": "raspberry-tcc",
                "ativo": True,
                "latitude": "-2.558300",
                "longitude": "-44.307700",
            },
        )
        DispositivoEsp32.objects.update_or_create(
            codigo="9084CED6CDC0",
            defaults={
                "nome": "esp32-tcc",
                "no": no,
                "sala": sala,
                "ativo": True,
                "interscity_uuid": "57395bf6-d8c8-49dd-aa28-57ce7a3d68c3",
            },
        )
        return no

    def _emitir_token_no_borda(self, no):
        token_existente = no.tokens.filter(
            nome=TOKEN_SEED_NOME,
            ativo=True,
            expira_em__gt=timezone.now(),
        ).first()
        if token_existente:
            self.stdout.write(
                self.style.WARNING(
                    "Token ativo do seed ja existe; o valor bruto nao pode ser recuperado."
                )
            )
            return

        _, token_bruto = TokenNoBorda.emitir_token(no, nome=TOKEN_SEED_NOME)
        self.stdout.write(
            self.style.SUCCESS(
                "Token do no de borda criado. Use o valor abaixo como MAIN_API_TOKEN."
            )
        )
        self.stdout.write(f"MAIN_API_TOKEN={token_bruto}")

    def _criar_horario_padrao(self, codigo):
        codigo = codigo.upper()
        dia = int(codigo[0])
        turno = codigo[1]
        numeros = codigo[2:]
        inicio = SLOTS_UFMA[turno][numeros[0]][0]
        fim = SLOTS_UFMA[turno][numeros[-1]][1]
        HorarioPadraoUFMA.objects.update_or_create(
            codigo=codigo,
            defaults={
                "dia_semana": dia,
                "horario_inicio": inicio,
                "horario_fim": fim,
                "ativo": True,
            },
        )
