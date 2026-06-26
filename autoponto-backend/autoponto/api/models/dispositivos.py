import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .academico import Sala
from .base import BaseModel


class NoBorda(BaseModel):
    codigo = models.CharField(max_length=50, unique=True)
    nome = models.CharField(max_length=255)
    ativo = models.BooleanField(default=True)
    ultimo_sync_em = models.DateTimeField(null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )

    @property
    def is_authenticated(self):
        return True

    class Meta:
        ordering = ("codigo",)
        verbose_name = "No de borda"
        verbose_name_plural = "Nos de borda"

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nome}"


class TokenNoBorda(BaseModel):
    no = models.ForeignKey(NoBorda, on_delete=models.CASCADE, related_name="tokens")
    nome = models.CharField(max_length=100)
    prefixo_token = models.CharField(max_length=12, db_index=True)
    hash_token = models.CharField(max_length=64, unique=True)
    ativo = models.BooleanField(default=True)
    expira_em = models.DateTimeField(null=True, blank=True)
    ultimo_uso_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("no__codigo", "-criado_em")
        verbose_name = "Token do no de borda"
        verbose_name_plural = "Tokens dos nos de borda"

    @staticmethod
    def gerar_hash(token_bruto: str) -> str:
        return hashlib.sha256(token_bruto.encode("utf-8")).hexdigest()

    @classmethod
    def emitir_token(cls, no: NoBorda, nome: str = "default", expira_em=None):
        agora = timezone.now()
        if expira_em is None:
            expira_em = agora + timedelta(
                days=settings.NODE_TOKEN_EXPIRATION_DAYS
            )
        cls.objects.filter(no=no, nome=nome, ativo=True).update(
            ativo=False,
            atualizado_em=agora,
        )
        token_bruto = secrets.token_urlsafe(32)
        token = cls.objects.create(
            no=no,
            nome=nome,
            prefixo_token=token_bruto[:12],
            hash_token=cls.gerar_hash(token_bruto),
            expira_em=expira_em,
        )
        return token, token_bruto

    def confere(self, token_bruto: str) -> bool:
        return secrets.compare_digest(self.hash_token, self.gerar_hash(token_bruto))

    def pode_autenticar(self) -> bool:
        return (
            self.ativo
            and self.expira_em is not None
            and self.expira_em > timezone.now()
        )

    def __str__(self) -> str:
        return f"{self.no.codigo}:{self.nome}"


class DispositivoEsp32(BaseModel):
    no = models.ForeignKey(
        NoBorda,
        on_delete=models.PROTECT,
        related_name="dispositivos",
        null=True,
        blank=True,
    )
    sala = models.ForeignKey(
        Sala,
        on_delete=models.PROTECT,
        related_name="dispositivos",
        null=True,
        blank=True,
    )
    codigo = models.CharField(max_length=50, unique=True)
    nome = models.CharField(max_length=255)
    ativo = models.BooleanField(default=True)
    interscity_uuid = models.CharField(max_length=64, blank=True, db_index=True)

    class Meta:
        ordering = ("codigo",)
        verbose_name = "Dispositivo ESP32"
        verbose_name_plural = "Dispositivos ESP32"
        constraints = [
            models.UniqueConstraint(
                fields=("sala",),
                condition=Q(ativo=True),
                name="uq_disp_sala_ativo",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nome}"
