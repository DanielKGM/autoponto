from api.models import Aula, PapelUsuario


def obter_aulas_acessiveis(usuario):
    queryset = Aula.objects.select_related(
        "turma",
        "turma__disciplina",
        "sala",
        "horario_padrao",
    )
    if usuario.papel == PapelUsuario.ADMINISTRADOR:
        return queryset
    if usuario.papel == PapelUsuario.PROFESSOR:
        return queryset.filter(turma__professores=usuario)
    return queryset.none()
