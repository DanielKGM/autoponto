from .academico import (
    Campus,
    Curso,
    Disciplina,
    HorarioPadraoUFMA,
    MatriculaTurma,
    PeriodoLetivo,
    Predio,
    Sala,
    Turma,
)
from .base import BaseModel
from .biometria import EmbeddingFacial
from .dispositivos import DispositivoEsp32, NoBorda, TokenNoBorda
from .identidade import PapelUsuario, Usuario
from .presencas import Aula, EventoReconhecimento, RegistroPresenca

__all__ = [
    "Aula",
    "BaseModel",
    "Campus",
    "Curso",
    "Disciplina",
    "DispositivoEsp32",
    "EmbeddingFacial",
    "EventoReconhecimento",
    "HorarioPadraoUFMA",
    "MatriculaTurma",
    "NoBorda",
    "PapelUsuario",
    "PeriodoLetivo",
    "Predio",
    "RegistroPresenca",
    "Sala",
    "TokenNoBorda",
    "Turma",
    "Usuario",
]
