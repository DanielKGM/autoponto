from django.core.exceptions import ValidationError
from django.db import models

from .base import BaseModel
from .identidade import PapelUsuario, Usuario


class EmbeddingFacial(BaseModel):
    aluno = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="embeddings_faciais")
    versao_modelo = models.CharField(max_length=50)
    vetor = models.JSONField()
    status = models.CharField(
        max_length=20,
        choices=(
            ("ATIVO", "Ativo"),
            ("INATIVO", "Inativo"),
            ("REVOGADO", "Revogado"),
        ),
        default="ATIVO",
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ("aluno__username", "-criado_em")
        verbose_name = "Embedding facial"
        verbose_name_plural = "Embeddings faciais"
        constraints = [
            models.UniqueConstraint(
                fields=("aluno",),
                name="uq_embedding_aluno",
            ),
        ]

    def clean(self):
        if self.aluno.papel != PapelUsuario.ALUNO:
            raise ValidationError({"aluno": "Embeddings faciais so podem ser criados para alunos."})

    def __str__(self) -> str:
        return f"{self.aluno.username} ({self.versao_modelo})"
