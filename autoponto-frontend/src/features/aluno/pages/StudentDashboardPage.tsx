import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { Link } from "react-router";
import type { EChartsOption } from "echarts";
import { apiFetch, detalheErro } from "../../../shared/api";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { PageMeta } from "../../../shared/ui/PageMeta";
import { ProgressBar } from "../../../shared/ui/ProgressBar";
import {
  SimpleTable,
  type SimpleTableColumn,
} from "../../../shared/ui/SimpleTable";
import { StatCard } from "../../../shared/ui/StatCard";
import {
  CalendarIcon,
  ChartIcon,
  CheckCircleIcon,
  ClockIcon,
} from "../../../shared/ui/icons";
import type {
  AulaResumo,
  DashboardAlunoResponse,
  FrequenciaTurmaAluno,
} from "../../../shared/types";
import {
  formatDate,
  formatDateTime,
  percentText,
  statusAlunoClass,
  statusAlunoLabel,
  statusAulaClass,
  statusAulaLabel,
} from "../../../shared/domain/academicUtils";
import {
  formatTimeRange,
  lessonDetailPath,
} from "../../../shared/domain/studentCalendarUtils";

const EChart = lazy(() =>
  import("../../../shared/ui/EChart").then((module) => ({
    default: module.EChart,
  })),
);

const frequencyColumns: SimpleTableColumn<FrequenciaTurmaAluno>[] = [
  {
    key: "disciplina",
    label: "Turma",
    render: (row) => (
      <div>
        <span className="cell-strong">{row.disciplina}</span>
        <div className="lesson-table-subtext">
          {row.codigo} · {row.periodo_letivo}
        </div>
      </div>
    ),
  },
  { key: "total_aulas_fechadas", label: "Aulas", align: "center" },
  { key: "presencas", label: "Presenças", align: "center" },
  { key: "faltas", label: "Faltas", align: "center" },
  {
    key: "percentual",
    label: "Frequência",
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
];

const recentColumns: SimpleTableColumn<
  DashboardAlunoResponse["ultimas_presencas"][number]
>[] = [
  {
    key: "disciplina",
    label: "Aula",
    render: (row) => (
      <div>
        <span className="cell-strong">{row.disciplina}</span>
        <div className="lesson-table-subtext">
          {formatDate(row.data)} · {formatTimeRange(row.inicio, row.fim)}
        </div>
      </div>
    ),
  },
  { key: "sala", label: "Sala", align: "center" },
  {
    key: "status",
    label: "Status",
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

function lessonCard(lesson: AulaResumo) {
  return (
    <Link
      className="lesson-list-item"
      to={lessonDetailPath(lesson.turma_id, lesson.aula_id)}
      key={lesson.aula_id}
    >
      <div>
        <strong>{lesson.disciplina}</strong>
        <span>
          {lesson.turma} · {lesson.sala}
        </span>
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
  );
}

export function StudentDashboardPage() {
  const [data, setData] = useState<DashboardAlunoResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    apiFetch<DashboardAlunoResponse>("/me/dashboard-aluno/")
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

  const chartOption = useMemo<EChartsOption>(
    () => ({
      tooltip: { trigger: "axis" },
      legend: { bottom: 0 },
      grid: { top: 24, right: 12, bottom: 48, left: 36 },
      xAxis: {
        type: "category",
        data: data?.frequencia_por_turma.map((item) => item.disciplina) ?? [],
        axisLabel: { hideOverlap: true },
      },
      yAxis: { type: "value", max: 100 },
      series: [
        {
          name: "Frequência",
          type: "bar",
          data: data?.frequencia_por_turma.map((item) => item.percentual) ?? [],
          itemStyle: { color: "#2A9D8F" },
        },
      ],
    }),
    [data],
  );

  return (
    <>
      <PageMeta
        title="Aluno | AutoPonto"
        description="Dashboard acadêmica do aluno."
      />
      <div className="page-header">
        <div className="page-header-row">
          <div>
            <div className="page-pretitle">Aluno</div>
            <h1 className="page-title">Dashboard do aluno</h1>
            <p className="page-description">
              Acompanhe aulas, presença recente e frequência por turma.
            </p>
          </div>
        </div>
      </div>

      {loading && (
        <div className="alert alert-info">Carregando dashboard...</div>
      )}
      {error && <div className="alert alert-error">{error}</div>}

      {data && (
        <>
          <div className="dashboard-kpi-grid academic-kpi-grid">
            <StatCard
              label="Frequência geral"
              value={percentText(data.resumo.percentual)}
              icon={<ChartIcon />}
              tone="green"
              subtext={`${data.resumo.presentes} presenças · ${data.resumo.ausentes} faltas`}
            />
            <StatCard
              label="Aulas fechadas"
              value={data.resumo.total_fechadas}
              icon={<CheckCircleIcon />}
              tone="blue"
            />
            <StatCard
              label="Pendentes"
              value={data.resumo.pendentes}
              icon={<ClockIcon />}
              tone="yellow"
            />
            <StatCard
              label="Aulas hoje"
              value={data.aulas_hoje.length}
              icon={<CalendarIcon />}
              tone="teal"
            />
          </div>

          <div className="academic-grid-two">
            <section className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">Aulas de hoje</div>
                  <div className="card-subtitle">
                    Chamadas e horários do dia.
                  </div>
                </div>
              </div>
              <div className="card-body lesson-list">
                {data.aulas_hoje.length > 0 ? (
                  data.aulas_hoje.map(lessonCard)
                ) : (
                  <EmptyState
                    title="Nenhuma aula hoje"
                    text="Quando houver aula hoje, ela aparecerá aqui."
                  />
                )}
              </div>
            </section>

            <section className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">Próximas aulas</div>
                  <div className="card-subtitle">
                    Aulas planejadas ou abertas nos próximos dias.
                  </div>
                </div>
              </div>
              <div className="card-body lesson-list">
                {data.proximas_aulas.length > 0 ? (
                  data.proximas_aulas.map(lessonCard)
                ) : (
                  <EmptyState
                    title="Sem próximas aulas"
                    text="A agenda futura da turma aparecerá nesta seção."
                  />
                )}
              </div>
            </section>
          </div>

          <section className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Frequência por turma</div>
                <div className="card-subtitle">
                  Percentual calculado somente com aulas fechadas.
                </div>
              </div>
            </div>
            <div className="card-body">
              {data.frequencia_por_turma.length > 0 && (
                <Suspense
                  fallback={
                    <div className="chart-loading">Carregando gráfico...</div>
                  }
                >
                  <EChart option={chartOption} className="academic-chart" />
                </Suspense>
              )}
              <SimpleTable
                columns={frequencyColumns}
                rows={data.frequencia_por_turma}
                rowKey={(row) => row.turma_id}
                emptyState={
                  <EmptyState
                    title="Sem frequência"
                    text="Nenhuma aula fechada foi encontrada para suas turmas."
                  />
                }
              />
            </div>
          </section>

          <section className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Últimas presenças</div>
                <div className="card-subtitle">
                  Aulas recentes com status resumido.
                </div>
              </div>
              <Link className="btn btn-outline btn-sm" to="/app/perfil">
                Ver detalhe
              </Link>
            </div>
            <div className="card-body">
              <SimpleTable
                columns={recentColumns}
                rows={data.ultimas_presencas}
                rowKey={(row) => row.aula_id}
                emptyState={
                  <EmptyState
                    title="Sem presenças recentes"
                    text="As presenças aparecerão após chamadas registradas."
                  />
                }
              />
            </div>
          </section>
        </>
      )}
    </>
  );
}
