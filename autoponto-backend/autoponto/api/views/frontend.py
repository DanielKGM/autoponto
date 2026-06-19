from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import PapelUsuario, Turma, Usuario
from api.serializers.frontend import MatriculaBiometricaPropriaSerializer
from api.services.biometria import matricular_biometria_aluno
from api.services.errors import AppError
from api.services.relatorios import (
    historico_presencas_aluno,
    payload_turma,
    presencas_do_aluno,
    relatorio_presencas_turma_data,
    relatorio_resumo_turma,
    turmas_do_aluno,
    turmas_do_professor,
    usuario_pode_acessar_turma,
)


def _payload_usuario(usuario: Usuario) -> dict:
    return {
        "id": str(usuario.id),
        "username": usuario.username,
        "email": usuario.email,
        "nome_completo": usuario.nome_completo,
        "matricula": usuario.matricula,
        "papel": usuario.papel,
    }


def _payload_permissoes(usuario: Usuario) -> dict:
    areas_por_papel = {
        PapelUsuario.ALUNO: ["aluno"],
        PapelUsuario.PROFESSOR: ["professor"],
        PapelUsuario.ADMINISTRADOR: ["admin", "professor", "aluno"],
    }
    return {
        "areas": areas_por_papel.get(usuario.papel, []),
        "pode_administrar": usuario.papel == PapelUsuario.ADMINISTRADOR,
        "pode_emitir_relatorios": usuario.papel in {PapelUsuario.PROFESSOR, PapelUsuario.ADMINISTRADOR},
        "pode_cadastrar_biometria_propria": usuario.papel == PapelUsuario.ALUNO,
    }


def _resposta_erro_app(erro: AppError) -> Response:
    corpo = {"detail": erro.message, "code": erro.code}
    corpo.update(erro.extra)
    return Response(corpo, status=erro.status_code)


def _exigir_professor_ou_admin(usuario: Usuario) -> None:
    if usuario.papel not in {PapelUsuario.PROFESSOR, PapelUsuario.ADMINISTRADOR}:
        raise PermissionDenied("Apenas professores e administradores podem acessar este relatorio.")


def _obter_turma_relatorio(usuario: Usuario, turma_id) -> Turma:
    _exigir_professor_ou_admin(usuario)
    turma = get_object_or_404(
        Turma.objects.select_related("disciplina", "disciplina__curso", "periodo_letivo").prefetch_related(
            "professores",
        ),
        pk=turma_id,
    )
    if not usuario_pode_acessar_turma(usuario, turma):
        raise PermissionDenied("Voce nao tem acesso a esta turma.")
    return turma


def _parse_data_obrigatoria(valor: str | None, nome: str = "data"):
    data = parse_date(valor or "")
    if not data:
        raise ValidationError({nome: "Informe uma data valida no formato YYYY-MM-DD."})
    return data


def _usuario_pode_historico_aluno(usuario: Usuario, aluno: Usuario, turma_id=None) -> bool:
    if usuario.papel == PapelUsuario.ADMINISTRADOR:
        return True
    if usuario.papel == PapelUsuario.ALUNO:
        return usuario.id == aluno.id
    if usuario.papel != PapelUsuario.PROFESSOR:
        return False

    turmas = Turma.objects.filter(professores=usuario, matriculas__aluno=aluno, matriculas__ativo=True)
    if turma_id:
        turmas = turmas.filter(id=turma_id)
    return turmas.exists()


def _turmas_historico_permitidas(usuario: Usuario, aluno: Usuario, turma_id=None):
    if usuario.papel in {PapelUsuario.ADMINISTRADOR, PapelUsuario.ALUNO}:
        return None
    turmas = Turma.objects.filter(professores=usuario, matriculas__aluno=aluno, matriculas__ativo=True)
    if turma_id:
        turmas = turmas.filter(id=turma_id)
    return list(turmas.values_list("id", flat=True))


class MeView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        return Response(
            {
                "usuario": _payload_usuario(request.user),
                "permissoes": _payload_permissoes(request.user),
            }
        )


class MinhasTurmasView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        if request.user.papel != PapelUsuario.ALUNO:
            raise PermissionDenied("Apenas alunos podem consultar suas turmas por este endpoint.")
        return Response(turmas_do_aluno(request.user))


class MinhasPresencasView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        if request.user.papel != PapelUsuario.ALUNO:
            raise PermissionDenied("Apenas alunos podem consultar suas presencas por este endpoint.")
        return Response(presencas_do_aluno(request.user))


class MinhaBiometriaView(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_scope = "biometria"

    @extend_schema(request=MatriculaBiometricaPropriaSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        if request.user.papel != PapelUsuario.ALUNO:
            raise PermissionDenied("Apenas alunos podem cadastrar a propria biometria por este endpoint.")

        serializer = MatriculaBiometricaPropriaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            perfil, embedding = matricular_biometria_aluno(
                aluno=request.user,
                capturas=serializer.validated_data["capturas"],
                versao_modelo=serializer.validated_data.get("versao_modelo", "sface"),
            )
        except AppError as erro:
            return _resposta_erro_app(erro)

        return Response(
            {
                "perfil_id": str(perfil.id),
                "embedding_id": str(embedding.id),
                "status": perfil.status,
            },
            status=status.HTTP_201_CREATED,
        )


class ProfessorTurmasView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        _exigir_professor_ou_admin(request.user)
        if request.user.papel == PapelUsuario.ADMINISTRADOR:
            turmas = Turma.objects.select_related("disciplina", "disciplina__curso", "periodo_letivo").prefetch_related(
                "professores",
            ).filter(ativo=True)
            return Response([payload_turma(turma) for turma in turmas])
        return Response(turmas_do_professor(request.user))


class RelatorioPresencasTurmaDataView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, turma_id):
        turma = _obter_turma_relatorio(request.user, turma_id)
        data = _parse_data_obrigatoria(request.query_params.get("data"))
        return Response(relatorio_presencas_turma_data(turma, data))


class RelatorioResumoTurmaView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, turma_id):
        turma = _obter_turma_relatorio(request.user, turma_id)
        inicio = parse_date(request.query_params.get("inicio") or "") or None
        fim = parse_date(request.query_params.get("fim") or "") or None
        if inicio and fim and fim < inicio:
            raise ValidationError({"fim": "A data final deve ser maior ou igual a inicial."})
        return Response(relatorio_resumo_turma(turma, inicio=inicio, fim=fim))


class RelatorioPresencasAlunoView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, aluno_id):
        aluno = get_object_or_404(Usuario, pk=aluno_id, papel=PapelUsuario.ALUNO)
        turma_id = request.query_params.get("turma") or None
        periodo_letivo_id = request.query_params.get("periodo_letivo") or None

        if not _usuario_pode_historico_aluno(request.user, aluno, turma_id=turma_id):
            raise PermissionDenied("Voce nao tem acesso ao historico deste aluno.")

        turma_ids_permitidas = _turmas_historico_permitidas(request.user, aluno, turma_id=turma_id)
        payload = historico_presencas_aluno(
            aluno,
            turma_id=turma_id,
            periodo_letivo_id=periodo_letivo_id,
            turma_ids_permitidas=turma_ids_permitidas,
        )
        payload["gerado_em"] = timezone.now().isoformat()
        return Response(payload)
