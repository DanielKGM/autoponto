import { useState, type FormEvent } from "react";
import { detalheErro, login } from "../../api";
import { Botao } from "../../components/Botao";
import { Mensagem } from "../../components/Mensagem";
import type { MeResponse } from "../../types";

type LoginScreenProps = {
  onEntrar: (me: MeResponse) => void;
  erroInicial?: string;
};

export function LoginScreen({ onEntrar, erroInicial }: LoginScreenProps) {
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
        <h1>Controle academico de frequencia</h1>
        <form onSubmit={enviar} className="form-grid">
          <label>
            Usuario
            <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required />
          </label>
          <label>
            Senha
            <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" autoComplete="current-password" required />
          </label>
          {erro && <Mensagem tipo="erro" texto={erro} />}
          <Botao disabled={carregando}>{carregando ? "Entrando..." : "Entrar"}</Botao>
        </form>
      </section>
    </main>
  );
}
