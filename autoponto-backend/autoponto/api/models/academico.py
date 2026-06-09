from django.core.exceptions import ValidationError
from django.db import models

from .base import BaseModel
from .identidade import PapelUsuario, Usuario


class Campus(BaseModel):
    nome = models.CharField(max_length=255, unique=True)
    codigo = models.CharField(max_length=20, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ("nome",)
        verbose_name = "Campus"
        verbose_name_plural = "Campi"

    def __str__(self) -> str:
        return self.nome


class Predio(BaseModel):
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name="predios")
    nome = models.CharField(max_length=255)
    codigo = models.CharField(max_length=20)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ("campus__nome", "nome")
        verbose_name = "Prédio"
        verbose_name_plural = "Prédios"
        constraints = [
            models.UniqueConstraint(fields=("campus", "codigo"), name="predio_codigo_unico_por_campus"),
        ]

    def __str__(self) -> str:
        return f"{self.campus.codigo}-{self.nome}"


class Sala(BaseModel):
    predio = models.ForeignKey(Predio, on_delete=models.CASCADE, related_name="salas")
    nome = models.CharField(max_length=255)
    codigo = models.CharField(max_length=20)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ("predio__campus__nome", "predio__nome", "nome")
        verbose_name = "Sala"
        verbose_name_plural = "Salas"
        constraints = [
            models.UniqueConstraint(fields=("predio", "codigo"), name="sala_codigo_unico_por_predio"),
        ]

    def __str__(self) -> str:
        return f"{self.predio.codigo}-{self.codigo}"


class PeriodoLetivo(BaseModel):
    nome = models.CharField(max_length=100, unique=True)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    ativo = models.BooleanField(default=False)

    class Meta:
        ordering = ("-data_inicio",)
        verbose_name = "Período letivo"
        verbose_name_plural = "Períodos letivos"

    def clean(self):
        if self.data_fim < self.data_inicio:
            raise ValidationError({"data_fim": "A data final deve ser maior ou igual à data inicial."})

    def __str__(self) -> str:
        return self.nome


class Curso(BaseModel):
    campus = models.ForeignKey(Campus, on_delete=models.PROTECT, related_name="cursos")
    codigo = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=255)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ("codigo",)
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nome}"


class Disciplina(BaseModel):
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, related_name="disciplinas")
    codigo = models.CharField(max_length=30)
    nome = models.CharField(max_length=255)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ("curso__codigo", "codigo")
        verbose_name = "Disciplina"
        verbose_name_plural = "Disciplinas"
        constraints = [
            models.UniqueConstraint(fields=("curso", "codigo"), name="disciplina_codigo_unico_por_curso"),
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
                name="turma_codigo_unico_por_periodo_disciplina",
            ),
        ]

    def clean(self):
        super().clean()
        if not self.pk:
            return
        professores_invalidos = self.professores.exclude(papel=PapelUsuario.PROFESSOR)
        if professores_invalidos.exists():
            raise ValidationError({"professores": "Apenas usuários professores podem ser vinculados à turma."})

    def __str__(self) -> str:
        return f"{self.disciplina.codigo}-{self.codigo}"


class MatriculaTurma(BaseModel):
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name="matriculas")
    aluno = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="matriculas_turma")
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ("turma__disciplina__codigo", "aluno__username")
        verbose_name = "Matrícula em turma"
        verbose_name_plural = "Matrículas em turma"
        constraints = [
            models.UniqueConstraint(fields=("turma", "aluno"), name="matricula_unica_por_turma_aluno"),
        ]

    def clean(self):
        if self.aluno.papel != PapelUsuario.ALUNO:
            raise ValidationError({"aluno": "Apenas usuários alunos podem ser matriculados em turmas."})

    def __str__(self) -> str:
        return f"{self.aluno} em {self.turma}"


class HorarioAula(BaseModel):
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name="horarios")
    sala = models.ForeignKey(Sala, on_delete=models.PROTECT, related_name="horarios_aula")
    dia_semana = models.PositiveSmallIntegerField()
    horario_inicio = models.TimeField()
    horario_fim = models.TimeField()
    abre_chamada_minutos = models.PositiveSmallIntegerField(default=0)
    fecha_chamada_minutos = models.PositiveSmallIntegerField(null=True, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ("turma__disciplina__codigo", "dia_semana", "horario_inicio")
        verbose_name = "Horário de aula"
        verbose_name_plural = "Horários de aula"
        constraints = [
            models.UniqueConstraint(
                fields=("turma", "dia_semana", "horario_inicio"),
                name="horario_unico_por_turma_dia_inicio",
            ),
        ]

    def clean(self):
        if self.dia_semana > 6:
            raise ValidationError({"dia_semana": "O dia da semana deve estar entre 0 e 6."})
        if self.horario_fim <= self.horario_inicio:
            raise ValidationError({"horario_fim": "O horário final deve ser maior que o inicial."})

        duracao = (
            self.horario_fim.hour * 60
            + self.horario_fim.minute
            - self.horario_inicio.hour * 60
            - self.horario_inicio.minute
        )
        if self.abre_chamada_minutos >= duracao:
            raise ValidationError(
                {"abre_chamada_minutos": "A chamada deve abrir antes do fim da aula."}
            )
        if self.fecha_chamada_minutos is not None:
            if self.fecha_chamada_minutos > duracao:
                raise ValidationError(
                    {"fecha_chamada_minutos": "A chamada não pode fechar depois do fim da aula."}
                )
            if self.fecha_chamada_minutos <= self.abre_chamada_minutos:
                raise ValidationError(
                    {"fecha_chamada_minutos": "O fechamento deve ser posterior à abertura da chamada."}
                )
        if not self.turma_id or not self.sala_id:
            return

        choque = HorarioAula.objects.filter(
            turma__periodo_letivo=self.turma.periodo_letivo,
            sala=self.sala,
            dia_semana=self.dia_semana,
            ativo=True,
            horario_inicio__lt=self.horario_fim,
            horario_fim__gt=self.horario_inicio,
        ).exclude(pk=self.pk)
        if choque.exists():
            raise ValidationError({"sala": "Já existe aula nessa sala no período, dia e horário informados."})

    def __str__(self) -> str:
        return f"{self.turma} {self.dia_semana} {self.horario_inicio}-{self.horario_fim}"
