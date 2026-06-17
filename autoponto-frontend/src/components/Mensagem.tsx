type MensagemProps = {
  tipo: "ok" | "erro" | "info";
  texto: string;
};

export function Mensagem({ tipo, texto }: MensagemProps) {
  return <div className={`mensagem ${tipo}`}>{texto}</div>;
}
