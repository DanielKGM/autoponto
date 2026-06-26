from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from .base import BaseModel
from .identidade import PapelUsuario, Usuario


class EmbeddingFacial(BaseModel):
    STATUS_ATIVO = "ATIVO"
    STATUS_INATIVO = "INATIVO"
    STATUS_REVOGADO = "REVOGADO"
    STATUS_CHOICES = (
        (STATUS_ATIVO, "Ativo"),
        (STATUS_INATIVO, "Inativo"),
        (STATUS_REVOGADO, "Revogado"),
    )

    aluno = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="embeddings_faciais")
    versao_modelo = models.CharField(max_length=50)
    vetor = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ATIVO,
    )
    ativo = models.BooleanField(default=True)
    revogado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("aluno__username", "-criado_em")
        verbose_name = "Embedding facial"
        verbose_name_plural = "Embeddings faciais"
        constraints = [
            models.UniqueConstraint(
                fields=("aluno",),
                condition=Q(ativo=True, status="ATIVO"),
                name="uq_embedding_aluno_ativo",
            ),
        ]

    def clean(self):
        if self.aluno.papel != PapelUsuario.ALUNO:
            raise ValidationError({"aluno": "Embeddings faciais so podem ser criados para alunos."})

    def __str__(self) -> str:
        return f"{self.aluno.username} ({self.versao_modelo})"
