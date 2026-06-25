import { useEffect, useState } from "react";
import { apiFetch, detalheErro } from "../../../shared/api";
import { useSession } from "../../../shared/session";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { PageMeta } from "../../../shared/ui/PageMeta";
import { ProgressBar } from "../../../shared/ui/ProgressBar";
import { SimpleTable, type SimpleTableColumn } from "../../../shared/ui/SimpleTable";
import type { FrequenciaTurmaAluno, ResumoFrequenciaAlunoResponse } from "../../../shared/types";
import { percentText } from "../../../shared/domain/academicUtils";

const frequencyColumns: SimpleTableColumn<FrequenciaTurmaAluno>[] = [
  {
    key: "disciplina",
    label: "Turma/Disciplina",
    render: (row) => (
      <div>
        <span className="cell-strong">{row.disciplina}</span>
        <div className="lesson-table-subtext">{row.codigo} · {row.periodo_letivo}</div>
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
        <ProgressBar value={row.percentual} tone={row.percentual >= 75 ? "green" : "yellow"} />
      </div>
    ),
  },
];

function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("") || "AP";
}

export function ProfilePage() {
  const { me } = useSession();
  const [frequency, setFrequency] = useState<ResumoFrequenciaAlunoResponse | null>(null);
  const [periodoId, setPeriodoId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
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

  return (
    <>
      <PageMeta
        title="Perfil | AutoPonto"
        description="Perfil do usuário autenticado."
      />
      <div className="page-header">
        <div className="page-pretitle">Conta</div>
        <h1 className="page-title">Perfil</h1>
      </div>

      <section className="card profile-overview-card">
        <div className="card-header">
          <div>
            <div className="card-title">Dados do usuário</div>
            <div className="card-subtitle">Resumo da sessão autenticada.</div>
          </div>
        </div>
        <div className="card-body profile-overview">
          <div className="profile-main">
            <div className="profile-avatar profile-avatar-lg" aria-hidden="true">{initials(nome)}</div>
            <div className="profile-main-copy">
              <span className="status status-blue">{me.usuario.papel}</span>
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
              <div className="card-subtitle">Resumo por turma e disciplina, calculado com aulas fechadas.</div>
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
            {loading && <div className="alert alert-info">Carregando frequência...</div>}
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
                  emptyState={<EmptyState title="Sem frequência" text="Nenhuma aula fechada foi encontrada para este período." />}
                />
              </>
            )}
          </div>
        </section>
      )}
    </>
  );
}
