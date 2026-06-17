import type { ReactNode } from "react";

export type Opcao = { id: string; rotulo: string };

type CampoProps = {
  label: string;
  children: ReactNode;
};

export function Campo({ label, children }: CampoProps) {
  return <label>{label}{children}</label>;
}

type SelectCampoProps = {
  name: string;
  label: string;
  opcoes: Opcao[];
  required?: boolean;
  placeholder?: string;
};

export function SelectCampo({ name, label, opcoes, required = true, placeholder = "Selecione" }: SelectCampoProps) {
  return (
    <Campo label={label}>
      <select name={name} required={required}>
        <option value="">{placeholder}</option>
        {opcoes.map((opcao) => <option key={opcao.id} value={opcao.id}>{opcao.rotulo}</option>)}
      </select>
    </Campo>
  );
}

export function valorTexto(form: FormData, campo: string): string {
  return String(form.get(campo) || "").trim();
}

export function valorOpcional(form: FormData, campo: string): string | null {
  const valor = valorTexto(form, campo);
  return valor || null;
}

export function ativoPadrao(form: FormData): boolean {
  return form.get("ativo") !== "false";
}
