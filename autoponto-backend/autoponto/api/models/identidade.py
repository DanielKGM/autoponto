from django.contrib.auth.models import AbstractUser
from django.db import models

from .base import BaseModel


class PapelUsuario(models.TextChoices):
    ALUNO = "ALUNO", "Aluno"
    PROFESSOR = "PROFESSOR", "Professor"
    ADMINISTRADOR = "ADMINISTRADOR", "Administrador"


class Usuario(AbstractUser, BaseModel):
    email = models.EmailField(unique=True)
    papel = models.CharField(max_length=20, choices=PapelUsuario.choices)
    matricula = models.CharField(max_length=50, blank=True)
    nome_completo = models.CharField(max_length=255, blank=True)

    REQUIRED_FIELDS = ["email", "papel"]

    class Meta:
        ordering = ("username",)
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self) -> str:
        return self.nome_completo or self.username
