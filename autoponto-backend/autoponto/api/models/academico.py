import re

from django.core.exceptions import ValidationError
from django.db import models

from .base import BaseModel
from .identidade import PapelUsuario, Usuario


class Campus(BaseModel):
    nome = models.CharField(max_length=255, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ("nome",)
        verbose_name = "Campus"
        verbose_name_plural = "Campi"

    def __str__(self) -> str:
        return self.nome


class Predio(BaseModel):
    campus = models.ForeignKey(Campus, on_delete=models.PROTECT, related_name="predios")
    nome = models.CharField(max_length=255)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ("campus__nome", "nome")
        verbose_name = "Predio"
        verbose_name_plural = "Predios"
        constraints = [
            models.UniqueConstraint(fields=("campus", "nome"), name="uq_predio_campus_nome"),
        ]

    def __str__(self) -> str:
        return f"{self.campus.nome} - {self.nome}"


class Sala(BaseModel):
    predio = models.ForeignKey(Predio, on_delete=models.PROTECT, related_name="salas")
    nome = models.CharField(max_length=255)
    codigo = models.CharField(max_length=20)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ("predio__campus__nome", "predio__nome", "nome")
        verbose_name = "Sala"
        verbose_name_plural = "Salas"
        constraints = [
            models.UniqueConstraint(fields=("predio", "codigo"), name="uq_sala_predio_codigo"),
        ]

    def __str__(self) -> str:
        return f"{self.predio.nome}-{self.codigo}"


class PeriodoLetivo(BaseModel):
    nome = models.CharField(max_length=100, unique=True)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    ativo = models.BooleanField(default=False)

    class Meta:
        ordering = ("-data_inicio",)
        verbose_name = "Periodo letivo"
        verbose_name_plural = "Periodos letivos"

    def clean(self):
        if self.data_fim < self.data_inicio:
            raise ValidationError({"data_fim": "A data final deve ser maior ou igual a data inicial."})

    def __str__(self) -> str:
        return self.nome


class Curso(BaseModel):
    campus = models.ForeignKey(Campus, on_delete=models.PROTECT, related_name="cursos")
    nome = models.CharField(max_length=255)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ("nome",)
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        constraints = [
            models.UniqueConstraint(fields=("campus", "nome"), name="uq_curso_campus_nome"),
        ]

    def __str__(self) -> str:
        return self.nome


class Disciplina(BaseModel):
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, related_name="disciplinas")
    codigo = models.CharField(max_length=30)
    nome = models.CharField(max_length=255)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ("curso__nome", "codigo")
        verbose_name = "Disciplina"
        verbose_name_plural = "Disciplinas"
        constraints = [
            models.UniqueConstraint(fields=("curso", "codigo"), name="uq_disc_curso_codigo"),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nome}"


class Turma(BaseModel):
    periodo_letivo = models.ForeignKey(PeriodoLetivo, on_delete=models.PROTECT, related_name="turmas")
    disciplina = models.ForeignKey(Disciplina, on_delete=models.PROTECT, related_name="turmas")
    codigo = models.CharField(max_length=50)
    professores = models.ManyToManyField(Usuario, related_name="turmas_ministradas", blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ("periodo_letivo__data_inicio", "disciplina__codigo", "codigo")
        verbose_name = "Turma"
        verbose_name_plural = "Turmas"
        constraints = [
            models.UniqueConstraint(
                fields=("periodo_letivo", "disciplina", "codigo"),
                name="uq_turma_periodo_disc_cod",
            ),
        ]

    def clean(self):
        super().clean()
        if not self.pk:
            return
        professores_invalidos = self.professores.exclude(papel=PapelUsuario.PROFESSOR)
        if professores_invalidos.exists():
            raise ValidationError({"professores": "Apenas usuarios professores podem ser vinculados a turma."})

    def __str__(self) -> str:
        return f"{self.disciplina.codigo}-{self.codigo}"


class MatriculaTurma(BaseModel):
    turma = models.ForeignKey(Turma, on_delete=models.PROTECT, related_name="matriculas")
    aluno = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="matriculas_turma")
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ("turma__disciplina__codigo", "aluno__username")
        verbose_name = "Matricula em turma"
        verbose_name_plural = "Matriculas em turma"
        constraints = [
            models.UniqueConstraint(fields=("turma", "aluno"), name="uq_matricula_turma_aluno"),
        ]

    def clean(self):
        if self.aluno.papel != PapelUsuario.ALUNO:
            raise ValidationError({"aluno": "Apenas usuarios alunos podem ser matriculados em turmas."})

    def __str__(self) -> str:
        return f"{self.aluno} em {self.turma}"


class HorarioPadraoUFMA(BaseModel):
    class DiaSemana(models.IntegerChoices):
        SEGUNDA = 2, "Segunda-feira"
        TERCA = 3, "Terca-feira"
        QUARTA = 4, "Quarta-feira"
        QUINTA = 5, "Quinta-feira"
        SEXTA = 6, "Sexta-feira"
        SABADO = 7, "Sabado"
        DOMINGO = 8, "Domingo"

    codigo = models.CharField(max_length=20, unique=True)
    dia_semana = models.PositiveSmallIntegerField(choices=DiaSemana.choices)
    horario_inicio = models.TimeField()
    horario_fim = models.TimeField()
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ("dia_semana", "horario_inicio", "codigo")
        verbose_name = "Horario padrao UFMA"
        verbose_name_plural = "Horarios padrao UFMA"

    @property
    def weekday_python(self) -> int:
        return int(self.dia_semana) - 2

    def clean(self):
        self.codigo = (self.codigo or "").strip().upper()
        if not re.fullmatch(r"[2-8][MTN][1-6]+", self.codigo):
            raise ValidationError(
                {
                    "codigo": (
                        "Use um codigo UFMA normalizado por dia, como 2M12. "
                        "Codigos compostos como 25M34 devem virar 2M34 e 5M34."
                    )
                }
            )
        if int(self.codigo[0]) != int(self.dia_semana):
            raise ValidationError({"dia_semana": "O dia da semana deve corresponder ao primeiro digito do codigo."})
        if self.horario_fim <= self.horario_inicio:
            raise ValidationError({"horario_fim": "O horario final deve ser maior que o inicial."})

    def __str__(self) -> str:
        return f"{self.codigo} {self.horario_inicio}-{self.horario_fim}"
