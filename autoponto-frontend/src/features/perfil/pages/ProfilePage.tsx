import { useEffect, useState } from "react";
import { apiFetch, detalheErro } from "../../../shared/api";
import { useSession } from "../../../shared/session";
import { ConfirmModal } from "../../../shared/ui/ConfirmModal";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { IconButton } from "../../../shared/ui/IconButton";
import { PageMeta } from "../../../shared/ui/PageMeta";
import { ProgressBar } from "../../../shared/ui/ProgressBar";
import {
  SimpleTable,
  type SimpleTableColumn,
} from "../../../shared/ui/SimpleTable";
import type {
  BiometriaAluno,
  BiometriasAlunoResponse,
  EventoReconhecimentoAluno,
  EventosReconhecimentoAlunoResponse,
  FrequenciaTurmaAluno,
  ResumoFrequenciaAlunoResponse,
} from "../../../shared/types";
import {
  formatDateTime,
  percentText,
} from "../../../shared/domain/academicUtils";
import { TrashIcon } from "../../../shared/ui/icons";

const frequencyColumns: SimpleTableColumn<FrequenciaTurmaAluno>[] = [
  {
    key: "disciplina",
    label: "Turma/Disciplina",
    render: (row) => (
      <div>
        <span className="cell-strong">{row.disciplina}</span>
        <div className="lesson-table-subtext">
          {row.codigo} · {row.periodo_letivo}
        </div>
      </div>
    ),
  },
  { key: "total_aulas_fechadas", label: "Aulas fechadas", align: "center" },
  { key: "presencas", label: "Presenças", align: "center" },
  { key: "faltas", label: "Faltas", align: "center" },
  {
    key: "percentual",
    label: "Percentual",
    align: "center",
    render: (row) => (
      <div className="table-progress-cell">
        <span>{percentText(row.percentual)}</span>
        <ProgressBar
          value={row.percentual}
          tone={row.percentual >= 75 ? "green" : "yellow"}
        />
      </div>
    ),
  },
  {
    key: "ultimo_sync_no_borda",
    label: "Última sincronização",
    align: "center",
    render: (row) => (
      <div>
        <span>{formatDateTime(row.ultimo_sync_no_borda)}</span>
        <div className="lesson-table-subtext">
          {row.no_borda_codigo || "Sem nó vinculado"}
        </div>
      </div>
    ),
  },
];

function biometricStatusClass(status: BiometriaAluno["status"]) {
  if (status === "ATIVO") return "status status-green";
  if (status === "REVOGADO") return "status status-muted";
  return "status status-yellow";
}

function biometricStatusLabel(status: BiometriaAluno["status"]) {
  const labels = {
    ATIVO: "Ativa",
    INATIVO: "Inativa",
    REVOGADO: "Revogada",
  };
  return labels[status] || status;
}

function initials(name: string) {
  return (
    name
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join("") || "AP"
  );
}

export function ProfilePage() {
  const { me } = useSession();
  const [frequency, setFrequency] =
    useState<ResumoFrequenciaAlunoResponse | null>(null);
  const [biometrics, setBiometrics] = useState<BiometriaAluno[]>([]);
  const [recognitionEvents, setRecognitionEvents] = useState<
    EventoReconhecimentoAluno[]
  >([]);
  const [periodoId, setPeriodoId] = useState("");
  const [loading, setLoading] = useState(false);
  const [biometricsLoading, setBiometricsLoading] = useState(false);
  const [deletingBiometric, setDeletingBiometric] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<BiometriaAluno | null>(null);
  const [error, setError] = useState("");
  const [biometricsError, setBiometricsError] = useState("");
  const isAluno = me.usuario.papel === "ALUNO";
  const nome = me.usuario.nome_completo || me.usuario.username;
  const detailFields = [
    ["Nome", nome],
    ["Email", me.usuario.email || "Sem email cadastrado"],
    ["Perfil", me.usuario.papel],
    ["Usuário", me.usuario.username],
    ["Matrícula", me.usuario.matricula || "-"],
    ["ID da conta", me.usuario.id],
  ];

  useEffect(() => {
    if (!isAluno) return;
    let active = true;
    const query = periodoId ? `?periodo_letivo=${periodoId}` : "";
    setLoading(true);
    setError("");
    apiFetch<ResumoFrequenciaAlunoResponse>(`/me/frequencia/${query}`)
      .then((response) => {
        if (!active) return;
        setFrequency(response);
        if (!periodoId && response.periodo_letivo_id) {
          setPeriodoId(response.periodo_letivo_id);
        }
      })
      .catch((err) => {
        if (active) setError(detalheErro(err));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [isAluno, periodoId]);

  function loadBiometricInfo() {
    if (!isAluno) return;
    setBiometricsLoading(true);
    setBiometricsError("");
    Promise.all([
      apiFetch<BiometriasAlunoResponse>("/me/biometrias/"),
      apiFetch<EventosReconhecimentoAlunoResponse>(
        "/me/eventos-reconhecimento/?limite=8",
      ),
    ])
      .then(([biometricResponse, eventResponse]) => {
        setBiometrics(biometricResponse.biometrias);
        setRecognitionEvents(eventResponse.eventos);
      })
      .catch((err) => setBiometricsError(detalheErro(err)))
      .finally(() => setBiometricsLoading(false));
  }

  useEffect(() => {
    loadBiometricInfo();
  }, [isAluno]);

  async function confirmDeleteBiometric() {
    if (!deleteTarget) return;
    setDeletingBiometric(true);
    setBiometricsError("");
    try {
      await apiFetch<void>(`/me/biometrias/${deleteTarget.id}/`, {
        method: "DELETE",
      });
      setDeleteTarget(null);
      loadBiometricInfo();
    } catch (err) {
      setBiometricsError(detalheErro(err));
    } finally {
      setDeletingBiometric(false);
    }
  }

  const biometricColumns: SimpleTableColumn<BiometriaAluno>[] = [
    {
      key: "versao_modelo",
      label: "Modelo",
      render: (row) => (
        <div>
          <span className="cell-strong">{row.versao_modelo}</span>
          <div className="lesson-table-subtext">
            Cadastro em {formatDateTime(row.criado_em)}
          </div>
        </div>
      ),
    },
    {
      key: "status",
      label: "Status",
      align: "center",
      render: (row) => (
        <span className={biometricStatusClass(row.status)}>
          {biometricStatusLabel(row.status)}
        </span>
      ),
    },
    {
      key: "revogado_em",
      label: "Revogação",
      align: "center",
      render: (row) => formatDateTime(row.revogado_em),
    },
    {
      key: "acao",
      label: "Ações",
      align: "center",
      className: "table-action-cell",
      width: "64px",
      render: (row) =>
        row.ativo ? (
          <div className="admin-row-actions">
            <IconButton
              label="Revogar biometria"
              icon={<TrashIcon />}
              variant="danger"
              onClick={() => setDeleteTarget(row)}
            />
          </div>
        ) : (
          "-"
        ),
    },
  ];

  const recognitionColumns: SimpleTableColumn<EventoReconhecimentoAluno>[] = [
    {
      key: "disciplina",
      label: "Evento",
      render: (row) => (
        <div>
          <span className="cell-strong">
            {row.disciplina || "Aula não vinculada"}
          </span>
          <div className="lesson-table-subtext">
            {row.turma || "-"} · {row.dispositivo}
          </div>
        </div>
      ),
    },
    {
      key: "confianca",
      label: "Score",
      align: "center",
      render: (row) => `${Math.round(row.confianca * 100)}%`,
    },
    {
      key: "reconhecido",
      label: "Resultado",
      align: "center",
      render: (row) => (
        <span
          className={
            row.reconhecido ? "status status-green" : "status status-red"
          }
        >
          {row.reconhecido ? "Reconhecido" : "Não reconhecido"}
        </span>
      ),
    },
    {
      key: "embedding_status",
      label: "Biometria",
      align: "center",
      render: (row) => row.embedding_status || "Removida",
    },
    {
      key: "ocorrido_em",
      label: "Data",
      align: "center",
      render: (row) => formatDateTime(row.ocorrido_em),
    },
  ];

  return (
    <>
      <PageMeta
        title="Perfil | AutoPonto"
        description="Perfil do usuário autenticado."
      />
      <div className="page-header">
        <div className="page-pretitle">Conta</div>
        <h1 className="page-title">Informações Pessoais</h1>
      </div>

      <section className="card">
        <div className="card-body profile-overview">
          <div className="profile-main">
            <div
              className="profile-avatar profile-avatar-lg"
              aria-hidden="true"
            >
              {initials(nome)}
            </div>
            <div className="profile-main-copy">
              <span className="chip chip-blue">{me.usuario.papel}</span>
              <strong>{nome}</strong>
              <span>{me.usuario.email || "Sem email cadastrado"}</span>
            </div>
          </div>

          <hr className="divider-plain profile-divider" />

          <div className="profile-grid profile-secondary-grid">
            {detailFields.map(([label, value]) => (
              <div key={label} className="profile-field">
                <span className="profile-label">{label}</span>
                <strong className="profile-value">{value}</strong>
              </div>
            ))}
          </div>
        </div>
      </section>

      {isAluno && (
        <section className="card">
          <div className="card-header profile-frequency-header">
            <div>
              <div className="card-title">Frequência detalhada</div>
            </div>
            <select
              className="form-control profile-period-select"
              value={periodoId}
              onChange={(event) => setPeriodoId(event.target.value)}
              aria-label="Período letivo"
              disabled={!frequency?.periodos.length}
            >
              {frequency?.periodos.length ? (
                frequency.periodos.map((periodo) => (
                  <option value={periodo.id} key={periodo.id}>
                    {periodo.nome}
                  </option>
                ))
              ) : (
                <option value="">Sem períodos</option>
              )}
            </select>
          </div>
          <div className="card-body">
            {loading && (
              <div className="alert alert-info">Carregando frequência...</div>
            )}
            {error && <div className="alert alert-error">{error}</div>}
            {frequency && (
              <>
                <div className="profile-frequency-summary">
                  <div>
                    <span>Aulas fechadas</span>
                    <strong>{frequency.resumo.total_aulas_fechadas}</strong>
                  </div>
                  <div>
                    <span>Presenças</span>
                    <strong>{frequency.resumo.presencas}</strong>
                  </div>
                  <div>
                    <span>Faltas</span>
                    <strong>{frequency.resumo.faltas}</strong>
                  </div>
                  <div>
                    <span>Percentual</span>
                    <strong>{percentText(frequency.resumo.percentual)}</strong>
                  </div>
                </div>
                <SimpleTable
                  columns={frequencyColumns}
                  rows={frequency.turmas}
                  rowKey={(row) => row.turma_id}
                  emptyState={
                    <EmptyState
                      title="Sem frequência"
                      text="Nenhuma aula fechada foi encontrada para este período."
                    />
                  }
                />
              </>
            )}
          </div>
        </section>
      )}

      {isAluno && (
        <>
          <section className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Biometrias cadastradas</div>
                <div className="card-subtitle">
                  Metadados do cadastro biométrico. As imagens enviadas não
                  ficam armazenadas.
                </div>
              </div>
            </div>
            <div className="card-body">
              {biometricsLoading && (
                <div className="alert alert-info">Carregando biometrias...</div>
              )}
              {biometricsError && (
                <div className="alert alert-error">{biometricsError}</div>
              )}
              <SimpleTable
                columns={biometricColumns}
                rows={biometrics}
                rowKey={(row) => row.id}
                emptyState={
                  <EmptyState
                    title="Sem biometria cadastrada"
                    text="Cadastre sua biometria para usar reconhecimento nas chamadas."
                  />
                }
              />
            </div>
          </section>

          <section className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Eventos de reconhecimento</div>
                <div className="card-subtitle">
                  Histórico recente de reconhecimentos associados à sua conta.
                </div>
              </div>
            </div>
            <div className="card-body">
              <SimpleTable
                columns={recognitionColumns}
                rows={recognitionEvents}
                rowKey={(row) => row.id}
                emptyState={
                  <EmptyState
                    title="Sem eventos"
                    text="Os eventos aparecerão após reconhecimentos enviados pelos dispositivos."
                  />
                }
              />
            </div>
          </section>
        </>
      )}

      <ConfirmModal
        open={deleteTarget !== null}
        title="Revogar biometria"
        confirmLabel="Revogar"
        variant="danger"
        loading={deletingBiometric}
        onCancel={() => setDeleteTarget(null)}
        onConfirm={() => void confirmDeleteBiometric()}
      >
        <p className="modal-confirm-text">
          O vetor biométrico será removido e esta biometria deixará de ser usada
          no reconhecimento.
        </p>
      </ConfirmModal>
    </>
  );
}
