import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .academico import Sala
from .base import BaseModel
from .identidade import Usuario


class NoBorda(BaseModel):
    codigo = models.CharField(max_length=50, unique=True)
    nome = models.CharField(max_length=255)
    ativo = models.BooleanField(default=True)
    ultimo_sync_em = models.DateTimeField(null=True, blank=True)
    interscity_uuid = models.CharField(max_length=64, blank=True, db_index=True)

    @property
    def is_authenticated(self):
        return True

    class Meta:
        ordering = ("codigo",)
        verbose_name = "Nó de borda"
        verbose_name_plural = "Nós de borda"

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
        verbose_name = "Token do nó de borda"
        verbose_name_plural = "Tokens dos nós de borda"

    @staticmethod
    def gerar_hash(token_bruto: str) -> str:
        return hashlib.sha256(token_bruto.encode("utf-8")).hexdigest()

    @classmethod
    def emitir_token(cls, no: NoBorda, nome: str = "default", expira_em=None):
        if expira_em is None:
            expira_em = timezone.now() + timedelta(days=settings.NODE_TOKEN_EXPIRATION_DAYS)
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
        return self.ativo and self.expira_em is not None and self.expira_em > timezone.now()

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
    ultimo_sync_em = models.DateTimeField(null=True, blank=True)
    interscity_uuid = models.CharField(max_length=64, blank=True, db_index=True)

    class Meta:
        ordering = ("codigo",)
        verbose_name = "Dispositivo ESP32"
        verbose_name_plural = "Dispositivos ESP32"
        constraints = [
            models.UniqueConstraint(
                fields=("sala",),
                condition=Q(ativo=True),
                name="dispositivo_ativo_unico_por_sala",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nome}"


class ComandoBorda(BaseModel):
    STATUS_PENDENTE = "PENDENTE"
    STATUS_ENTREGUE = "ENTREGUE"
    STATUS_FALHOU = "FALHOU"
    STATUS_REJEITADO = "REJEITADO"
    STATUS_CHOICES = (
        (STATUS_PENDENTE, "Pendente"),
        (STATUS_ENTREGUE, "Entregue"),
        (STATUS_FALHOU, "Falhou"),
        (STATUS_REJEITADO, "Rejeitado"),
    )

    no = models.ForeignKey(NoBorda, on_delete=models.CASCADE, related_name="comandos")
    dispositivo = models.ForeignKey(
        DispositivoEsp32,
        on_delete=models.CASCADE,
        related_name="comandos",
        null=True,
        blank=True,
    )
    tipo = models.CharField(max_length=100)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    origem = models.CharField(max_length=50, default="backend")
    id_origem = models.CharField(max_length=100, blank=True, db_index=True)
    capacidade = models.CharField(max_length=100, blank=True)
    criado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comandos_borda_criados",
    )
    entregue_em = models.DateTimeField(null=True, blank=True)
    ultimo_erro = models.TextField(blank=True)

    class Meta:
        ordering = ("criado_em",)
        verbose_name = "Comando de borda"
        verbose_name_plural = "Comandos de borda"
        constraints = [
            models.UniqueConstraint(
                fields=("origem", "id_origem"),
                condition=~Q(id_origem=""),
                name="comando_borda_origem_id_unico",
            ),
        ]

    @staticmethod
    def normalizar_status(status: str) -> str:
        mapa = {
            "PENDING": ComandoBorda.STATUS_PENDENTE,
            "PENDENTE": ComandoBorda.STATUS_PENDENTE,
            "DELIVERED": ComandoBorda.STATUS_ENTREGUE,
            "ENTREGUE": ComandoBorda.STATUS_ENTREGUE,
            "FAILED": ComandoBorda.STATUS_FALHOU,
            "FALHOU": ComandoBorda.STATUS_FALHOU,
            "REJECTED": ComandoBorda.STATUS_REJEITADO,
            "REJEITADO": ComandoBorda.STATUS_REJEITADO,
        }
        normalizado = mapa.get(str(status).upper())
        if normalizado is None:
            raise ValidationError({"status": "Status de comando desconhecido."})
        return normalizado

    def clean(self):
        if self.dispositivo_id and self.no_id and self.dispositivo.no_id != self.no_id:
            raise ValidationError({"dispositivo": "O dispositivo deve pertencer ao nó do comando."})

    def marcar_status(self, status: str, erro: str = ""):
        self.status = self.normalizar_status(status)
        self.ultimo_erro = erro
        if self.status == self.STATUS_ENTREGUE:
            self.entregue_em = timezone.now()
        self.save(update_fields=["status", "ultimo_erro", "entregue_em", "atualizado_em"])

    def __str__(self) -> str:
        return f"{self.no.codigo}:{self.tipo}:{self.status}"
