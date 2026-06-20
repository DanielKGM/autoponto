from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from api.models import (
    Aula,
    DispositivoEsp32,
    EmbeddingFacial,
    EventoSincronizacaoBorda,
    MatriculaTurma,
    PapelUsuario,
    Sala,
    Usuario,
)
from api.services.auditoria_sync import registrar_evento_sync


def _acao_disponivel(disponivel: bool) -> str:
    return (
        EventoSincronizacaoBorda.Acao.UPSERT
        if disponivel
        else EventoSincronizacaoBorda.Acao.DELETE
    )


@receiver(post_save, sender=Sala)
def auditar_sala_salva(sender, instance: Sala, **kwargs):
    registrar_evento_sync(
        EventoSincronizacaoBorda.Entidade.SALAS,
        _acao_disponivel(instance.ativo),
        instance.id,
    )


@receiver(pre_delete, sender=Sala)
def auditar_sala_deletada(sender, instance: Sala, **kwargs):
    registrar_evento_sync(
        EventoSincronizacaoBorda.Entidade.SALAS,
        EventoSincronizacaoBorda.Acao.DELETE,
        instance.id,
    )


@receiver(post_save, sender=DispositivoEsp32)
def auditar_dispositivo_salvo(sender, instance: DispositivoEsp32, **kwargs):
    registrar_evento_sync(
        EventoSincronizacaoBorda.Entidade.DISPOSITIVOS,
        _acao_disponivel(instance.ativo and instance.no_id and instance.sala_id),
        instance.id,
    )


@receiver(pre_delete, sender=DispositivoEsp32)
def auditar_dispositivo_deletado(sender, instance: DispositivoEsp32, **kwargs):
    registrar_evento_sync(
        EventoSincronizacaoBorda.Entidade.DISPOSITIVOS,
        EventoSincronizacaoBorda.Acao.DELETE,
        instance.id,
    )


@receiver(post_save, sender=Aula)
def auditar_aula_salva(sender, instance: Aula, **kwargs):
    disponivel = (
        instance.turma.ativo
        and instance.status not in {Aula.STATUS_FECHADA, Aula.STATUS_CANCELADA}
    )
    acao = _acao_disponivel(disponivel)
    registrar_evento_sync(EventoSincronizacaoBorda.Entidade.AULAS, acao, instance.id)


@receiver(pre_delete, sender=Aula)
def auditar_aula_deletada(sender, instance: Aula, **kwargs):
    registrar_evento_sync(
        EventoSincronizacaoBorda.Entidade.AULAS,
        EventoSincronizacaoBorda.Acao.DELETE,
        instance.id,
    )


@receiver(post_save, sender=MatriculaTurma)
def auditar_matricula_salva(sender, instance: MatriculaTurma, **kwargs):
    acao = _acao_disponivel(
        instance.ativo
        and instance.aluno.is_active
        and instance.aluno.papel == PapelUsuario.ALUNO
    )
    registrar_evento_sync(
        EventoSincronizacaoBorda.Entidade.MATRICULAS_TURMA,
        acao,
        instance.id,
    )


@receiver(pre_delete, sender=MatriculaTurma)
def auditar_matricula_deletada(sender, instance: MatriculaTurma, **kwargs):
    registrar_evento_sync(
        EventoSincronizacaoBorda.Entidade.MATRICULAS_TURMA,
        EventoSincronizacaoBorda.Acao.DELETE,
        instance.id,
    )


@receiver(post_save, sender=Usuario)
def auditar_aluno_salvo(sender, instance: Usuario, **kwargs):
    if instance.papel != PapelUsuario.ALUNO:
        return
    acao = _acao_disponivel(instance.is_active)
    registrar_evento_sync(
        EventoSincronizacaoBorda.Entidade.ALUNOS,
        acao,
        instance.id,
    )
    for matricula in instance.matriculas_turma.filter(ativo=True):
        registrar_evento_sync(
            EventoSincronizacaoBorda.Entidade.MATRICULAS_TURMA,
            acao,
            matricula.id,
        )
    for embedding in instance.embeddings_faciais.filter(ativo=True):
        registrar_evento_sync(
            EventoSincronizacaoBorda.Entidade.EMBEDDINGS_FACIAIS,
            acao,
            embedding.id,
        )


@receiver(pre_delete, sender=Usuario)
def auditar_aluno_deletado(sender, instance: Usuario, **kwargs):
    if instance.papel != PapelUsuario.ALUNO:
        return
    registrar_evento_sync(
        EventoSincronizacaoBorda.Entidade.ALUNOS,
        EventoSincronizacaoBorda.Acao.DELETE,
        instance.id,
    )
    for matricula in instance.matriculas_turma.filter(ativo=True):
        registrar_evento_sync(
            EventoSincronizacaoBorda.Entidade.MATRICULAS_TURMA,
            EventoSincronizacaoBorda.Acao.DELETE,
            matricula.id,
        )
    for embedding in instance.embeddings_faciais.filter(ativo=True):
        registrar_evento_sync(
            EventoSincronizacaoBorda.Entidade.EMBEDDINGS_FACIAIS,
            EventoSincronizacaoBorda.Acao.DELETE,
            embedding.id,
        )


@receiver(post_save, sender=EmbeddingFacial)
def auditar_embedding_salvo(sender, instance: EmbeddingFacial, **kwargs):
    registrar_evento_sync(
        EventoSincronizacaoBorda.Entidade.EMBEDDINGS_FACIAIS,
        _acao_disponivel(instance.ativo and instance.status == "ATIVO"),
        instance.id,
    )


@receiver(pre_delete, sender=EmbeddingFacial)
def auditar_embedding_deletado(sender, instance: EmbeddingFacial, **kwargs):
    registrar_evento_sync(
        EventoSincronizacaoBorda.Entidade.EMBEDDINGS_FACIAIS,
        EventoSincronizacaoBorda.Acao.DELETE,
        instance.id,
    )
