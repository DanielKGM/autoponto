from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .academico import HorarioAula, MatriculaTurma
from .base import BaseModel
from .dispositivos import DispositivoEsp32
from .identidade import PapelUsuario, Usuario


class Aula(BaseModel):
    STATUS_PLANEJADA = "PLANEJADA"
    STATUS_ABERTA = "ABERTA"
    STATUS_FECHADA = "FECHADA"
    STATUS_CANCELADA = "CANCELADA"
    STATUS_CHOICES = (
        (STATUS_PLANEJADA, "Planejada"),
        (STATUS_ABERTA, "Aberta"),
        (STATUS_FECHADA, "Fechada"),
        (STATUS_CANCELADA, "Cancelada"),
    )

    horario = models.ForeignKey(HorarioAula, on_delete=models.CASCADE, related_name="aulas")
    data = models.DateField()
    inicio = models.DateTimeField()
    fim = models.DateTimeField()
    chamada_inicio = models.DateTimeField()
    chamada_fim = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PLANEJADA)
    fechada_em = models.DateTimeField(null=True, blank=True)
    fechada_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="aulas_fechadas",
    )

    class Meta:
        ordering = ("data", "inicio")
        verbose_name = "Aula"
        verbose_name_plural = "Aulas"
        constraints = [
            models.UniqueConstraint(fields=("horario", "data"), name="aula_unica_por_horario_data"),
        ]

    def clean(self):
        if self.fim <= self.inicio:
            raise ValidationError({"fim": "O fim da aula deve ser maior que o início."})
        if self.chamada_fim <= self.chamada_inicio:
            raise ValidationError({"chamada_fim": "O fim da chamada deve ser maior que o início da chamada."})
        if self.chamada_inicio < self.inicio:
            raise ValidationError({"chamada_inicio": "A chamada não pode abrir antes da aula."})
        if self.chamada_fim > self.fim:
            raise ValidationError({"chamada_fim": "A chamada não pode fechar depois da aula."})
        if self.horario_id and self.data.weekday() != self.horario.dia_semana:
            raise ValidationError({"data": "A data da aula não corresponde ao dia da semana do horário."})

    def __str__(self) -> str:
        return f"{self.horario.turma} em {self.data}"


class RegistroPresenca(BaseModel):
    STATUS_PRESENTE = "PRESENTE"
    STATUS_AUSENTE = "AUSENTE"
    STATUS_ATRASO = "ATRASO"
    STATUS_JUSTIFICADA = "JUSTIFICADA"
    STATUS_CHOICES = (
        (STATUS_PRESENTE, "Presente"),
        (STATUS_AUSENTE, "Ausente"),
        (STATUS_ATRASO, "Atraso"),
        (STATUS_JUSTIFICADA, "Justificada"),
    )

    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name="presencas")
    aluno = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="presencas")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PRESENTE)
    registrado_em = models.DateTimeField(default=timezone.now)
    registrado_por_dispositivo = models.ForeignKey(
        DispositivoEsp32,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="presencas_registradas",
    )

    class Meta:
        ordering = ("aula__data", "aluno__username")
        verbose_name = "Registro de presença"
        verbose_name_plural = "Registros de presença"
        constraints = [
            models.UniqueConstraint(fields=("aula", "aluno"), name="presenca_unica_por_aula_aluno"),
        ]

    def clean(self):
        if self.aluno.papel != PapelUsuario.ALUNO:
            raise ValidationError({"aluno": "Presença só pode ser registrada para alunos."})
        if self.aula_id:
            matriculado = MatriculaTurma.objects.filter(
                turma=self.aula.horario.turma,
                aluno=self.aluno,
                ativo=True,
            ).exists()
            if not matriculado:
                raise ValidationError({"aluno": "Aluno não está matriculado nessa turma."})

    def __str__(self) -> str:
        return f"{self.aluno} - {self.aula}"


class EventoReconhecimento(BaseModel):
    id_evento_origem = models.CharField(max_length=100, blank=True, null=True, unique=True)
    dispositivo = models.ForeignKey(DispositivoEsp32, on_delete=models.CASCADE, related_name="eventos_reconhecimento")
    aula = models.ForeignKey(
        Aula,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos_reconhecimento",
    )
    aluno_candidato = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos_reconhecimento",
    )
    confianca = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    reconhecido = models.BooleanField(default=False)
    ocorrido_em = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-ocorrido_em",)
        verbose_name = "Evento de reconhecimento"
        verbose_name_plural = "Eventos de reconhecimento"

    def clean(self):
        if self.aluno_candidato and self.aluno_candidato.papel != PapelUsuario.ALUNO:
            raise ValidationError({"aluno_candidato": "Candidatos de reconhecimento devem ser alunos."})

    def __str__(self) -> str:
        return f"{self.dispositivo.codigo} @ {self.ocorrido_em}"
