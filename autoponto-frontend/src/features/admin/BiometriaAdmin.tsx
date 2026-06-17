import type { FormEvent } from "react";
import { apiFetch } from "../../api";
import { Botao } from "../../components/Botao";
import { arquivoParaBase64, validarArquivosBiometria } from "../../shared/biometria";
import type { UsuarioCrud } from "../../types";
import { SelectCampo, type Opcao } from "./adminShared";

type Props = {
  alunos: UsuarioCrud[];
  onCriado: (mensagem: string) => Promise<void>;
  onErro: (mensagem: string) => void;
};

export function BiometriaAdmin({ alunos, onCriado, onErro }: Props) {
  const alunoOpcoes: Opcao[] = alunos.map((aluno) => ({ id: aluno.id, rotulo: `${aluno.nome_completo || aluno.username}${aluno.matricula ? ` (${aluno.matricula})` : ""}` }));

  async function cadastrarBiometria(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const form = evento.currentTarget;
    const dados = new FormData(form);
    const arquivo = dados.get("arquivo");
    if (!(arquivo instanceof File) || arquivo.size === 0) {
      onErro("Selecione uma imagem.");
      return;
    }
    const erroArquivo = validarArquivosBiometria([arquivo]);
    if (erroArquivo) {
      onErro(erroArquivo);
      return;
    }
    const capturas = [await arquivoParaBase64(arquivo)];
    await apiFetch("/perfis-biometricos/matricular/", {
      method: "POST",
      body: JSON.stringify({ aluno_id: String(dados.get("aluno_id") || ""), capturas, versao_modelo: "sface" }),
    });
    form.reset();
    await onCriado("Biometria do aluno cadastrada.");
  }

  return (
    <section className="panel form-section">
      <h3>Biometria de aluno</h3>
      <form className="form-grid compact" onSubmit={cadastrarBiometria}>
        <SelectCampo name="aluno_id" label="Aluno" opcoes={alunoOpcoes} />
        <label>Imagem do rosto<input name="arquivo" type="file" accept="image/*" required /></label>
        <Botao>Cadastrar rosto</Botao>
      </form>
    </section>
  );
}
