from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from api.services.aulas import atualizar_status_aulas


def _parse_now(value: str | None):
    if not value:
        return timezone.now()
    parsed = parse_datetime(value)
    if not parsed:
        raise CommandError("Use --now em formato ISO, por exemplo 2026-06-25T08:00:00-03:00.")
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed)
    return parsed


class Command(BaseCommand):
    help = "Atualiza status de aulas planejadas/abertas conforme o horario atual."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Mostra quantas aulas seriam alteradas sem salvar mudancas.",
        )
        parser.add_argument(
            "--now",
            help="Data/hora ISO usada como base da execucao. Util para testes e auditoria.",
        )

    def handle(self, *args, **options):
        agora = _parse_now(options.get("now"))
        resultado = atualizar_status_aulas(agora=agora, dry_run=options["dry_run"])
        prefixo = "DRY-RUN " if options["dry_run"] else ""
        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"{prefixo}aulas atualizadas: "
                    f"planejadas_abertas={resultado['planejadas_abertas']}, "
                    f"planejadas_fechadas={resultado['planejadas_fechadas']}, "
                    f"abertas_fechadas={resultado['abertas_fechadas']}"
                )
            )
        )
