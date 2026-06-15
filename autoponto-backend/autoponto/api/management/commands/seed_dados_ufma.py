from datetime import time

from django.core.management.base import BaseCommand

from api.models import Campus, Curso, Disciplina, HorarioPadraoUFMA, Predio, Sala


class Command(BaseCommand):
    help = "Cria dados-base de exemplo para Engenharia da Computacao UFMA Sao Luis."

    disciplinas = [
        ("EECP0036", "Desenvolvimento de Sistemas Web"),
        ("EECP0029", "Inteligencia Artificial"),
        ("EECP0015", "Banco de Dados"),
    ]
    horarios = [
        ("2M12", HorarioPadraoUFMA.DiaSemana.SEGUNDA, time(8, 0), time(9, 40)),
        ("2M34", HorarioPadraoUFMA.DiaSemana.SEGUNDA, time(10, 0), time(11, 40)),
        ("5M34", HorarioPadraoUFMA.DiaSemana.QUINTA, time(10, 0), time(11, 40)),
        ("3T12", HorarioPadraoUFMA.DiaSemana.TERCA, time(14, 0), time(15, 40)),
        ("4N12", HorarioPadraoUFMA.DiaSemana.QUARTA, time(18, 30), time(20, 10)),
    ]

    def handle(self, *args, **options):
        campus, _ = Campus.objects.update_or_create(
            nome="Campus Dom Delgado",
            defaults={"ativo": True},
        )
        predio, _ = Predio.objects.update_or_create(
            campus=campus,
            nome="Centro de Ciencias Exatas e Tecnologia",
            defaults={"ativo": True},
        )
        Sala.objects.update_or_create(
            predio=predio,
            codigo="LAB101",
            defaults={"nome": "Laboratorio 101", "ativo": True},
        )
        curso, _ = Curso.objects.update_or_create(
            campus=campus,
            nome="Engenharia da Computacao",
            defaults={"ativo": True},
        )

        for codigo, nome in self.disciplinas:
            Disciplina.objects.update_or_create(
                curso=curso,
                codigo=codigo,
                defaults={
                    "nome": nome,
                    "ativo": True,
                },
            )

        for codigo, dia_semana, inicio, fim in self.horarios:
            HorarioPadraoUFMA.objects.update_or_create(
                codigo=codigo,
                defaults={
                    "dia_semana": dia_semana,
                    "horario_inicio": inicio,
                    "horario_fim": fim,
                    "ativo": True,
                },
            )

        self.stdout.write(self.style.SUCCESS("Dados de exemplo da UFMA criados/atualizados."))
