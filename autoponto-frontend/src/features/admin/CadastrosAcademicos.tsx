import type { FormEvent } from "react";
import { apiFetch } from "../../api";
import { Botao } from "../../components/Botao";
import type {
  CampusCrud,
  CursoCrud,
  DisciplinaCrud,
  HorarioPadraoUFMACrud,
  PeriodoLetivoCrud,
  PredioCrud,
  SalaCrud,
  TurmaCrud,
  UsuarioCrud,
} from "../../types";
import { Campo, SelectCampo, ativoPadrao, valorTexto, type Opcao } from "./adminShared";

type Props = {
  campi: CampusCrud[];
  predios: PredioCrud[];
  salas: SalaCrud[];
  periodos: PeriodoLetivoCrud[];
  cursos: CursoCrud[];
  disciplinas: DisciplinaCrud[];
  turmas: TurmaCrud[];
  horariosPadrao: HorarioPadraoUFMACrud[];
  professores: UsuarioCrud[];
  onCriado: (mensagem: string) => Promise<void>;
};

function opcoes<T extends { id: string }>(itens: T[], rotulo: (item: T) => string): Opcao[] {
  return itens.map((item) => ({ id: item.id, rotulo: rotulo(item) }));
}

function nomePorId<T extends { id: string }>(itens: T[], id: string, rotulo: (item: T) => string): string {
  const item = itens.find((valor) => valor.id === id);
  return item ? rotulo(item) : id || "-";
}

export function CadastrosAcademicos(props: Props) {
  const campusOpcoes = opcoes(props.campi, (campus) => campus.nome);
  const predioOpcoes = opcoes(props.predios, (predio) => `${nomePorId(props.campi, predio.campus, (c) => c.nome)} - ${predio.nome}`);
  const cursoOpcoes = opcoes(props.cursos, (curso) => `${nomePorId(props.campi, curso.campus, (c) => c.nome)} - ${curso.nome}`);
  const disciplinaOpcoes = opcoes(props.disciplinas, (disciplina) => `${disciplina.codigo} - ${disciplina.nome}`);
  const periodoOpcoes = opcoes(props.periodos, (periodo) => periodo.nome);
  const turmaOpcoes = opcoes(props.turmas, (turma) => `${turma.codigo} - ${nomePorId(props.disciplinas, turma.disciplina, (d) => d.nome)}`);
  const salaOpcoes = opcoes(props.salas, (sala) => `${sala.codigo} - ${sala.nome}`);
  const horarioOpcoes = opcoes(props.horariosPadrao, (horario) => `${horario.codigo} (${horario.horario_inicio.slice(0, 5)}-${horario.horario_fim.slice(0, 5)})`);
  const professorOpcoes = opcoes(props.professores, (professor) => professor.nome_completo || professor.username);

  async function criarCampus(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const form = new FormData(evento.currentTarget);
    await apiFetch("/campi/", { method: "POST", body: JSON.stringify({ nome: valorTexto(form, "nome"), ativo: ativoPadrao(form) }) });
    evento.currentTarget.reset();
    await props.onCriado("Campus cadastrado.");
  }

  async function criarPredio(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const form = new FormData(evento.currentTarget);
    await apiFetch("/predios/", { method: "POST", body: JSON.stringify({ campus: valorTexto(form, "campus"), nome: valorTexto(form, "nome"), ativo: true }) });
    evento.currentTarget.reset();
    await props.onCriado("Predio cadastrado.");
  }

  async function criarSala(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const form = new FormData(evento.currentTarget);
    await apiFetch("/salas/", { method: "POST", body: JSON.stringify({ predio: valorTexto(form, "predio"), codigo: valorTexto(form, "codigo"), nome: valorTexto(form, "nome"), ativo: true }) });
    evento.currentTarget.reset();
    await props.onCriado("Sala cadastrada.");
  }

  async function criarPeriodo(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const form = new FormData(evento.currentTarget);
    await apiFetch("/periodos-letivos/", { method: "POST", body: JSON.stringify({ nome: valorTexto(form, "nome"), data_inicio: valorTexto(form, "data_inicio"), data_fim: valorTexto(form, "data_fim"), ativo: ativoPadrao(form) }) });
    evento.currentTarget.reset();
    await props.onCriado("Periodo letivo cadastrado.");
  }

  async function criarCurso(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const form = new FormData(evento.currentTarget);
    await apiFetch("/cursos/", { method: "POST", body: JSON.stringify({ campus: valorTexto(form, "campus"), nome: valorTexto(form, "nome"), ativo: true }) });
    evento.currentTarget.reset();
    await props.onCriado("Curso cadastrado.");
  }

  async function criarDisciplina(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const form = new FormData(evento.currentTarget);
    await apiFetch("/disciplinas/", { method: "POST", body: JSON.stringify({ curso: valorTexto(form, "curso"), codigo: valorTexto(form, "codigo"), nome: valorTexto(form, "nome"), ativo: true }) });
    evento.currentTarget.reset();
    await props.onCriado("Disciplina cadastrada.");
  }

  async function criarTurma(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const form = new FormData(evento.currentTarget);
    const professor = valorTexto(form, "professor");
    await apiFetch("/turmas/", { method: "POST", body: JSON.stringify({ periodo_letivo: valorTexto(form, "periodo_letivo"), disciplina: valorTexto(form, "disciplina"), codigo: valorTexto(form, "codigo"), professores: professor ? [professor] : [], ativo: true }) });
    evento.currentTarget.reset();
    await props.onCriado("Turma cadastrada.");
  }

  async function criarHorarioPadrao(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const form = new FormData(evento.currentTarget);
    await apiFetch("/horarios-padrao-ufma/", { method: "POST", body: JSON.stringify({ codigo: valorTexto(form, "codigo"), dia_semana: Number(valorTexto(form, "dia_semana")), horario_inicio: valorTexto(form, "horario_inicio"), horario_fim: valorTexto(form, "horario_fim"), ativo: true }) });
    evento.currentTarget.reset();
    await props.onCriado("Horario padrao cadastrado.");
  }

  async function criarHorarioAula(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const form = new FormData(evento.currentTarget);
    await apiFetch("/horarios-aula/", { method: "POST", body: JSON.stringify({ turma: valorTexto(form, "turma"), sala: valorTexto(form, "sala"), horario_padrao: valorTexto(form, "horario_padrao"), ativo: true }) });
    evento.currentTarget.reset();
    await props.onCriado("Horario de aula vinculado.");
  }

  return (
    <section className="panel-stack">
      <section className="panel form-section">
        <h3>Estrutura fisica</h3>
        <form className="form-grid compact" onSubmit={criarCampus}><Campo label="Campus"><input name="nome" placeholder="Cidade Universitaria Dom Delgado - Sao Luis" required /></Campo><Botao>Cadastrar campus</Botao></form>
        <form className="form-grid compact" onSubmit={criarPredio}><SelectCampo name="campus" label="Campus" opcoes={campusOpcoes} /><Campo label="Predio"><input name="nome" placeholder="Paulo Freire" required /></Campo><Botao>Cadastrar predio</Botao></form>
        <form className="form-grid compact" onSubmit={criarSala}><SelectCampo name="predio" label="Predio" opcoes={predioOpcoes} /><Campo label="Codigo"><input name="codigo" placeholder="105N" required /></Campo><Campo label="Nome"><input name="nome" placeholder="105 Norte" required /></Campo><Botao>Cadastrar sala</Botao></form>
      </section>

      <section className="panel form-section">
        <h3>Oferta academica</h3>
        <form className="form-grid compact" onSubmit={criarPeriodo}><Campo label="Periodo"><input name="nome" placeholder="2026.1" required /></Campo><Campo label="Inicio"><input name="data_inicio" type="date" required /></Campo><Campo label="Fim"><input name="data_fim" type="date" required /></Campo><Botao>Cadastrar periodo</Botao></form>
        <form className="form-grid compact" onSubmit={criarCurso}><SelectCampo name="campus" label="Campus" opcoes={campusOpcoes} /><Campo label="Curso"><input name="nome" placeholder="Engenharia da Computacao" required /></Campo><Botao>Cadastrar curso</Botao></form>
        <form className="form-grid compact" onSubmit={criarDisciplina}><SelectCampo name="curso" label="Curso" opcoes={cursoOpcoes} /><Campo label="Codigo"><input name="codigo" placeholder="EECP0021" required /></Campo><Campo label="Nome"><input name="nome" placeholder="SISTEMAS DISTRIBUIDOS" required /></Campo><Botao>Cadastrar disciplina</Botao></form>
        <form className="form-grid compact" onSubmit={criarTurma}><SelectCampo name="periodo_letivo" label="Periodo" opcoes={periodoOpcoes} /><SelectCampo name="disciplina" label="Disciplina" opcoes={disciplinaOpcoes} /><Campo label="Codigo"><input name="codigo" placeholder="20261EECP0021" required /></Campo><SelectCampo name="professor" label="Professor" opcoes={professorOpcoes} required={false} /><Botao>Cadastrar turma</Botao></form>
      </section>

      <section className="panel form-section">
        <h3>Horarios UFMA</h3>
        <form className="form-grid compact" onSubmit={criarHorarioPadrao}><Campo label="Codigo"><input name="codigo" placeholder="2N34" required /></Campo><Campo label="Dia"><select name="dia_semana" required><option value="2">Segunda</option><option value="3">Terca</option><option value="4">Quarta</option><option value="5">Quinta</option><option value="6">Sexta</option><option value="7">Sabado</option></select></Campo><Campo label="Inicio"><input name="horario_inicio" type="time" required /></Campo><Campo label="Fim"><input name="horario_fim" type="time" required /></Campo><Botao>Cadastrar padrao</Botao></form>
        <form className="form-grid compact" onSubmit={criarHorarioAula}><SelectCampo name="turma" label="Turma" opcoes={turmaOpcoes} /><SelectCampo name="sala" label="Sala" opcoes={salaOpcoes} /><SelectCampo name="horario_padrao" label="Horario padrao" opcoes={horarioOpcoes} /><Botao>Vincular horario</Botao></form>
      </section>
    </section>
  );
}

