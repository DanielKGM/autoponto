from django.db import transaction
from django.utils import timezone

from api.models import Aula, DispositivoEsp32, EventoReconhecimento, RegistroPresenca, Usuario
from .errors import DomainValidationError


@transaction.atomic
def registrar_presenca(*, aula: Aula, aluno: Usuario, dispositivo: DispositivoEsp32, status: str = "PRESENTE"):
    registro, _ = RegistroPresenca.objects.update_or_create(
        aula=aula,
        aluno=aluno,
        defaults={
            "status": status,
            "registrado_em": timezone.now(),
            "registrado_por_dispositivo": dispositivo,
        },
    )
    if aula.status == Aula.STATUS_PLANEJADA:
        aula.status = Aula.STATUS_ABERTA
        aula.save(update_fields=["status", "atualizado_em"])
    return registro


@transaction.atomic
def registrar_evento_reconhecimento(
    *,
    dispositivo: DispositivoEsp32,
    aula: Aula,
    aluno_candidato: Usuario | None,
    confianca,
    reconhecido: bool,
):
    if reconhecido and aluno_candidato is None:
        raise DomainValidationError("Um evento reconhecido precisa de um aluno candidato.")

    evento = EventoReconhecimento.objects.create(
        dispositivo=dispositivo,
        aula=aula,
        aluno_candidato=aluno_candidato,
        confianca=confianca,
        reconhecido=reconhecido,
    )

    registro = None
    if reconhecido and aluno_candidato is not None:
        registro = registrar_presenca(
            aula=aula,
            aluno=aluno_candidato,
            dispositivo=dispositivo,
        )
    return evento, registro
