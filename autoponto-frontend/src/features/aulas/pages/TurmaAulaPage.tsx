import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import { apiFetch, detalheErro } from "../../../shared/api";
import { useSession } from "../../../shared/session";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { IconButton } from "../../../shared/ui/IconButton";
import { PageMeta } from "../../../shared/ui/PageMeta";
import {
  SimpleTable,
  type SimpleTableColumn,
} from "../../../shared/ui/SimpleTable";
import { StatCard } from "../../../shared/ui/StatCard";
import {
  ClockIcon,
  RefreshIcon,
  UserCheckIcon,
  UsersIcon,
  UserXIcon,
} from "../../../shared/ui/icons";
import type { TurmaAulaDetalheResponse } from "../../../shared/types";
import {
  formatDate,
  formatDateTime,
  statusAlunoClass,
  statusAlunoLabel,
  statusAulaClass,
  statusAulaLabel,
} from "../../../shared/domain/academicUtils";
import {
  formatTimeRange,
  lessonDetailPath,
} from "../../../shared/domain/studentCalendarUtils";

type AlunoChamada = TurmaAulaDetalheResponse["alunos"][number];
type EventoReconhecimento =
  TurmaAulaDetalheResponse["eventos_reconhecimento"][number];

const alunoColumns: SimpleTableColumn<AlunoChamada>[] = [
  {
    key: "nome",
    label: "Aluno",
    render: (row) => (
      <div>
        <span className="cell-strong">{row.nome}</span>
        <div className="lesson-table-subtext">
          {row.matricula || "Sem matrícula"}
        </div>
      </div>
    ),
  },
  {
    key: "status",
    label: "Presença",
    align: "center",
    render: (row) => (
      <span className={statusAlunoClass(row.status)}>
        {statusAlunoLabel(row.status)}
      </span>
    ),
  },
  {
    key: "registrado_em",
    label: "Registro",
    align: "center",
    render: (row) => formatDateTime(row.registrado_em),
  },
];

const eventoColumns: SimpleTableColumn<EventoReconhecimento>[] = [
  { key: "dispositivo", label: "Dispositivo" },
  {
    key: "aluno",
    label: "Candidato",
    render: (row) => row.aluno || "-",
  },
  {
    key: "confianca",
    label: "Confiança",
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
    key: "ocorrido_em",
    label: "Ocorrido",
    align: "center",
    render: (row) => formatDateTime(row.ocorrido_em),
  },
];

export function TurmaAulaPage() {
  const { me } = useSession();
  const { turmaId, aulaId } = useParams();
  const [data, setData] = useState<TurmaAulaDetalheResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    if (!turmaId) return;
    const path = aulaId
      ? `/turmas/${turmaId}/aula/${aulaId}/`
      : `/turmas/${turmaId}/aula/`;
    setLoading(true);
    setError("");
    apiFetch<TurmaAulaDetalheResponse>(path)
      .then(setData)
      .catch((err) => setError(detalheErro(err)))
      .finally(() => setLoading(false));
  }, [aulaId, turmaId]);

  useEffect(() => {
    load();
  }, [load]);

  async function postAction(action: "abrir-chamada" | "fechar-chamada") {
    if (!data?.aula) return;
    setSaving(true);
    setError("");
    try {
      await apiFetch(`/aulas/${data.aula.aula_id}/${action}/`, {
        method: "POST",
      });
      load();
    } catch (err) {
      setError(detalheErro(err));
    } finally {
      setSaving(false);
    }
  }

  const canManage =
    me.usuario.papel === "PROFESSOR" || me.usuario.papel === "ADMINISTRADOR";
  const title = data?.aula
    ? `${data.aula.disciplina} · ${data.aula.turma}`
    : data?.turma.nome || "Turma";

  return (
    <>
      <PageMeta
        title={`${title} | AutoPonto`}
        description="Detalhe da turma e da aula."
      />
      <div className="page-header">
        <div className="page-header-row">
          <div>
            <div className="page-pretitle">Turma/Aula</div>
            <h1 className="page-title">{title}</h1>
            <p className="page-description">
              {data?.turma
                ? `${data.turma.periodo_letivo} · ${data.turma.curso}`
                : "Carregando dados da turma."}
            </p>
          </div>
          <div className="page-actions">
            <IconButton
              label="Atualizar"
              icon={<RefreshIcon />}
              onClick={load}
              disabled={loading || saving}
            />
          </div>
        </div>
      </div>

      {loading && <div className="alert alert-info">Carregando turma...</div>}
      {error && <div className="alert alert-error">{error}</div>}

      {data && (
        <>
          <div className="dashboard-kpi-grid academic-kpi-grid">
            <StatCard
              label="Alunos"
              value={data.turma.total_alunos}
              icon={<UsersIcon />}
              tone="blue"
            />
            <StatCard
              label="Presentes"
              value={data.resumo?.presentes ?? 0}
              icon={<UserCheckIcon />}
              tone="green"
            />
            <StatCard
              label="Ausentes"
              value={data.resumo?.ausentes ?? 0}
              icon={<UserXIcon />}
              tone="red"
            />
            <StatCard
              label="Pendentes"
              value={data.resumo?.pendentes ?? 0}
              icon={<ClockIcon />}
              tone="yellow"
            />
          </div>

          <section className="card">
            <div className="card-header">
              <div>
                <div className="card-title">
                  {data.aula ? "Aula selecionada" : "Dados gerais da turma"}
                </div>
                <div className="card-subtitle">
                  {data.aula
                    ? "Detalhes da chamada selecionada no calendário."
                    : data.instrucao}
                </div>
              </div>
              {data.aula && canManage && (
                <div className="page-actions">
                  {data.aula.pode_abrir_chamada && (
                    <button
                      className="btn btn-primary btn-sm"
                      type="button"
                      onClick={() => void postAction("abrir-chamada")}
                      disabled={saving}
                    >
                      Abrir chamada
                    </button>
                  )}
                  {data.aula.pode_fechar_chamada && (
                    <button
                      className="btn btn-danger btn-sm"
                      type="button"
                      onClick={() => void postAction("fechar-chamada")}
                      disabled={saving}
                    >
                      Fechar chamada
                    </button>
                  )}
                </div>
              )}
            </div>
            <div className="card-body">
              {data.aula?.status_aula === "CANCELADA" && (
                <div className="alert alert-warning">
                  Aula cancelada. A chamada não pode ser aberta nem fechada.
                </div>
              )}
              {data.aula?.status_aula === "PLANEJADA" && (
                <div className="alert alert-info">
                  Aula ainda sem chamada aberta.
                </div>
              )}
              {data.aula?.status_aula === "FECHADA" &&
                data.resumo?.presentes === 0 && (
                  <div className="alert alert-warning">
                    Aula fechada sem presenças registradas.
                  </div>
                )}

              {data.aula ? (
                <div className="lesson-detail-grid">
                  <div className="profile-field">
                    <span className="profile-label">Disciplina</span>
                    <strong className="profile-value">
                      {data.aula.disciplina}
                    </strong>
                  </div>
                  <div className="profile-field">
                    <span className="profile-label">Turma</span>
                    <strong className="profile-value">{data.aula.turma}</strong>
                  </div>
                  <div className="profile-field">
                    <span className="profile-label">Sala</span>
                    <strong className="profile-value">{data.aula.sala}</strong>
                  </div>
                  <div className="profile-field">
                    <span className="profile-label">Data</span>
                    <strong className="profile-value">
                      {formatDate(data.aula.data)}
                    </strong>
                  </div>
                  <div className="profile-field">
                    <span className="profile-label">Horário</span>
                    <strong className="profile-value">
                      {formatTimeRange(data.aula.inicio, data.aula.fim)}
                    </strong>
                  </div>
                  <div className="profile-field">
                    <span className="profile-label">Status</span>
                    <strong className="profile-value">
                      <span className={statusAulaClass(data.aula.status_aula)}>
                        {statusAulaLabel(data.aula.status_aula)}
                      </span>
                    </strong>
                  </div>
                </div>
              ) : (
                <EmptyState title="Selecione uma aula" text={data.instrucao} />
              )}
            </div>
          </section>

          {!data.aula && data.proximas_aulas.length > 0 && (
            <section className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">Próximas aulas</div>
                  <div className="card-subtitle">
                    Atalho para aulas desta turma.
                  </div>
                </div>
              </div>
              <div className="card-body lesson-list">
                {data.proximas_aulas.map((lesson) => (
                  <Link
                    className="lesson-list-item"
                    to={lessonDetailPath(lesson.turma_id, lesson.aula_id)}
                    key={lesson.aula_id}
                  >
                    <div>
                      <strong>{lesson.disciplina}</strong>
                      <span>{lesson.sala}</span>
                    </div>
                    <div className="lesson-list-meta">
                      <span>
                        {formatDate(lesson.data)} ·{" "}
                        {formatTimeRange(lesson.inicio, lesson.fim)}
                      </span>
                      <span className={statusAulaClass(lesson.status_aula)}>
                        {statusAulaLabel(lesson.status_aula)}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          )}

          {data.aula && (
            <section className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">Alunos matriculados</div>
                  <div className="card-subtitle">
                    Status de presença nesta aula.
                  </div>
                </div>
              </div>
              <div className="card-body">
                <SimpleTable
                  columns={alunoColumns}
                  rows={data.alunos}
                  rowKey={(row) => row.aluno_id}
                  emptyState={
                    <EmptyState
                      title="Nenhum aluno"
                      text="Não há alunos ativos nesta turma."
                    />
                  }
                />
              </div>
            </section>
          )}

          {data.aula && canManage && (
            <section className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">Eventos de reconhecimento</div>
                  <div className="card-subtitle">
                    Eventos associados à aula selecionada.
                  </div>
                </div>
              </div>
              <div className="card-body">
                <SimpleTable
                  columns={eventoColumns}
                  rows={data.eventos_reconhecimento}
                  rowKey={(row) => row.id}
                  emptyState={
                    <EmptyState
                      title="Sem eventos"
                      text="Nenhum reconhecimento foi associado a esta aula."
                    />
                  }
                />
              </div>
            </section>
          )}
        </>
      )}
    </>
  );
}
