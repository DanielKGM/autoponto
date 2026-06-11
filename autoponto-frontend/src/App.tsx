import { useEffect, useMemo, useState, type ButtonHTMLAttributes, type ChangeEvent, type FormEvent } from "react";
import { apiFetch, carregarSessaoAutenticada, detalheErro, login, logout, normalizarLista } from "./api";
import type {
  MeResponse,
  PresencaAluno,
  RelatorioResumoTurma,
  RelatorioTurmaData,
  TurmaCrud,
  TurmaResumo,
  UsuarioCrud,
} from "./types";

type DiagnosticoInterSCity = Record<string, { ok: boolean; status: string; codigo_http?: number; detalhe?: string }>;
const MAX_CAPTURAS_BIOMETRIA = 5;
const MAX_BYTES_BIOMETRIA = 2 * 1024 * 1024;

function hojeIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function formatarData(valor: string): string {
  return new Intl.DateTimeFormat("pt-BR", { timeZone: "UTC" }).format(new Date(`${valor}T00:00:00Z`));
}

function formatarHora(valor: string): string {
  return new Intl.DateTimeFormat("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(valor));
}

function areaInicial(me: MeResponse): string {
  if (me.permissoes.areas.includes("admin")) return "admin";
  if (me.permissoes.areas.includes("professor")) return "professor";
  return "aluno";
}

async function arquivoParaBase64(arquivo: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const resultado = String(reader.result || "");
      resolve(resultado.includes(",") ? resultado.split(",")[1] : resultado);
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(arquivo);
  });
}

function validarArquivosBiometria(arquivos: File[]): string | null {
  if (arquivos.length === 0) {
    return "Selecione ao menos uma imagem.";
  }
  if (arquivos.length > MAX_CAPTURAS_BIOMETRIA) {
    return `Selecione no maximo ${MAX_CAPTURAS_BIOMETRIA} imagens.`;
  }
  const invalido = arquivos.find((arquivo) => !arquivo.type.startsWith("image/"));
  if (invalido) {
    return "Use apenas arquivos de imagem.";
  }
  const grande = arquivos.find((arquivo) => arquivo.size > MAX_BYTES_BIOMETRIA);
  if (grande) {
    return "Cada imagem deve ter no maximo 2 MB.";
  }
  return null;
}

function Mensagem({ tipo, texto }: { tipo: "ok" | "erro" | "info"; texto: string }) {
  return <div className={`mensagem ${tipo}`}>{texto}</div>;
}

function Botao({ children, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button {...props}>{children}</button>;
}

function App() {
  const [me, setMe] = useState<MeResponse | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState("");
  const [area, setArea] = useState("aluno");

  useEffect(() => {
    async function carregarSessao() {
      try {
        const dados = await carregarSessaoAutenticada();
        if (dados) {
          setMe(dados);
          setArea(areaInicial(dados));
        }
      } catch (e) {
        setErro(detalheErro(e));
      } finally {
        setCarregando(false);
      }
    }
    void carregarSessao();
  }, []);

  function sair() {
    void logout();
    setMe(null);
    setArea("aluno");
  }

  if (carregando) {
    return <main className="tela-centro">Carregando AutoPonto...</main>;
  }

  if (!me) {
    return <LoginScreen onEntrar={(dados) => { setMe(dados); setArea(areaInicial(dados)); }} erroInicial={erro} />;
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <strong>AutoPonto</strong>
          <span>{me.usuario.nome_completo || me.usuario.username}</span>
        </div>
        <nav>
          {me.permissoes.areas.map((item) => (
            <Botao key={item} className={area === item ? "ativo" : ""} onClick={() => setArea(item)}>
              {item === "admin" ? "Admin" : item === "professor" ? "Professor" : "Aluno"}
            </Botao>
          ))}
          <Botao onClick={sair}>Sair</Botao>
        </nav>
      </header>

      {area === "aluno" && <AlunoPainel />}
      {area === "professor" && <ProfessorPainel />}
      {area === "admin" && <AdminPainel />}
    </main>
  );
}

function LoginScreen({ onEntrar, erroInicial }: { onEntrar: (me: MeResponse) => void; erroInicial?: string }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [erro, setErro] = useState(erroInicial || "");
  const [carregando, setCarregando] = useState(false);

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    setCarregando(true);
    setErro("");
    try {
      onEntrar(await login(username, password));
    } catch (e) {
      setErro(detalheErro(e));
    } finally {
      setCarregando(false);
    }
  }

  return (
    <main className="login-layout">
      <section className="login-panel">
        <div className="marca">AutoPonto</div>
        <h1>Controle acadêmico de frequência</h1>
        <form onSubmit={enviar} className="form-grid">
          <label>
            Usuário
            <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required />
          </label>
          <label>
            Senha
            <input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              type="password"
              autoComplete="current-password"
              required
            />
          </label>
          {erro && <Mensagem tipo="erro" texto={erro} />}
          <Botao disabled={carregando}>{carregando ? "Entrando..." : "Entrar"}</Botao>
        </form>
      </section>
    </main>
  );
}

function AlunoPainel() {
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
      await apiFetch("/me/biometria/", {
        method: "POST",
        body: JSON.stringify({ capturas, versao_modelo: "sface" }),
      });
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
      <header className="page-title">
        <h2>Painel do aluno</h2>
        <p>Turmas do período ativo, presença registrada e cadastro biométrico.</p>
      </header>

      <section className="panel">
        <h3>Turmas deste semestre</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Disciplina</th>
                <th>Turma</th>
                <th>Período</th>
                <th>Professor</th>
              </tr>
            </thead>
            <tbody>
              {turmas.map((turma) => (
                <tr key={turma.turma_id}>
                  <td>{turma.disciplina}</td>
                  <td>{turma.codigo}</td>
                  <td>{turma.periodo_letivo}</td>
                  <td>{turma.professores.map((p) => p.nome).join(", ") || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel two-columns">
        <div>
          <h3>Presenças</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Disciplina</th>
                  <th>Status</th>
                  <th>Sala</th>
                </tr>
              </thead>
              <tbody>
                {presencas.map((presenca) => (
                  <tr key={presenca.presenca_id}>
                    <td>{formatarData(presenca.data)}</td>
                    <td>{presenca.disciplina}</td>
                    <td><span className={`badge ${presenca.status.toLowerCase()}`}>{presenca.status}</span></td>
                    <td>{presenca.sala}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <form className="form-grid" onSubmit={cadastrarBiometria}>
          <h3>Cadastro biométrico</h3>
          <label>
            Imagens do rosto
            <input
              type="file"
              accept="image/*"
              multiple
              onChange={(evento: ChangeEvent<HTMLInputElement>) => {
                const selecionados = Array.from(evento.target.files || []);
                setArquivos(selecionados);
                setErro(validarArquivosBiometria(selecionados) || "");
              }}
            />
          </label>
          {mensagem && <Mensagem tipo="ok" texto={mensagem} />}
          {erro && <Mensagem tipo="erro" texto={erro} />}
          <Botao disabled={enviando || arquivos.length === 0}>{enviando ? "Enviando..." : "Cadastrar rosto"}</Botao>
        </form>
      </section>
    </section>
  );
}

function ProfessorPainel() {
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
      <header className="page-title">
        <h2>Painel do professor</h2>
        <p>Turmas ministradas e relatórios de presença por aula.</p>
      </header>
      <form className="toolbar panel" onSubmit={buscarRelatorio}>
        <label>
          Turma
          <select value={turmaId} onChange={(e) => setTurmaId(e.target.value)}>
            {turmas.map((turma) => (
              <option key={turma.turma_id} value={turma.turma_id}>
                {turma.disciplina} - {turma.codigo}
              </option>
            ))}
          </select>
        </label>
        <label>
          Data
          <input type="date" value={data} onChange={(e) => setData(e.target.value)} />
        </label>
        <Botao>Gerar relatório</Botao>
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
      <div className="panel-header">
        <div>
          <h3>{relatorio.disciplina}</h3>
          <p>{formatarData(relatorio.data)} · {relatorio.aulas.map((aula) => `${formatarHora(aula.inicio)} ${aula.sala}`).join(", ")}</p>
        </div>
        <div className="stats">
          <span>Presentes: {relatorio.totais.presentes}</span>
          <span>Ausentes: {relatorio.totais.ausentes}</span>
          <span>Matriculados: {relatorio.totais.matriculados}</span>
        </div>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Aluno</th>
              <th>Matrícula</th>
              <th>Status</th>
              <th>Registro</th>
            </tr>
          </thead>
          <tbody>
            {relatorio.alunos.map((aluno) => (
              <tr key={aluno.aluno_id}>
                <td>{aluno.nome}</td>
                <td>{aluno.matricula || "-"}</td>
                <td><span className={`badge ${aluno.status.toLowerCase()}`}>{aluno.status}</span></td>
                <td>{aluno.registrado_em ? formatarHora(aluno.registrado_em) : "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ResumoTurma({ resumo }: { resumo: RelatorioResumoTurma }) {
  return (
    <section className="panel">
      <h3>Resumo da turma</h3>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Aluno</th>
              <th>Presenças</th>
              <th>Faltas</th>
              <th>% presença</th>
            </tr>
          </thead>
          <tbody>
            {resumo.alunos.map((aluno) => (
              <tr key={aluno.aluno_id}>
                <td>{aluno.nome}</td>
                <td>{aluno.presencas}</td>
                <td>{aluno.faltas}</td>
                <td>{aluno.percentual_presenca.toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function AdminPainel() {
  const [usuarios, setUsuarios] = useState<UsuarioCrud[]>([]);
  const [turmas, setTurmas] = useState<TurmaCrud[]>([]);
  const [diagnostico, setDiagnostico] = useState<DiagnosticoInterSCity>({});
  const [mensagem, setMensagem] = useState("");
  const [erro, setErro] = useState("");
  const alunos = useMemo(() => usuarios.filter((u) => u.papel === "ALUNO"), [usuarios]);
  const professores = useMemo(() => usuarios.filter((u) => u.papel === "PROFESSOR"), [usuarios]);

  async function carregar() {
    try {
      const [usuariosApi, turmasApi, diagApi] = await Promise.all([
        apiFetch<UsuarioCrud[] | { results: UsuarioCrud[] }>("/usuarios/"),
        apiFetch<TurmaCrud[] | { results: TurmaCrud[] }>("/turmas/"),
        apiFetch<DiagnosticoInterSCity>("/interscity/diagnostico/"),
      ]);
      setUsuarios(normalizarLista(usuariosApi));
      setTurmas(normalizarLista(turmasApi));
      setDiagnostico(diagApi);
    } catch (e) {
      setErro(detalheErro(e));
    }
  }

  useEffect(() => {
    void carregar();
  }, []);

  async function criarUsuario(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setMensagem("");
    setErro("");
    const form = evento.currentTarget;
    const dados = new FormData(form);
    try {
      await apiFetch("/usuarios/", {
        method: "POST",
        body: JSON.stringify(Object.fromEntries(dados)),
      });
      form.reset();
      setMensagem("Usuário cadastrado.");
      await carregar();
    } catch (e) {
      setErro(detalheErro(e));
    }
  }

  async function matricularAluno(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setMensagem("");
    setErro("");
    const form = evento.currentTarget;
    const dados = Object.fromEntries(new FormData(form));
    try {
      await apiFetch("/matriculas-turma/", {
        method: "POST",
        body: JSON.stringify({ ...dados, ativo: true }),
      });
      form.reset();
      setMensagem("Aluno matriculado na turma.");
      await carregar();
    } catch (e) {
      setErro(detalheErro(e));
    }
  }

  async function vincularProfessor(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setMensagem("");
    setErro("");
    const dados = Object.fromEntries(new FormData(evento.currentTarget)) as { turma: string; professor: string };
    try {
      await apiFetch(`/turmas/${dados.turma}/`, {
        method: "PATCH",
        body: JSON.stringify({ professores: [dados.professor] }),
      });
      setMensagem("Professor vinculado à turma.");
      await carregar();
    } catch (e) {
      setErro(detalheErro(e));
    }
  }

  async function cadastrarBiometria(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setMensagem("");
    setErro("");
    const form = evento.currentTarget;
    const dados = new FormData(form);
    const arquivo = dados.get("arquivo");
    if (!(arquivo instanceof File) || arquivo.size === 0) {
      setErro("Selecione uma imagem.");
      return;
    }
    const erroArquivo = validarArquivosBiometria([arquivo]);
    if (erroArquivo) {
      setErro(erroArquivo);
      return;
    }
    try {
      const capturas = [await arquivoParaBase64(arquivo)];
      await apiFetch("/perfis-biometricos/matricular/", {
        method: "POST",
        body: JSON.stringify({
          aluno_id: dados.get("aluno_id"),
          capturas,
          versao_modelo: "sface",
        }),
      });
      form.reset();
      setMensagem("Biometria do aluno cadastrada.");
    } catch (e) {
      setErro(detalheErro(e));
    }
  }

  return (
    <section className="page-grid">
      <header className="page-title">
        <h2>Painel administrativo</h2>
        <p>Cadastros principais, vínculos acadêmicos, biometria e diagnóstico IoT.</p>
      </header>

      {mensagem && <Mensagem tipo="ok" texto={mensagem} />}
      {erro && <Mensagem tipo="erro" texto={erro} />}

      <section className="stats-grid">
        <div className="stat"><strong>{usuarios.length}</strong><span>Usuários</span></div>
        <div className="stat"><strong>{turmas.length}</strong><span>Turmas</span></div>
        <div className="stat"><strong>{alunos.length}</strong><span>Alunos</span></div>
        <div className="stat"><strong>{professores.length}</strong><span>Professores</span></div>
      </section>

      <section className="panel admin-grid">
        <form className="form-grid" onSubmit={criarUsuario}>
          <h3>Cadastrar usuário</h3>
          <input name="username" placeholder="usuário" required />
          <input name="email" placeholder="email" type="email" required />
          <input name="nome_completo" placeholder="nome completo" />
          <input name="matricula" placeholder="matrícula" />
          <select name="papel" defaultValue="ALUNO">
            <option value="ALUNO">Aluno</option>
            <option value="PROFESSOR">Professor</option>
            <option value="ADMINISTRADOR">Administrador</option>
          </select>
          <input name="password" placeholder="senha inicial" type="password" />
          <Botao>Cadastrar</Botao>
        </form>

        <form className="form-grid" onSubmit={matricularAluno}>
          <h3>Matricular aluno</h3>
          <select name="aluno" required>
            <option value="">Aluno</option>
            {alunos.map((aluno) => <option key={aluno.id} value={aluno.id}>{aluno.nome_completo || aluno.username}</option>)}
          </select>
          <select name="turma" required>
            <option value="">Turma</option>
            {turmas.map((turma) => <option key={turma.id} value={turma.id}>{turma.codigo}</option>)}
          </select>
          <Botao>Matricular</Botao>
        </form>

        <form className="form-grid" onSubmit={vincularProfessor}>
          <h3>Vincular professor</h3>
          <select name="professor" required>
            <option value="">Professor</option>
            {professores.map((professor) => (
              <option key={professor.id} value={professor.id}>{professor.nome_completo || professor.username}</option>
            ))}
          </select>
          <select name="turma" required>
            <option value="">Turma</option>
            {turmas.map((turma) => <option key={turma.id} value={turma.id}>{turma.codigo}</option>)}
          </select>
          <Botao>Vincular</Botao>
        </form>

        <form className="form-grid" onSubmit={cadastrarBiometria}>
          <h3>Biometria de aluno</h3>
          <select name="aluno_id" required>
            <option value="">Aluno</option>
            {alunos.map((aluno) => <option key={aluno.id} value={aluno.id}>{aluno.nome_completo || aluno.username}</option>)}
          </select>
          <input name="arquivo" type="file" accept="image/*" required />
          <Botao>Cadastrar rosto</Botao>
        </form>
      </section>

      <section className="panel">
        <h3>Diagnóstico Interscity UFMA</h3>
        <div className="diagnostico-grid">
          {Object.entries(diagnostico).map(([servico, info]) => (
            <div key={servico} className="diagnostico-item">
              <strong>{servico}</strong>
              <span className={`badge ${info.status}`}>{info.status}</span>
            </div>
          ))}
        </div>
      </section>

      <ProfessorPainel />
    </section>
  );
}

export default App;
