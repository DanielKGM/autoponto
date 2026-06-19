export type PapelUsuario = "ALUNO" | "PROFESSOR" | "ADMINISTRADOR";

export type UsuarioAtual = {
  id: string;
  username: string;
  email: string;
  nome_completo: string;
  matricula: string;
  papel: PapelUsuario;
};

export type MeResponse = {
  usuario: UsuarioAtual;
  permissoes: {
    areas: string[];
    pode_administrar: boolean;
    pode_emitir_relatorios: boolean;
    pode_cadastrar_biometria_propria: boolean;
  };
};

export type TurmaResumo = {
  turma_id: string;
  codigo: string;
  nome: string;
  disciplina_id: string;
  disciplina: string;
  periodo_letivo_id: string;
  periodo_letivo: string;
  curso: string;
  professores: Array<{ id: string; nome: string }>;
};

export type PresencaAluno = {
  presenca_id: string;
  aula_id: string;
  turma_id: string;
  disciplina: string;
  turma: string;
  periodo_letivo: string;
  data: string;
  inicio: string;
  fim: string;
  sala: string;
  status: string;
  registrado_em: string;
  origem: string | null;
};

export type RelatorioTurmaData = TurmaResumo & {
  data: string;
  aulas: Array<{
    aula_id: string;
    inicio: string;
    fim: string;
    status: string;
    fechada_em: string | null;
    fechada_por: string | null;
    sala: string;
  }>;
  totais: { presentes: number; ausentes: number; matriculados: number };
  alunos: Array<{ aluno_id: string; nome: string; matricula: string; status: string; registrado_em: string | null }>;
};

export type RelatorioResumoTurma = TurmaResumo & {
  inicio: string;
  fim: string;
  total_aulas: number;
  alunos: Array<{
    aluno_id: string;
    nome: string;
    matricula: string;
    presencas: number;
    faltas: number;
    percentual_presenca: number;
  }>;
};

export type UsuarioCrud = UsuarioAtual & {
  is_active: boolean;
};

export type CampusCrud = { id: string; nome: string; ativo: boolean };
export type PredioCrud = { id: string; campus: string; nome: string; ativo: boolean };
export type SalaCrud = { id: string; predio: string; nome: string; codigo: string; ativo: boolean };
export type PeriodoLetivoCrud = { id: string; nome: string; data_inicio: string; data_fim: string; ativo: boolean };
export type CursoCrud = { id: string; campus: string; nome: string; ativo: boolean };
export type DisciplinaCrud = { id: string; curso: string; codigo: string; nome: string; ativo: boolean };
export type TurmaCrud = { id: string; codigo: string; disciplina: string; periodo_letivo: string; professores: string[]; ativo: boolean };
export type MatriculaTurmaCrud = { id: string; turma: string; aluno: string; ativo: boolean };
export type HorarioPadraoUFMACrud = {
  id: string;
  codigo: string;
  dia_semana: number;
  horario_inicio: string;
  horario_fim: string;
  ativo: boolean;
};
export type HorarioAulaCrud = { id: string; turma: string; sala: string; horario_padrao: string; ativo: boolean };
export type NoBordaCrud = { id: string; codigo: string; nome: string; ativo: boolean };
export type DispositivoEsp32Crud = {
  id: string;
  no: string | null;
  sala: string | null;
  codigo: string;
  nome: string;
  ativo: boolean;
  sala_nome?: string | null;
  no_codigo?: string | null;
  interscity_uuid: string;
  latitude: string | null;
  longitude: string | null;
};

export type DispositivoStatus = {
  id: string;
  codigo: string;
  nome: string;
  sala: string | null;
  predio: string | null;
  latitude: string | null;
  longitude: string | null;
  interscity_uuid: string;
};

export type DiagnosticoInterSCity = Record<string, { ok: boolean; status: string; codigo_http?: number; detalhe?: string }>;
