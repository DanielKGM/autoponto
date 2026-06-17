import { useEffect, useMemo, useState, type FormEvent } from "react";
import { apiFetch, detalheErro, normalizarLista } from "../../api";
import { Botao } from "../../components/Botao";
import { Mensagem } from "../../components/Mensagem";
import { arquivoParaBase64, validarArquivosBiometria } from "../../shared/biometria";
import { ProfessorPainel } from "../professor/ProfessorPainel";
import type { DiagnosticoInterSCity, DispositivoStatus, TurmaCrud, UsuarioCrud } from "../../types";

export function AdminPainel() {
  const [usuarios, setUsuarios] = useState<UsuarioCrud[]>([]);
  const [turmas, setTurmas] = useState<TurmaCrud[]>([]);
  const [dispositivos, setDispositivos] = useState<DispositivoStatus[]>([]);
  const [diagnostico, setDiagnostico] = useState<DiagnosticoInterSCity>({});
  const [mensagem, setMensagem] = useState("");
  const [erro, setErro] = useState("");
  const alunos = useMemo(() => usuarios.filter((u) => u.papel === "ALUNO"), [usuarios]);
  const professores = useMemo(() => usuarios.filter((u) => u.papel === "PROFESSOR"), [usuarios]);

  async function carregar() {
    try {
      const [usuariosApi, turmasApi, dispositivosApi, diagApi] = await Promise.all([
        apiFetch<UsuarioCrud[] | { results: UsuarioCrud[] }>("/usuarios/"),
        apiFetch<TurmaCrud[] | { results: TurmaCrud[] }>("/turmas/"),
        apiFetch<DispositivoStatus[]>("/dispositivos-esp32/status-dashboard/"),
        apiFetch<DiagnosticoInterSCity>("/interscity/diagnostico/"),
      ]);
      setUsuarios(normalizarLista(usuariosApi)); setTurmas(normalizarLista(turmasApi)); setDispositivos(dispositivosApi); setDiagnostico(diagApi);
    } catch (e) { setErro(detalheErro(e)); }
  }
  useEffect(() => { void carregar(); }, []);

  async function criarUsuario(evento: FormEvent<HTMLFormElement>) { evento.preventDefault(); setMensagem(""); setErro(""); const form = evento.currentTarget; const dados = new FormData(form); try { await apiFetch("/usuarios/", { method: "POST", body: JSON.stringify(Object.fromEntries(dados)) }); form.reset(); setMensagem("Usuario cadastrado."); await carregar(); } catch (e) { setErro(detalheErro(e)); } }
  async function matricularAluno(evento: FormEvent<HTMLFormElement>) { evento.preventDefault(); setMensagem(""); setErro(""); const form = evento.currentTarget; const dados = Object.fromEntries(new FormData(form)); try { await apiFetch("/matriculas-turma/", { method: "POST", body: JSON.stringify({ ...dados, ativo: true }) }); form.reset(); setMensagem("Aluno matriculado na turma."); await carregar(); } catch (e) { setErro(detalheErro(e)); } }
  async function vincularProfessor(evento: FormEvent<HTMLFormElement>) { evento.preventDefault(); setMensagem(""); setErro(""); const dados = Object.fromEntries(new FormData(evento.currentTarget)) as { turma: string; professor: string }; try { await apiFetch(`/turmas/${dados.turma}/`, { method: "PATCH", body: JSON.stringify({ professores: [dados.professor] }) }); setMensagem("Professor vinculado a turma."); await carregar(); } catch (e) { setErro(detalheErro(e)); } }
  async function cadastrarBiometria(evento: FormEvent<HTMLFormElement>) { evento.preventDefault(); setMensagem(""); setErro(""); const form = evento.currentTarget; const dados = new FormData(form); const arquivo = dados.get("arquivo"); if (!(arquivo instanceof File) || arquivo.size === 0) { setErro("Selecione uma imagem."); return; } const erroArquivo = validarArquivosBiometria([arquivo]); if (erroArquivo) { setErro(erroArquivo); return; } try { const capturas = [await arquivoParaBase64(arquivo)]; await apiFetch("/perfis-biometricos/matricular/", { method: "POST", body: JSON.stringify({ aluno_id: dados.get("aluno_id"), capturas, versao_modelo: "sface" }) }); form.reset(); setMensagem("Biometria do aluno cadastrada."); } catch (e) { setErro(detalheErro(e)); } }

  return (
    <section className="page-grid">
      <header className="page-title"><h2>Painel administrativo</h2><p>Cadastros principais, vinculos academicos, biometria e diagnostico IoT.</p></header>
      {mensagem && <Mensagem tipo="ok" texto={mensagem} />}{erro && <Mensagem tipo="erro" texto={erro} />}
      <section className="stats-grid"><div className="stat"><strong>{usuarios.length}</strong><span>Usuarios</span></div><div className="stat"><strong>{turmas.length}</strong><span>Turmas</span></div><div className="stat"><strong>{alunos.length}</strong><span>Alunos</span></div><div className="stat"><strong>{professores.length}</strong><span>Professores</span></div><div className="stat"><strong>{dispositivos.length}</strong><span>ESP32</span></div></section>
      <section className="panel admin-grid">
        <form className="form-grid" onSubmit={criarUsuario}><h3>Cadastrar usuario</h3><input name="username" placeholder="usuario" required /><input name="email" placeholder="email" type="email" required /><input name="nome_completo" placeholder="nome completo" /><input name="matricula" placeholder="matricula" /><select name="papel" defaultValue="ALUNO"><option value="ALUNO">Aluno</option><option value="PROFESSOR">Professor</option><option value="ADMINISTRADOR">Administrador</option></select><input name="password" placeholder="senha inicial" type="password" /><Botao>Cadastrar</Botao></form>
        <form className="form-grid" onSubmit={matricularAluno}><h3>Matricular aluno</h3><select name="aluno" required><option value="">Aluno</option>{alunos.map((aluno) => <option key={aluno.id} value={aluno.id}>{aluno.nome_completo || aluno.username}</option>)}</select><select name="turma" required><option value="">Turma</option>{turmas.map((turma) => <option key={turma.id} value={turma.id}>{turma.codigo}</option>)}</select><Botao>Matricular</Botao></form>
        <form className="form-grid" onSubmit={vincularProfessor}><h3>Vincular professor</h3><select name="professor" required><option value="">Professor</option>{professores.map((professor) => <option key={professor.id} value={professor.id}>{professor.nome_completo || professor.username}</option>)}</select><select name="turma" required><option value="">Turma</option>{turmas.map((turma) => <option key={turma.id} value={turma.id}>{turma.codigo}</option>)}</select><Botao>Vincular</Botao></form>
        <form className="form-grid" onSubmit={cadastrarBiometria}><h3>Biometria de aluno</h3><select name="aluno_id" required><option value="">Aluno</option>{alunos.map((aluno) => <option key={aluno.id} value={aluno.id}>{aluno.nome_completo || aluno.username}</option>)}</select><input name="arquivo" type="file" accept="image/*" required /><Botao>Cadastrar rosto</Botao></form>
      </section>
      <section className="panel"><div className="panel-header"><div><h3>Dispositivos ESP32</h3></div></div><div className="table-wrap"><table><thead><tr><th>Codigo</th><th>Sala</th><th>No</th><th>Status</th><th>Efetivo</th><th>Origem</th></tr></thead><tbody>{dispositivos.map((d) => <tr key={d.id}><td>{d.codigo}</td><td>{d.sala || "-"}</td><td>{d.no || "-"}</td><td><span className={`badge ${d.status}`}>{d.status}</span></td><td><span className={`badge ${d.status_efetivo}`}>{d.status_efetivo}</span></td><td>{d.origem_status}</td></tr>)}</tbody></table></div></section>
      <section className="panel"><h3>Diagnostico Interscity UFMA</h3><div className="diagnostico-grid">{Object.entries(diagnostico).map(([servico, info]) => <div key={servico} className="diagnostico-item"><strong>{servico}</strong><span className={`badge ${info.status}`}>{info.status}</span></div>)}</div></section>
      <ProfessorPainel />
    </section>
  );
}
