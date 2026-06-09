from django.core.management.base import BaseCommand

from api.models import Campus, Curso, Disciplina, Predio, Sala


class Command(BaseCommand):
    help = "Cria dados-base de exemplo para Engenharia da Computação UFMA São Luís."

    disciplinas = [
        ("EECP0036", "Desenvolvimento de Sistemas Web"),
        ("EECP0029", "Inteligência Artificial"),
        ("EECP0015", "Banco de Dados"),
    ]

    def handle(self, *args, **options):
        campus, _ = Campus.objects.update_or_create(
            codigo="SLZ",
            defaults={"nome": "Campus Dom Delgado", "ativo": True},
        )
        predio, _ = Predio.objects.update_or_create(
            campus=campus,
            codigo="CCET",
            defaults={"nome": "Centro de Ciências Exatas e Tecnologia", "ativo": True},
        )
        Sala.objects.update_or_create(
            predio=predio,
            codigo="LAB101",
            defaults={"nome": "Laboratório 101", "ativo": True},
        )
        curso, _ = Curso.objects.update_or_create(
            codigo="ECP-UFMA",
            defaults={
                "campus": campus,
                "nome": "Engenharia da Computação",
                "ativo": True,
            },
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

        self.stdout.write(self.style.SUCCESS("Dados de exemplo da UFMA criados/atualizados."))
