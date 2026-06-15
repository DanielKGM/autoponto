from django.contrib import admin

from api.models import (
    Aula,
    Campus,
    Curso,
    Disciplina,
    DispositivoEsp32,
    EmbeddingFacial,
    EventoReconhecimento,
    HorarioAula,
    HorarioPadraoUFMA,
    MatriculaTurma,
    NoBorda,
    PerfilBiometrico,
    PeriodoLetivo,
    Predio,
    RegistroPresenca,
    Sala,
    TokenNoBorda,
    Turma,
    Usuario,
)


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "papel", "matricula", "is_active")
    search_fields = ("username", "email", "nome_completo", "matricula")
    list_filter = ("papel", "is_active")


@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo")
    search_fields = ("nome",)
    list_filter = ("ativo",)


@admin.register(Predio)
class PredioAdmin(admin.ModelAdmin):
    list_display = ("nome", "campus", "ativo")
    search_fields = ("nome",)
    list_filter = ("campus", "ativo")


@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "predio", "ativo")
    search_fields = ("codigo", "nome")
    list_filter = ("predio", "ativo")


@admin.register(PeriodoLetivo)
class PeriodoLetivoAdmin(admin.ModelAdmin):
    list_display = ("nome", "data_inicio", "data_fim", "ativo")
    list_filter = ("ativo",)


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ("nome", "campus", "ativo")
    search_fields = ("nome",)
    list_filter = ("campus", "ativo")


@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "curso", "ativo")
    search_fields = ("codigo", "nome")
    list_filter = ("curso", "ativo")


@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "disciplina", "periodo_letivo", "ativo")
    search_fields = ("codigo", "disciplina__nome", "disciplina__codigo")
    list_filter = ("periodo_letivo", "disciplina", "ativo")
    filter_horizontal = ("professores",)


@admin.register(MatriculaTurma)
class MatriculaTurmaAdmin(admin.ModelAdmin):
    list_display = ("turma", "aluno", "ativo", "criado_em")
    search_fields = ("turma__disciplina__nome", "aluno__username", "aluno__matricula")
    list_filter = ("turma", "ativo")


@admin.register(HorarioPadraoUFMA)
class HorarioPadraoUFMAAdmin(admin.ModelAdmin):
    list_display = ("codigo", "dia_semana", "horario_inicio", "horario_fim", "ativo")
    search_fields = ("codigo",)
    list_filter = ("dia_semana", "ativo")


@admin.register(HorarioAula)
class HorarioAulaAdmin(admin.ModelAdmin):
    list_display = (
        "turma",
        "sala",
        "horario_padrao",
        "ativo",
    )
    list_filter = ("horario_padrao", "sala", "ativo")


@admin.register(NoBorda)
class NoBordaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "ativo", "ultimo_sync_em", "interscity_uuid")
    search_fields = ("codigo", "nome", "interscity_uuid")
    list_filter = ("ativo",)


@admin.register(TokenNoBorda)
class TokenNoBordaAdmin(admin.ModelAdmin):
    list_display = ("no", "nome", "prefixo_token", "ativo", "expira_em", "ultimo_uso_em")
    list_filter = ("ativo", "no")
    readonly_fields = ("hash_token", "prefixo_token")


@admin.register(DispositivoEsp32)
class DispositivoEsp32Admin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "no", "sala", "status", "status_atualizado_em", "ativo", "interscity_uuid")
    search_fields = ("codigo", "nome", "interscity_uuid")
    list_filter = ("no", "sala", "status", "ativo")


@admin.register(Aula)
class AulaAdmin(admin.ModelAdmin):
    list_display = ("horario", "data", "inicio", "fim", "status", "fechada_por")
    list_filter = ("status", "data")


@admin.register(RegistroPresenca)
class RegistroPresencaAdmin(admin.ModelAdmin):
    list_display = ("aula", "aluno", "status", "registrado_em", "registrado_por_dispositivo")
    search_fields = ("aluno__username", "aluno__matricula")
    list_filter = ("status", "aula")


@admin.register(EventoReconhecimento)
class EventoReconhecimentoAdmin(admin.ModelAdmin):
    list_display = ("dispositivo", "aula", "aluno_candidato", "confianca", "reconhecido", "ocorrido_em")
    list_filter = ("reconhecido", "dispositivo")


@admin.register(PerfilBiometrico)
class PerfilBiometricoAdmin(admin.ModelAdmin):
    list_display = ("aluno", "status")
    search_fields = ("aluno__username", "aluno__matricula")
    list_filter = ("status",)


@admin.register(EmbeddingFacial)
class EmbeddingFacialAdmin(admin.ModelAdmin):
    list_display = ("perfil", "versao_modelo", "status", "ativo")
    list_filter = ("status", "ativo", "versao_modelo")
