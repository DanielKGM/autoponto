import { useEffect, useState } from "react";
import { apiFetch, detalheErro } from "../../api";
import { Botao } from "../../components/Botao";
import { Mensagem } from "../../components/Mensagem";
import { MapaDispositivos } from "../admin/InfraestruturaIot";
import type { DispositivoStatus } from "../../types";

export function MapaOperacional() {
  const [status, setStatus] = useState<DispositivoStatus[]>([]);
  const [erro, setErro] = useState("");
  const [atualizadoEm, setAtualizadoEm] = useState<string | null>(null);

  async function carregar() {
    try {
      setErro("");
      const dados = await apiFetch<DispositivoStatus[]>("/public/mapa/dispositivos/");
      setStatus(dados);
      setAtualizadoEm(new Date().toLocaleString("pt-BR"));
    } catch (e) {
      setErro(detalheErro(e));
    }
  }

  useEffect(() => { void carregar(); }, []);

  return (
    <section className="page-grid">
      <header className="page-title"><h2>Mapa operacional</h2><p>ESP32 cadastradas com localizacao e recurso IntersCity.</p></header>
      <div className="panel-header map-actions"><span>{atualizadoEm ? `Atualizado em ${atualizadoEm}` : "Aguardando atualizacao"}</span><Botao onClick={() => void carregar()}>Atualizar</Botao></div>
      {erro && <Mensagem tipo="erro" texto={erro} />}
      <MapaDispositivos status={status} />
    </section>
  );
}
