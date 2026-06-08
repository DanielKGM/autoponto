from api.models import Aula, PapelUsuario


def obter_aulas_acessiveis(usuario):
    queryset = Aula.objects.select_related(
        "horario",
        "horario__turma",
        "horario__turma__disciplina",
        "horario__sala",
    )
    if usuario.papel == PapelUsuario.ADMINISTRADOR:
        return queryset
    if usuario.papel == PapelUsuario.PROFESSOR:
        return queryset.filter(horario__turma__professores=usuario)
    return queryset.none()


get_accessible_sessions = obter_aulas_acessiveis
