import { useEffect, useMemo, useState, type FormEvent } from "react";
import { apiFetch, detalheErro, normalizarLista } from "../../api";
import { Botao } from "../../components/Botao";
import { Mensagem } from "../../components/Mensagem";
import { ProfessorPainel } from "../professor/ProfessorPainel";
import type {
  CampusCrud,
  CursoCrud,
  DiagnosticoInterSCity,
  DisciplinaCrud,
  DispositivoEsp32Crud,
  DispositivoStatus,
  HorarioAulaCrud,
  HorarioPadraoUFMACrud,
  MatriculaTurmaCrud,
  NoBordaCrud,
  PeriodoLetivoCrud,
  PredioCrud,
  SalaCrud,
  TurmaCrud,
  UsuarioCrud,
} from "../../types";
import { BiometriaAdmin } from "./BiometriaAdmin";
import { CadastrosAcademicos } from "./CadastrosAcademicos";
import { InfraestruturaIot } from "./InfraestruturaIot";
import { Campo, valorTexto } from "./adminShared";
import { VinculosAcademicos } from "./VinculosAcademicos";

type AbaAdmin = "resumo" | "academico" | "vinculos" | "iot" | "biometria" | "relatorios";

type EstadoAdmin = {
  usuarios: UsuarioCrud[];
  campi: CampusCrud[];
  predios: PredioCrud[];
  salas: SalaCrud[];
  periodos: PeriodoLetivoCrud[];
  cursos: CursoCrud[];
  disciplinas: DisciplinaCrud[];
  turmas: TurmaCrud[];
  matriculas: MatriculaTurmaCrud[];
  horariosPadrao: HorarioPadraoUFMACrud[];
  horariosAula: HorarioAulaCrud[];
  nos: NoBordaCrud[];
  dispositivos: DispositivoEsp32Crud[];
  status: DispositivoStatus[];
  diagnostico: DiagnosticoInterSCity;
};

const estadoInicial: EstadoAdmin = {
  usuarios: [],
  campi: [],
  predios: [],
  salas: [],
  periodos: [],
  cursos: [],
  disciplinas: [],
  turmas: [],
  matriculas: [],
  horariosPadrao: [],
  horariosAula: [],
  nos: [],
  dispositivos: [],
  status: [],
  diagnostico: {},
};

export function AdminPainel() {
  const [dados, setDados] = useState<EstadoAdmin>(estadoInicial);
  const [aba, setAba] = useState<AbaAdmin>("resumo");
  const [mensagem, setMensagem] = useState("");
  const [erro, setErro] = useState("");
  const alunos = useMemo(() => dados.usuarios.filter((u) => u.papel === "ALUNO"), [dados.usuarios]);
  const professores = useMemo(() => dados.usuarios.filter((u) => u.papel === "PROFESSOR"), [dados.usuarios]);

  async function carregar() {
    const [usuarios, campi, predios, salas, periodos, cursos, disciplinas, turmas, matriculas, horariosPadrao, horariosAula, nos, dispositivos, status, diagnostico] = await Promise.all([
      apiFetch<UsuarioCrud[] | { results: UsuarioCrud[] }>("/usuarios/"),
      apiFetch<CampusCrud[] | { results: CampusCrud[] }>("/campi/"),
      apiFetch<PredioCrud[] | { results: PredioCrud[] }>("/predios/"),
      apiFetch<SalaCrud[] | { results: SalaCrud[] }>("/salas/"),
      apiFetch<PeriodoLetivoCrud[] | { results: PeriodoLetivoCrud[] }>("/periodos-letivos/"),
      apiFetch<CursoCrud[] | { results: CursoCrud[] }>("/cursos/"),
      apiFetch<DisciplinaCrud[] | { results: DisciplinaCrud[] }>("/disciplinas/"),
      apiFetch<TurmaCrud[] | { results: TurmaCrud[] }>("/turmas/"),
      apiFetch<MatriculaTurmaCrud[] | { results: MatriculaTurmaCrud[] }>("/matriculas-turma/"),
      apiFetch<HorarioPadraoUFMACrud[] | { results: HorarioPadraoUFMACrud[] }>("/horarios-padrao-ufma/"),
      apiFetch<HorarioAulaCrud[] | { results: HorarioAulaCrud[] }>("/horarios-aula/"),
      apiFetch<NoBordaCrud[] | { results: NoBordaCrud[] }>("/nos-borda/"),
      apiFetch<DispositivoEsp32Crud[] | { results: DispositivoEsp32Crud[] }>("/dispositivos-esp32/"),
      apiFetch<DispositivoStatus[]>("/dispositivos-esp32/status-dashboard/"),
      apiFetch<DiagnosticoInterSCity>("/interscity/diagnostico/"),
    ]);
    setDados({
      usuarios: normalizarLista(usuarios),
      campi: normalizarLista(campi),
      predios: normalizarLista(predios),
      salas: normalizarLista(salas),
      periodos: normalizarLista(periodos),
      cursos: normalizarLista(cursos),
      disciplinas: normalizarLista(disciplinas),
      turmas: normalizarLista(turmas),
      matriculas: normalizarLista(matriculas),
      horariosPadrao: normalizarLista(horariosPadrao),
      horariosAula: normalizarLista(horariosAula),
      nos: normalizarLista(nos),
      dispositivos: normalizarLista(dispositivos),
      status,
      diagnostico,
    });
  }

  async function carregarComTratamento() {
    try {
      setErro("");
      await carregar();
    } catch (e) {
      setErro(detalheErro(e));
    }
  }

  useEffect(() => { void carregarComTratamento(); }, []);

  async function depoisDeCriar(texto: string) {
    setMensagem(texto);
    setErro("");
    await carregarComTratamento();
  }

  function erroFilho(texto: string) {
    setMensagem("");
    setErro(texto);
  }

  async function criarUsuario(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setMensagem("");
    setErro("");
    const form = evento.currentTarget;
    const dadosForm = new FormData(form);
    try {
      const payload = {
        username: valorTexto(dadosForm, "username"),
        email: valorTexto(dadosForm, "email"),
        nome_completo: valorTexto(dadosForm, "nome_completo"),
        matricula: valorTexto(dadosForm, "matricula"),
        papel: valorTexto(dadosForm, "papel"),
        password: valorTexto(dadosForm, "password"),
        is_active: true,
      };
      await apiFetch("/usuarios/", { method: "POST", body: JSON.stringify(payload) });
      form.reset();
      await depoisDeCriar("Usuario cadastrado.");
    } catch (e) {
      setErro(detalheErro(e));
    }
  }

  return (
    <section className="page-grid">
      <header className="page-title"><h2>Painel administrativo</h2><p>Cadastros academicos, vinculos, biometria, infraestrutura IoT e relatorios.</p></header>
      {mensagem && <Mensagem tipo="ok" texto={mensagem} />}{erro && <Mensagem tipo="erro" texto={erro} />}
      <nav className="tabs" aria-label="Areas administrativas">
        {(["resumo", "academico", "vinculos", "iot", "biometria", "relatorios"] as AbaAdmin[]).map((item) => <Botao key={item} className={aba === item ? "ativo" : ""} onClick={() => setAba(item)}>{rotuloAba(item)}</Botao>)}
      </nav>
      {aba === "resumo" && <ResumoAdmin dados={dados} alunos={alunos.length} professores={professores.length} onCriarUsuario={criarUsuario} />}
      {aba === "academico" && <CadastrosAcademicos {...dados} professores={professores} onCriado={depoisDeCriar} />}
      {aba === "vinculos" && <VinculosAcademicos alunos={alunos} professores={professores} turmas={dados.turmas} matriculas={dados.matriculas} onCriado={depoisDeCriar} />}
      {aba === "iot" && <InfraestruturaIot nos={dados.nos} salas={dados.salas} dispositivos={dados.dispositivos} status={dados.status} diagnostico={dados.diagnostico} onCriado={depoisDeCriar} />}
      {aba === "biometria" && <BiometriaAdmin alunos={alunos} onCriado={depoisDeCriar} onErro={erroFilho} />}
      {aba === "relatorios" && <ProfessorPainel />}
    </section>
  );
}

function rotuloAba(aba: AbaAdmin): string {
  const rotulos: Record<AbaAdmin, string> = { resumo: "Resumo", academico: "Academico", vinculos: "Vinculos", iot: "IoT", biometria: "Biometria", relatorios: "Relatorios" };
  return rotulos[aba];
}

function ResumoAdmin({ dados, alunos, professores, onCriarUsuario }: { dados: EstadoAdmin; alunos: number; professores: number; onCriarUsuario: (evento: FormEvent<HTMLFormElement>) => void }) {
  return (
    <section className="panel-stack">
      <section className="stats-grid">
        <div className="stat"><strong>{dados.usuarios.length}</strong><span>Usuarios</span></div>
        <div className="stat"><strong>{alunos}</strong><span>Alunos</span></div>
        <div className="stat"><strong>{professores}</strong><span>Professores</span></div>
        <div className="stat"><strong>{dados.turmas.length}</strong><span>Turmas</span></div>
        <div className="stat"><strong>{dados.matriculas.length}</strong><span>Matriculas</span></div>
        <div className="stat"><strong>{dados.status.length}</strong><span>ESP32</span></div>
      </section>
      <section className="panel form-section">
        <h3>Cadastrar usuario</h3>
        <form className="form-grid compact" onSubmit={onCriarUsuario}>
          <Campo label="Usuario"><input name="username" placeholder="daniel.campos" required /></Campo>
          <Campo label="Email"><input name="email" placeholder="opcional" type="email" /></Campo>
          <Campo label="Nome completo"><input name="nome_completo" placeholder="Nome do usuario" /></Campo>
          <Campo label="Matricula"><input name="matricula" placeholder="20250000000" /></Campo>
          <Campo label="Papel"><select name="papel" defaultValue="ALUNO"><option value="ALUNO">Aluno</option><option value="PROFESSOR">Professor</option><option value="ADMINISTRADOR">Administrador</option></select></Campo>
          <Campo label="Senha inicial"><input name="password" placeholder="opcional" type="password" /></Campo>
          <Botao>Cadastrar usuario</Botao>
        </form>
      </section>
      <section className="panel">
        <h3>Usuarios recentes</h3>
        <div className="table-wrap"><table><thead><tr><th>Usuario</th><th>Nome</th><th>Papel</th><th>Matricula</th></tr></thead><tbody>{dados.usuarios.slice(0, 12).map((usuario) => <tr key={usuario.id}><td>{usuario.username}</td><td>{usuario.nome_completo || "-"}</td><td>{usuario.papel}</td><td>{usuario.matricula || "-"}</td></tr>)}</tbody></table></div>
      </section>
    </section>
  );
}
