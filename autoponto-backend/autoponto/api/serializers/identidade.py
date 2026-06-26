from rest_framework import serializers

from api.models import PapelUsuario, Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    matricula = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Usuario
        fields = (
            "id",
            "username",
            "email",
            "nome_completo",
            "matricula",
            "papel",
            "password",
            "is_active",
        )
        read_only_fields = ("id",)

    def validate(self, attrs):
        papel = attrs.get("papel", self.instance.papel if self.instance else None)
        matricula = attrs.get("matricula", self.instance.matricula if self.instance else "")
        matricula = "" if matricula is None else str(matricula).strip()

        if papel == PapelUsuario.ALUNO and not matricula:
            raise serializers.ValidationError({"matricula": "Informe a matricula do aluno."})
        if "matricula" in attrs or papel == PapelUsuario.PROFESSOR:
            attrs["matricula"] = matricula
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        usuario = Usuario(**validated_data)
        if password:
            usuario.set_password(password)
        else:
            usuario.set_unusable_password()
        usuario.save()
        return usuario

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
