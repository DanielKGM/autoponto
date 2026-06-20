from django.db import models


class EventoSincronizacaoBorda(models.Model):
    class Entidade(models.TextChoices):
        SALAS = "salas", "Salas"
        DISPOSITIVOS = "dispositivos", "Dispositivos"
        AULAS = "aulas", "Aulas"
        ALUNOS = "alunos", "Alunos"
        MATRICULAS_TURMA = "matriculas_turma", "Matriculas em turma"
        EMBEDDINGS_FACIAIS = "embeddings_faciais", "Embeddings faciais"

    class Acao(models.TextChoices):
        UPSERT = "UPSERT", "Criar ou atualizar"
        DELETE = "DELETE", "Remover"

    entidade = models.CharField(max_length=40, choices=Entidade.choices, db_index=True)
    acao = models.CharField(max_length=10, choices=Acao.choices)
    identificador = models.UUIDField(db_index=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("id",)
        verbose_name = "Evento de sincronizacao de borda"
        verbose_name_plural = "Eventos de sincronizacao de borda"
        indexes = [
            models.Index(fields=("entidade", "identificador", "id")),
        ]

    def __str__(self) -> str:
        return f"{self.id} {self.entidade}:{self.identificador} {self.acao}"
