from .academico import Campus, Curso, Disciplina, HorarioAula, MatriculaTurma, PeriodoLetivo, Predio, Sala, Turma
from .base import BaseModel
from .biometria import EmbeddingFacial, PerfilBiometrico
from .dispositivos import ComandoBorda, DispositivoEsp32, NoBorda, TokenNoBorda
from .identidade import PapelUsuario, Usuario
from .presencas import Aula, EventoReconhecimento, RegistroPresenca

__all__ = [
    "Aula",
    "BaseModel",
    "Campus",
    "ComandoBorda",
    "Curso",
    "Disciplina",
    "DispositivoEsp32",
    "EmbeddingFacial",
    "EventoReconhecimento",
    "HorarioAula",
    "MatriculaTurma",
    "NoBorda",
    "PapelUsuario",
    "PerfilBiometrico",
    "PeriodoLetivo",
    "Predio",
    "RegistroPresenca",
    "Sala",
    "TokenNoBorda",
    "Turma",
    "Usuario",
]
