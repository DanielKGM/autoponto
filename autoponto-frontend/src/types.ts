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

export type TurmaCrud = {
  id: string;
  codigo: string;
  disciplina: string;
  periodo_letivo: string;
  professores: string[];
  ativo: boolean;
};

export type DispositivoStatus = {
  id: string;
  codigo: string;
  nome: string;
  ativo: boolean;
  status: "offline" | "working" | "idle";
  status_efetivo: "offline" | "working" | "idle";
  status_atualizado_em: string | null;
  sala: string | null;
  no: string | null;
  interscity_uuid: string;
  origem_status: "local" | "collector";
  interscity_status?: string;
};
