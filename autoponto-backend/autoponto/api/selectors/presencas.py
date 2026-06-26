from api.models import Aula, PapelUsuario
from api.selectors.aulas import com_status_aula


def obter_aulas_acessiveis(usuario):
    queryset = Aula.objects.select_related(
        "turma",
        "turma__disciplina",
        "sala",
        "horario_padrao",
    )
    if usuario.papel == PapelUsuario.ADMINISTRADOR:
        return com_status_aula(queryset)
    if usuario.papel == PapelUsuario.PROFESSOR:
        return com_status_aula(queryset.filter(turma__professores=usuario))
    return com_status_aula(queryset.none())
