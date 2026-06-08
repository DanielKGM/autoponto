from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from .base import BaseModel
from .identidade import PapelUsuario, Usuario


class PerfilBiometrico(BaseModel):
    aluno = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name="perfil_biometrico")
    status = models.CharField(
        max_length=20,
        choices=(
            ("PENDENTE", "Pendente"),
            ("ATIVO", "Ativo"),
            ("INATIVO", "Inativo"),
        ),
        default="PENDENTE",
    )
    observacoes = models.TextField(blank=True)

    class Meta:
        ordering = ("aluno__username",)
        verbose_name = "Perfil biométrico"
        verbose_name_plural = "Perfis biométricos"

    def clean(self):
        if self.aluno.papel != PapelUsuario.ALUNO:
            raise ValidationError({"aluno": "Perfis biométricos só podem ser criados para alunos."})

    def __str__(self) -> str:
        return f"Perfil biométrico de {self.aluno}"


class EmbeddingFacial(BaseModel):
    perfil = models.ForeignKey(PerfilBiometrico, on_delete=models.CASCADE, related_name="embeddings")
    versao_modelo = models.CharField(max_length=50)
    vetor = models.JSONField()
    pontuacao_qualidade = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    metadados_origem = models.JSONField(default=dict, blank=True)
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
        ordering = ("perfil__aluno__username", "-criado_em")
        verbose_name = "Embedding facial"
        verbose_name_plural = "Embeddings faciais"
        constraints = [
            models.UniqueConstraint(
                fields=("perfil",),
                condition=Q(ativo=True),
                name="embedding_ativo_unico_por_perfil",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.perfil.aluno.username} ({self.versao_modelo})"
