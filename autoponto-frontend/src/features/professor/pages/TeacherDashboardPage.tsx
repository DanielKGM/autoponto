import { useEffect, useState } from "react";
import { Link } from "react-router";
import { apiFetch, detalheErro } from "../../../shared/api";
import { DataTable, type DataTableColumn } from "../../../shared/ui/DataTable";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { PageMeta } from "../../../shared/ui/PageMeta";
import { SimpleTable, type SimpleTableColumn } from "../../../shared/ui/SimpleTable";
import { StatCard } from "../../../shared/ui/StatCard";
import { CalendarIcon, ClockIcon, UnlockIcon, UsersIcon } from "../../../shared/ui/icons";
import type { AulaResumo, DashboardProfessorResponse, PresencaRecenteProfessor, TurmaResumo } from "../../../shared/types";
import {
  formatDate,
  formatDateTime,
  statusAulaClass,
  statusAulaLabel,
  statusAlunoClass,
  statusAlunoLabel,
} from "../../../shared/domain/academicUtils";
import { formatTimeRange, lessonDetailPath, turmaPath } from "../../../shared/domain/studentCalendarUtils";

const lessonColumns: SimpleTableColumn<AulaResumo>[] = [
  {
    key: "disciplina",
    label: "Aula",
    render: (row) => (
      <div>
        <span className="cell-strong">{row.disciplina}</span>
        <div className="lesson-table-subtext">{row.turma} · {row.sala}</div>
      </div>
    ),
  },
  {
    key: "horario",
    label: "Horário",
    align: "center",
    render: (row) => `${formatDate(row.data)} · ${formatTimeRange(row.inicio, row.fim)}`,
  },
  {
    key: "status_aula",
    label: "Status",
    align: "center",
    render: (row) => <span className={statusAulaClass(row.status_aula)}>{statusAulaLabel(row.status_aula)}</span>,
  },
  {
    key: "acao",
    label: "",
    align: "center",
    width: "92px",
    render: (row) => (
      <Link className="btn btn-outline btn-sm" to={lessonDetailPath(row.turma_id, row.aula_id)}>
        Abrir
      </Link>
    ),
  },
];

const turmaColumns: DataTableColumn<TurmaResumo>[] = [
  {
    key: "disciplina",
    label: "Disciplina",
    render: (row) => (
      <div>
        <span className="cell-strong">{row.disciplina}</span>
        <div className="lesson-table-subtext">{row.curso}</div>
      </div>
    ),
  },
  { key: "codigo", label: "Turma", align: "center" },
  { key: "periodo_letivo", label: "Período", align: "center" },
];

const presencaColumns: SimpleTableColumn<PresencaRecenteProfessor>[] = [
  {
    key: "aluno",
    label: "Aluno",
    render: (row) => (
      <div>
        <span className="cell-strong">{row.aluno}</span>
        <div className="lesson-table-subtext">{row.disciplina} · {row.turma}</div>
      </div>
    ),
  },
  {
    key: "status",
    label: "Status",
    align: "center",
    render: (row) => <span className={statusAlunoClass(row.status as "PRESENTE" | "AUSENTE")}>{statusAlunoLabel(row.status as "PRESENTE" | "AUSENTE")}</span>,
  },
  {
    key: "registrado_em",
    label: "Registrado",
    align: "center",
    render: (row) => formatDateTime(row.registrado_em),
  },
];

export function TeacherDashboardPage() {
  const [data, setData] = useState<DashboardProfessorResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    apiFetch<DashboardProfessorResponse>("/professor/dashboard/")
      .then((response) => {
        if (active) setData(response);
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
  }, []);

  return (
    <>
      <PageMeta title="Professor | AutoPonto" description="Dashboard acadêmica do professor." />
      <div className="page-header">
        <div className="page-header-row">
          <div>
            <div className="page-pretitle">Professor</div>
            <h1 className="page-title">Dashboard do professor</h1>
            <p className="page-description">Acompanhe aulas do dia, chamadas abertas e turmas ministradas.</p>
          </div>
        </div>
      </div>

      {loading && <div className="alert alert-info">Carregando dashboard...</div>}
      {error && <div className="alert alert-error">{error}</div>}

      {data && (
        <>
          <div className="dashboard-kpi-grid academic-kpi-grid">
            <StatCard label="Aulas hoje" value={data.totais.aulas_hoje} icon={<CalendarIcon />} tone="teal" />
            <StatCard label="Chamadas abertas" value={data.totais.chamadas_abertas} icon={<UnlockIcon />} tone="yellow" />
            <StatCard label="Pendentes" value={data.totais.chamadas_pendentes} icon={<ClockIcon />} tone="red" />
            <StatCard label="Turmas" value={data.totais.turmas_ministradas} icon={<UsersIcon />} tone="blue" />
          </div>

          <div className="academic-grid-two">
            <section className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">Aulas de hoje</div>
                  <div className="card-subtitle">Aulas das turmas ministradas hoje.</div>
                </div>
              </div>
              <div className="card-body">
                <SimpleTable
                  columns={lessonColumns}
                  rows={data.aulas_hoje}
                  rowKey={(row) => row.aula_id}
                  emptyState={<EmptyState title="Nenhuma aula hoje" text="As aulas do dia aparecerão aqui." />}
                />
              </div>
            </section>

            <section className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">Chamadas abertas</div>
                  <div className="card-subtitle">Aulas aguardando fechamento.</div>
                </div>
              </div>
              <div className="card-body">
                <SimpleTable
                  columns={lessonColumns}
                  rows={data.chamadas_abertas}
                  rowKey={(row) => row.aula_id}
                  emptyState={<EmptyState title="Nenhuma chamada aberta" text="Chamadas abertas aparecerão nesta lista." />}
                />
              </div>
            </section>
          </div>

          <section className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Chamadas pendentes</div>
                <div className="card-subtitle">Aulas planejadas que ainda não foram abertas.</div>
              </div>
            </div>
            <div className="card-body">
              <SimpleTable
                columns={lessonColumns}
                rows={data.chamadas_pendentes}
                rowKey={(row) => row.aula_id}
                emptyState={<EmptyState title="Sem chamadas pendentes" text="Não há aulas planejadas pendentes até hoje." />}
              />
            </div>
          </section>

          <section className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Turmas ministradas</div>
                <div className="card-subtitle">Acesso rápido aos dados gerais de cada turma.</div>
              </div>
            </div>
            <div className="card-body">
              <DataTable
                columns={turmaColumns}
                rows={data.turmas}
                context={undefined}
                rowKey={(row) => row.turma_id}
                rowActions={(row) => <Link className="btn btn-outline btn-sm" to={turmaPath(row.turma_id)}>Abrir</Link>}
                emptyState={<EmptyState title="Nenhuma turma" text="Turmas ministradas aparecerão aqui." />}
              />
            </div>
          </section>

          <section className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Presenças recentes</div>
                <div className="card-subtitle">Últimos registros recebidos das chamadas.</div>
              </div>
            </div>
            <div className="card-body">
              <SimpleTable
                columns={presencaColumns}
                rows={data.presencas_recentes}
                rowKey={(row) => row.presenca_id}
                emptyState={<EmptyState title="Sem presenças recentes" text="Registros de presença aparecerão após reconhecimentos." />}
              />
            </div>
          </section>
        </>
      )}
    </>
  );
}
