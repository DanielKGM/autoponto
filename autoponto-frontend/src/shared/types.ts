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

export type AulaStatus = "PLANEJADA" | "ABERTA" | "FECHADA" | "CANCELADA";

export type PresencaStatus = "PRESENTE" | "AUSENTE";

export type StatusAlunoResumo = PresencaStatus | "PENDENTE";

export type StatusAlunoCalendario =
  | "PRESENTE"
  | "AUSENTE"
  | "PENDENTE"
  | "NAO_APLICAVEL";

export type CalendarioVisualizacao = "ALUNO" | "PROFESSOR";

export type AulaCalendario = {
  aula_id: string;
  turma_id: string;
  disciplina: string;
  turma: string;
  periodo_letivo: string;
  data: string;
  inicio: string;
  fim: string;
  sala: string;
  status_aula: AulaStatus;
  status_aluno: StatusAlunoCalendario | null;
  presenca_id: string | null;
  registrado_em: string | null;
};

export type AulaCalendarioAluno = AulaCalendario;

export type CalendarioAulasResponse = {
  visualizacao: CalendarioVisualizacao;
  inicio: string;
  fim: string;
  aulas: AulaCalendario[];
};

export type CalendarioAulasAlunoResponse = CalendarioAulasResponse;

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

export type AulaResumo = {
  aula_id: string;
  turma_id: string;
  disciplina: string;
  turma: string;
  periodo_letivo: string;
  data: string;
  inicio: string;
  fim: string;
  sala: string;
  status_aula: AulaStatus;
  status_aluno: StatusAlunoResumo | "NAO_APLICAVEL" | null;
  presenca_id?: string | null;
  registrado_em?: string | null;
};

export type FrequenciaTurmaAluno = TurmaResumo & {
  ultimo_sync_no_borda: string | null;
  no_borda_codigo: string | null;
  no_borda_nome: string | null;
  total_aulas_fechadas: number;
  presencas: number;
  faltas: number;
  percentual: number;
};

export type ResumoFrequenciaAlunoResponse = {
  aluno_id: string;
  periodo_letivo_id: string | null;
  periodo_letivo: string | null;
  periodos: Array<{ id: string; nome: string; data_inicio: string; data_fim: string; ativo: boolean }>;
  resumo: {
    total_aulas_fechadas: number;
    presencas: number;
    faltas: number;
    percentual: number;
  };
  turmas: FrequenciaTurmaAluno[];
};

export type DashboardAlunoResponse = {
  gerado_em: string;
  biometria_cadastrada: boolean;
  aulas_hoje: AulaResumo[];
  proximas_aulas: AulaResumo[];
  resumo: {
    total_fechadas: number;
    presentes: number;
    ausentes: number;
    pendentes: number;
    percentual: number;
  };
  frequencia_por_turma: FrequenciaTurmaAluno[];
  ultimas_presencas: Array<AulaResumo & { status: StatusAlunoResumo }>;
};

export type BiometriaAluno = {
  id: string;
  versao_modelo: string;
  status: "ATIVO" | "INATIVO" | "REVOGADO";
  ativo: boolean;
  possui_vetor: boolean;
  criado_em: string;
  atualizado_em: string;
  revogado_em: string | null;
};

export type BiometriasAlunoResponse = {
  biometrias: BiometriaAluno[];
};

export type EventoReconhecimentoAluno = {
  id: string;
  aula_id: string | null;
  turma_id: string | null;
  disciplina: string | null;
  turma: string | null;
  data: string | null;
  inicio: string | null;
  fim: string | null;
  sala: string | null;
  dispositivo: string;
  confianca: number;
  reconhecido: boolean;
  ocorrido_em: string;
  embedding_id: string | null;
  embedding_status: string | null;
  embedding_criado_em: string | null;
};

export type EventosReconhecimentoAlunoResponse = {
  eventos: EventoReconhecimentoAluno[];
};

export type PresencaRecenteProfessor = PresencaAluno & {
  aluno_id: string;
  aluno: string;
};

export type DashboardProfessorResponse = {
  gerado_em: string;
  aulas_hoje: AulaResumo[];
  chamadas_abertas: AulaResumo[];
  chamadas_pendentes: AulaResumo[];
  turmas: TurmaResumo[];
  presencas_recentes: PresencaRecenteProfessor[];
  totais: {
    aulas_hoje: number;
    chamadas_abertas: number;
    chamadas_pendentes: number;
    turmas_ministradas: number;
  };
};

export type TurmaAulaDetalheResponse = {
  turma: TurmaResumo & { total_alunos: number };
  aula: (AulaResumo & {
    pode_abrir_chamada: boolean;
    pode_fechar_chamada: boolean;
    fechada_em: string | null;
    fechada_por: string | null;
  }) | null;
  proximas_aulas: AulaResumo[];
  alunos: Array<{
    aluno_id: string;
    nome: string;
    matricula: string;
    status: StatusAlunoResumo;
    registrado_em: string | null;
    presenca_id: string | null;
  }>;
  eventos_reconhecimento: Array<{
    id: string;
    dispositivo: string;
    aluno_id: string | null;
    aluno: string | null;
    confianca: number;
    reconhecido: boolean;
    ocorrido_em: string;
    embedding_id: string | null;
    embedding_status: string | null;
  }>;
  resumo: {
    presentes: number;
    ausentes: number;
    pendentes: number;
    matriculados: number;
  } | null;
  instrucao: string;
};

export type ResumoFrequenciaTurmaResponse = TurmaResumo & {
  resumo: {
    total_aulas_fechadas: number;
    presencas: number;
    faltas: number;
    percentual: number;
  };
  alunos: Array<{
    aluno_id: string;
    nome: string;
    matricula: string;
    total_aulas_fechadas: number;
    presencas: number;
    faltas: number;
    percentual: number;
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
};

export type DispositivoStatus = {
  id: string;
  codigo: string;
  nome: string;
  sala: string | null;
  predio: string | null;
  interscity_uuid: string;
};

export type NoBordaMapa = {
  id: string;
  codigo: string;
  nome: string;
  latitude: string | null;
  longitude: string | null;
  ultimo_sync_em: string | null;
  dispositivos: DispositivoStatus[];
};

export type DispositivoHistorico = {
  dispositivo: DispositivoStatus;
  collector_status: string;
  periodo?: string;
  historico: Record<string, Array<Record<string, unknown>>>;
  pir?: {
    tipo: "histograma";
    balde_minutos?: number;
    eventos: Array<{ timestamp: string; valor: boolean; nivel: number }>;
    baldes: Array<{ inicio: string; fim: string; quantidade: number }>;
    total: number;
  };
  ultimo: Record<string, Record<string, unknown>>;
};

export type DiagnosticoInterSCity = Record<string, { ok: boolean; status: string; codigo_http?: number; detalhe?: string }>;
