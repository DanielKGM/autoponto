import { useEffect, useState, type FormEvent } from "react";
import { apiFetch, detalheErro } from "../../api";
import { Botao } from "../../components/Botao";
import { Mensagem } from "../../components/Mensagem";
import { formatarData, formatarHora, hojeIso } from "../../shared/formatacao";
import type { RelatorioResumoTurma, RelatorioTurmaData, TurmaResumo } from "../../types";

export function ProfessorPainel() {
  const [turmas, setTurmas] = useState<TurmaResumo[]>([]);
  const [turmaId, setTurmaId] = useState("");
  const [data, setData] = useState(hojeIso());
  const [relatorio, setRelatorio] = useState<RelatorioTurmaData | null>(null);
  const [resumo, setResumo] = useState<RelatorioResumoTurma | null>(null);
  const [erro, setErro] = useState("");

  useEffect(() => {
    async function carregar() {
      try {
        const dados = await apiFetch<TurmaResumo[]>("/professor/turmas/");
        setTurmas(dados);
        setTurmaId(dados[0]?.turma_id || "");
      } catch (e) {
        setErro(detalheErro(e));
      }
    }
    void carregar();
  }, []);

  async function buscarRelatorio(evento: FormEvent) {
    evento.preventDefault();
    if (!turmaId) return;
    setErro("");
    try {
      const [porData, resumoTurma] = await Promise.all([
        apiFetch<RelatorioTurmaData>(`/relatorios/turmas/${turmaId}/presencas/?data=${data}`),
        apiFetch<RelatorioResumoTurma>(`/relatorios/turmas/${turmaId}/resumo/?inicio=${data}&fim=${data}`),
      ]);
      setRelatorio(porData);
      setResumo(resumoTurma);
    } catch (e) {
      setErro(detalheErro(e));
    }
  }

  return (
    <section className="page-grid">
      <header className="page-title"><h2>Painel do professor</h2><p>Turmas ministradas e relatorios de presenca por aula.</p></header>
      <form className="toolbar panel" onSubmit={buscarRelatorio}>
        <label>Turma<select value={turmaId} onChange={(e) => setTurmaId(e.target.value)}>{turmas.map((turma) => <option key={turma.turma_id} value={turma.turma_id}>{turma.disciplina} - {turma.codigo}</option>)}</select></label>
        <label>Data<input type="date" value={data} onChange={(e) => setData(e.target.value)} /></label>
        <Botao>Gerar relatorio</Botao>
      </form>
      {erro && <Mensagem tipo="erro" texto={erro} />}
      {relatorio && <RelatorioData relatorio={relatorio} />}
      {resumo && <ResumoTurma resumo={resumo} />}
    </section>
  );
}

function RelatorioData({ relatorio }: { relatorio: RelatorioTurmaData }) {
  return (
    <section className="panel">
      <div className="panel-header"><div><h3>{relatorio.disciplina}</h3><p>{formatarData(relatorio.data)} - {relatorio.aulas.map((aula) => `${formatarHora(aula.inicio)} ${aula.sala}`).join(", ")}</p></div><div className="stats"><span>Presentes: {relatorio.totais.presentes}</span><span>Ausentes: {relatorio.totais.ausentes}</span><span>Matriculados: {relatorio.totais.matriculados}</span></div></div>
      <div className="table-wrap"><table><thead><tr><th>Aluno</th><th>Matricula</th><th>Status</th><th>Registro</th></tr></thead><tbody>{relatorio.alunos.map((aluno) => <tr key={aluno.aluno_id}><td>{aluno.nome}</td><td>{aluno.matricula || "-"}</td><td><span className={`badge ${aluno.status.toLowerCase()}`}>{aluno.status}</span></td><td>{aluno.registrado_em ? formatarHora(aluno.registrado_em) : "-"}</td></tr>)}</tbody></table></div>
    </section>
  );
}

function ResumoTurma({ resumo }: { resumo: RelatorioResumoTurma }) {
  return <section className="panel"><h3>Resumo da turma</h3><div className="table-wrap"><table><thead><tr><th>Aluno</th><th>Presencas</th><th>Faltas</th><th>% presenca</th></tr></thead><tbody>{resumo.alunos.map((aluno) => <tr key={aluno.aluno_id}><td>{aluno.nome}</td><td>{aluno.presencas}</td><td>{aluno.faltas}</td><td>{aluno.percentual_presenca.toFixed(1)}%</td></tr>)}</tbody></table></div></section>;
}
