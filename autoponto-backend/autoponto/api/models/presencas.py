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
            models.UniqueConstraint(fields=("horario", "data"), name="uq_aula_horario_data"),
        ]

    def clean(self):
        if self.fim <= self.inicio:
            raise ValidationError({"fim": "O fim da aula deve ser maior que o inicio."})
        if self.horario_id and self.data.weekday() != self.horario.horario_padrao.weekday_python:
            raise ValidationError({"data": "A data da aula nao corresponde ao dia da semana do horario."})
        if self.horario_id:
            periodo = self.horario.turma.periodo_letivo
            if self.data < periodo.data_inicio or self.data > periodo.data_fim:
                raise ValidationError({"data": "A data da aula deve estar dentro do periodo letivo da turma."})

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
        verbose_name = "Registro de presenca"
        verbose_name_plural = "Registros de presenca"
        constraints = [
            models.UniqueConstraint(fields=("aula", "aluno"), name="uq_presenca_aula_aluno"),
        ]

    def clean(self):
        if self.aluno.papel != PapelUsuario.ALUNO:
            raise ValidationError({"aluno": "Presenca so pode ser registrada para alunos."})
        if self.aula_id:
            matriculado = MatriculaTurma.objects.filter(
                turma=self.aula.horario.turma,
                aluno=self.aluno,
                ativo=True,
            ).exists()
            if not matriculado:
                raise ValidationError({"aluno": "Aluno nao esta matriculado nessa turma."})

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
