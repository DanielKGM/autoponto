import type { FormEvent } from "react";
import { apiFetch } from "../../api";
import { Botao } from "../../components/Botao";
import type { MatriculaTurmaCrud, TurmaCrud, UsuarioCrud } from "../../types";
import { SelectCampo, valorTexto, type Opcao } from "./adminShared";

type Props = {
  alunos: UsuarioCrud[];
  professores: UsuarioCrud[];
  turmas: TurmaCrud[];
  matriculas: MatriculaTurmaCrud[];
  onCriado: (mensagem: string) => Promise<void>;
};

function opcoesUsuarios(usuarios: UsuarioCrud[]): Opcao[] {
  return usuarios.map((usuario) => ({ id: usuario.id, rotulo: `${usuario.nome_completo || usuario.username}${usuario.matricula ? ` (${usuario.matricula})` : ""}` }));
}

function opcoesTurmas(turmas: TurmaCrud[]): Opcao[] {
  return turmas.map((turma) => ({ id: turma.id, rotulo: turma.codigo }));
}

export function VinculosAcademicos({ alunos, professores, turmas, matriculas, onCriado }: Props) {
  async function matricularAluno(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const form = new FormData(evento.currentTarget);
    await apiFetch("/matriculas-turma/", { method: "POST", body: JSON.stringify({ aluno: valorTexto(form, "aluno"), turma: valorTexto(form, "turma"), ativo: true }) });
    evento.currentTarget.reset();
    await onCriado("Aluno matriculado na turma.");
  }

  async function vincularProfessor(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const form = new FormData(evento.currentTarget);
    const turma = turmas.find((item) => item.id === valorTexto(form, "turma"));
    const professor = valorTexto(form, "professor");
    const professoresAtuais = turma?.professores || [];
    const professores = Array.from(new Set([...professoresAtuais, professor].filter(Boolean)));
    await apiFetch(`/turmas/${valorTexto(form, "turma")}/`, { method: "PATCH", body: JSON.stringify({ professores }) });
    evento.currentTarget.reset();
    await onCriado("Professor vinculado a turma.");
  }

  return (
    <section className="panel-stack">
      <section className="panel form-section">
        <h3>Matriculas e professores</h3>
        <form className="form-grid compact" onSubmit={matricularAluno}>
          <SelectCampo name="aluno" label="Aluno" opcoes={opcoesUsuarios(alunos)} />
          <SelectCampo name="turma" label="Turma" opcoes={opcoesTurmas(turmas)} />
          <Botao>Matricular aluno</Botao>
        </form>
        <form className="form-grid compact" onSubmit={vincularProfessor}>
          <SelectCampo name="professor" label="Professor" opcoes={opcoesUsuarios(professores)} />
          <SelectCampo name="turma" label="Turma" opcoes={opcoesTurmas(turmas)} />
          <Botao>Vincular professor</Botao>
        </form>
      </section>
      <section className="panel">
        <h3>Matriculas registradas</h3>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Aluno</th><th>Turma</th><th>Status</th></tr></thead>
            <tbody>
              {matriculas.map((matricula) => {
                const aluno = alunos.find((item) => item.id === matricula.aluno);
                const turma = turmas.find((item) => item.id === matricula.turma);
                return <tr key={matricula.id}><td>{aluno?.nome_completo || aluno?.username || matricula.aluno}</td><td>{turma?.codigo || matricula.turma}</td><td><span className={`badge ${matricula.ativo ? "ok" : "offline"}`}>{matricula.ativo ? "Ativa" : "Inativa"}</span></td></tr>;
              })}
            </tbody>
          </table>
        </div>
      </section>
    </section>
  );
}
