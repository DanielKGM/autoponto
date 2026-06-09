from datetime import date, time

from api.models import (
    Campus,
    Curso,
    Disciplina,
    DispositivoEsp32,
    HorarioAula,
    MatriculaTurma,
    PapelUsuario,
    PeriodoLetivo,
    Predio,
    Sala,
    Turma,
    Usuario,
)


def criar_contexto_academico():
    campus = Campus.objects.create(nome="Campus Dom Delgado", codigo="SLZ")
    predio = Predio.objects.create(campus=campus, nome="Centro de Ciencias Exatas e Tecnologia", codigo="CCET")
    sala = Sala.objects.create(predio=predio, nome="Laboratorio 101", codigo="LAB101")
    periodo = PeriodoLetivo.objects.create(
        nome="2026.1",
        data_inicio=date(2026, 1, 1),
        data_fim=date(2026, 12, 31),
        ativo=True,
    )
    curso = Curso.objects.create(
        campus=campus,
        codigo="ECP-UFMA",
        nome="Engenharia da Computacao",
    )
    disciplina = Disciplina.objects.create(
        curso=curso,
        codigo="EECP0036",
        nome="Desenvolvimento de Sistemas Web",
    )
    professor = Usuario.objects.create_user(
        username="professor",
        password="password123",
        email="professor@example.com",
        papel=PapelUsuario.PROFESSOR,
        nome_completo="Professor Usuario",
    )
    aluno = Usuario.objects.create_user(
        username="aluno",
        password="password123",
        email="aluno@example.com",
        papel=PapelUsuario.ALUNO,
        nome_completo="Aluno Usuario",
        matricula="20260001",
    )
    admin = Usuario.objects.create_user(
        username="admin",
        password="password123",
        email="admin@example.com",
        papel=PapelUsuario.ADMINISTRADOR,
        nome_completo="Administrador",
        is_staff=True,
        is_superuser=True,
    )
    turma = Turma.objects.create(periodo_letivo=periodo, disciplina=disciplina, codigo="A")
    turma.professores.add(professor)
    matricula = MatriculaTurma.objects.create(turma=turma, aluno=aluno)
    horario = HorarioAula.objects.create(
        turma=turma,
        sala=sala,
        dia_semana=0,
        horario_inicio=time(8, 0),
        horario_fim=time(9, 40),
    )
    dispositivo = DispositivoEsp32.objects.create(
        codigo="ESP32-LAB101",
        nome="ESP32 Laboratorio 101",
        sala=sala,
    )
    data_aula = date(2026, 4, 20)
    return {
        "campus": campus,
        "predio": predio,
        "sala": sala,
        "periodo": periodo,
        "curso": curso,
        "disciplina": disciplina,
        "professor": professor,
        "aluno": aluno,
        "admin": admin,
        "turma": turma,
        "matricula": matricula,
        "horario": horario,
        "dispositivo": dispositivo,
        "data_aula": data_aula,
    }
