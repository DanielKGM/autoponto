import { useEffect, useState } from "react";
import { carregarSessaoAutenticada, detalheErro, logout } from "../api";
import { Botao } from "../components/Botao";
import { AdminPainel } from "../features/admin/AdminPainel";
import { AlunoPainel } from "../features/aluno/AlunoPainel";
import { LoginScreen } from "../features/auth/LoginScreen";
import { ProfessorPainel } from "../features/professor/ProfessorPainel";
import type { MeResponse } from "../types";

function areaInicial(me: MeResponse): string {
  if (me.permissoes.areas.includes("admin")) return "admin";
  if (me.permissoes.areas.includes("professor")) return "professor";
  return "aluno";
}

export default function App() {
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

  if (carregando) return <main className="tela-centro">Carregando AutoPonto...</main>;
  if (!me) return <LoginScreen onEntrar={(dados) => { setMe(dados); setArea(areaInicial(dados)); }} erroInicial={erro} />;

  return (
    <main className="app-shell">
      <header className="topbar">
        <div><strong>AutoPonto</strong><span>{me.usuario.nome_completo || me.usuario.username}</span></div>
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
