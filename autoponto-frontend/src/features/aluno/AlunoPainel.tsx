import { useEffect, useState, type ChangeEvent, type FormEvent } from "react";
import { apiFetch, detalheErro } from "../../api";
import { Botao } from "../../components/Botao";
import { Mensagem } from "../../components/Mensagem";
import { arquivoParaBase64, validarArquivosBiometria } from "../../shared/biometria";
import { formatarData } from "../../shared/formatacao";
import type { PresencaAluno, TurmaResumo } from "../../types";

export function AlunoPainel() {
  const [turmas, setTurmas] = useState<TurmaResumo[]>([]);
  const [presencas, setPresencas] = useState<PresencaAluno[]>([]);
  const [arquivos, setArquivos] = useState<File[]>([]);
  const [mensagem, setMensagem] = useState("");
  const [erro, setErro] = useState("");
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    async function carregar() {
      try {
        const [turmasAluno, presencasAluno] = await Promise.all([
          apiFetch<TurmaResumo[]>("/me/turmas/"),
          apiFetch<PresencaAluno[]>("/me/presencas/"),
        ]);
        setTurmas(turmasAluno);
        setPresencas(presencasAluno);
      } catch (e) {
        setErro(detalheErro(e));
      }
    }
    void carregar();
  }, []);

  async function cadastrarBiometria(evento: FormEvent) {
    evento.preventDefault();
    setMensagem("");
    setErro("");
    const erroArquivos = validarArquivosBiometria(arquivos);
    if (erroArquivos) {
      setErro(erroArquivos);
      return;
    }
    setEnviando(true);
    try {
      const capturas = await Promise.all(arquivos.map(arquivoParaBase64));
      await apiFetch("/me/biometria/", { method: "POST", body: JSON.stringify({ capturas, versao_modelo: "sface" }) });
      setMensagem("Biometria cadastrada com sucesso.");
      setArquivos([]);
    } catch (e) {
      setErro(detalheErro(e));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <section className="page-grid">
      <header className="page-title"><h2>Painel do aluno</h2><p>Turmas do periodo ativo, presenca registrada e cadastro biometrico.</p></header>
      <section className="panel">
        <h3>Turmas deste semestre</h3>
        <div className="table-wrap"><table><thead><tr><th>Disciplina</th><th>Turma</th><th>Periodo</th><th>Professor</th></tr></thead><tbody>
          {turmas.map((turma) => <tr key={turma.turma_id}><td>{turma.disciplina}</td><td>{turma.codigo}</td><td>{turma.periodo_letivo}</td><td>{turma.professores.map((p) => p.nome).join(", ") || "-"}</td></tr>)}
        </tbody></table></div>
      </section>
      <section className="panel two-columns">
        <div>
          <h3>Presencas</h3>
          <div className="table-wrap"><table><thead><tr><th>Data</th><th>Disciplina</th><th>Status</th><th>Sala</th></tr></thead><tbody>
            {presencas.map((presenca) => <tr key={presenca.presenca_id}><td>{formatarData(presenca.data)}</td><td>{presenca.disciplina}</td><td><span className={`badge ${presenca.status.toLowerCase()}`}>{presenca.status}</span></td><td>{presenca.sala}</td></tr>)}
          </tbody></table></div>
        </div>
        <form className="form-grid" onSubmit={cadastrarBiometria}>
          <h3>Cadastro biometrico</h3>
          <label>Imagens do rosto<input type="file" accept="image/*" multiple onChange={(evento: ChangeEvent<HTMLInputElement>) => { const selecionados = Array.from(evento.target.files || []); setArquivos(selecionados); setErro(validarArquivosBiometria(selecionados) || ""); }} /></label>
          {mensagem && <Mensagem tipo="ok" texto={mensagem} />}
          {erro && <Mensagem tipo="erro" texto={erro} />}
          <Botao disabled={enviando || arquivos.length === 0}>{enviando ? "Enviando..." : "Cadastrar rosto"}</Botao>
        </form>
      </section>
    </section>
  );
}
