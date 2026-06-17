import { useEffect, useState } from "react";
import { carregarSessaoAutenticada, detalheErro, logout } from "../api";
import { Botao } from "../components/Botao";
import { AdminPainel } from "../features/admin/AdminPainel";
import { AlunoPainel } from "../features/aluno/AlunoPainel";
import { LoginScreen } from "../features/auth/LoginScreen";
import { MapaOperacional } from "../features/mapa/MapaOperacional";
import { PerfilPainel } from "../features/perfil/PerfilPainel";
import { ProfessorPainel } from "../features/professor/ProfessorPainel";
import type { MeResponse } from "../types";

type AreaApp = "aluno" | "professor" | "admin" | "mapa" | "perfil";

function areaInicial(me: MeResponse): AreaApp {
  if (me.permissoes.areas.includes("admin")) return "admin";
  if (me.permissoes.areas.includes("professor")) return "professor";
  return "aluno";
}

function areasDisponiveis(me: MeResponse): AreaApp[] {
  const areas = me.permissoes.areas.filter((item): item is AreaApp => item === "admin" || item === "professor" || item === "aluno");
  return [...areas, "mapa", "perfil"];
}

function rotuloArea(area: AreaApp): string {
  const rotulos: Record<AreaApp, string> = { aluno: "Aluno", professor: "Professor", admin: "Admin", mapa: "Mapa", perfil: "Perfil" };
  return rotulos[area];
}

export default function App() {
  const [me, setMe] = useState<MeResponse | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState("");
  const [area, setArea] = useState<AreaApp>("aluno");

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
          {areasDisponiveis(me).map((item) => (
            <Botao key={item} className={area === item ? "ativo" : ""} onClick={() => setArea(item)}>
              {rotuloArea(item)}
            </Botao>
          ))}
          <Botao onClick={sair}>Sair</Botao>
        </nav>
      </header>
      {area === "aluno" && <AlunoPainel />}
      {area === "professor" && <ProfessorPainel />}
      {area === "admin" && <AdminPainel />}
      {area === "mapa" && <MapaOperacional />}
      {area === "perfil" && <PerfilPainel me={me} />}
    </main>
  );
}
