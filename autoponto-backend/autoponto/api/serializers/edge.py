from rest_framework import serializers

from api.models import (
    Aula,
    DispositivoEsp32,
    EmbeddingFacial,
    MatriculaTurma,
    Sala,
    Usuario,
)


class EdgeSalaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sala
        fields = ("id", "nome")


class EdgeDispositivoSerializer(serializers.ModelSerializer):
    sala_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = DispositivoEsp32
        fields = ("id", "codigo", "sala_id", "ativo", "interscity_uuid")


class EdgeAulaSerializer(serializers.ModelSerializer):
    nome = serializers.SerializerMethodField()
    turma_id = serializers.UUIDField(read_only=True)
    sala_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Aula
        fields = ("id", "nome", "turma_id", "sala_id", "inicio", "fim", "status")

    def get_nome(self, aula: Aula) -> str:
        return f"{aula.turma.disciplina.nome} - {aula.turma.codigo}"


class EdgeAlunoSerializer(serializers.ModelSerializer):
    nome = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ("id", "matricula", "nome")

    def get_nome(self, aluno: Usuario) -> str:
        return aluno.nome_completo or aluno.username


class EdgeMatriculaTurmaSerializer(serializers.ModelSerializer):
    turma_id = serializers.UUIDField(read_only=True)
    aluno_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = MatriculaTurma
        fields = ("id", "turma_id", "aluno_id")


class EdgeEmbeddingFacialSerializer(serializers.ModelSerializer):
    aluno_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = EmbeddingFacial
        fields = ("id", "aluno_id", "vetor")


EDGE_SERIALIZERS = {
    "salas": EdgeSalaSerializer,
    "dispositivos": EdgeDispositivoSerializer,
    "aulas": EdgeAulaSerializer,
    "alunos": EdgeAlunoSerializer,
    "matriculas_turma": EdgeMatriculaTurmaSerializer,
    "embeddings_faciais": EdgeEmbeddingFacialSerializer,
}
EDGE_ENTIDADES = tuple(EDGE_SERIALIZERS)
