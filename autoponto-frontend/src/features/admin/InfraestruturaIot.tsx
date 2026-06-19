import { useState, type FormEvent } from "react";
import { apiFetch } from "../../api";
import { Botao } from "../../components/Botao";
import type { DiagnosticoInterSCity, DispositivoEsp32Crud, DispositivoStatus, NoBordaCrud, SalaCrud } from "../../types";
import { Campo, SelectCampo, valorOpcional, valorTexto, type Opcao } from "./adminShared";

type Props = {
  nos: NoBordaCrud[];
  salas: SalaCrud[];
  dispositivos: DispositivoEsp32Crud[];
  status: DispositivoStatus[];
  diagnostico: DiagnosticoInterSCity;
  onCriado: (mensagem: string) => Promise<void>;
};

function opcoes<T extends { id: string }>(itens: T[], rotulo: (item: T) => string): Opcao[] {
  return itens.map((item) => ({ id: item.id, rotulo: rotulo(item) }));
}

export function InfraestruturaIot({ nos, salas, dispositivos, status, diagnostico, onCriado }: Props) {
  async function criarNo(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const form = new FormData(evento.currentTarget);
    await apiFetch("/nos-borda/", { method: "POST", body: JSON.stringify({ codigo: valorTexto(form, "codigo"), nome: valorTexto(form, "nome"), ativo: true }) });
    evento.currentTarget.reset();
    await onCriado("No de borda cadastrado.");
  }

  async function criarDispositivo(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const form = new FormData(evento.currentTarget);
    await apiFetch("/dispositivos-esp32/", { method: "POST", body: JSON.stringify({ codigo: valorTexto(form, "codigo"), nome: valorTexto(form, "nome"), no: valorOpcional(form, "no"), sala: valorOpcional(form, "sala"), interscity_uuid: valorTexto(form, "interscity_uuid"), latitude: valorOpcional(form, "latitude"), longitude: valorOpcional(form, "longitude"), ativo: true }) });
    evento.currentTarget.reset();
    await onCriado("ESP32 cadastrada.");
  }

  return (
    <section className="panel-stack">
      <section className="panel form-section">
        <h3>Nos e ESP32</h3>
        <form className="form-grid compact" onSubmit={criarNo}><Campo label="Codigo"><input name="codigo" placeholder="88A29E606012" required /></Campo><Campo label="Nome"><input name="nome" placeholder="raspberry-tcc" required /></Campo><Botao>Cadastrar no</Botao></form>
        <form className="form-grid compact" onSubmit={criarDispositivo}><SelectCampo name="no" label="No" opcoes={opcoes(nos, (no) => `${no.codigo} - ${no.nome}`)} required={false} /><SelectCampo name="sala" label="Sala" opcoes={opcoes(salas, (sala) => `${sala.codigo} - ${sala.nome}`)} required={false} /><Campo label="Codigo"><input name="codigo" placeholder="9084CED6CDC0" required /></Campo><Campo label="Nome"><input name="nome" placeholder="esp32-tcc" required /></Campo><Campo label="UUID IntersCity"><input name="interscity_uuid" placeholder="8cf4ce45-..." /></Campo><Campo label="Latitude"><input name="latitude" placeholder="-2.558300" /></Campo><Campo label="Longitude"><input name="longitude" placeholder="-44.307700" /></Campo><Botao>Cadastrar ESP32</Botao></form>
      </section>
      <MapaDispositivos status={status} />
      <section className="panel"><h3>Diagnostico IntersCity UFMA</h3><div className="diagnostico-grid">{Object.entries(diagnostico).map(([servico, info]) => <div key={servico} className="diagnostico-item"><strong>{servico}</strong><span className={`badge ${info.status}`}>{info.status}</span></div>)}</div></section>
      <section className="panel"><h3>ESP32 cadastradas</h3><div className="table-wrap"><table><thead><tr><th>Codigo</th><th>Nome</th><th>No</th><th>Sala</th><th>UUID IntersCity</th></tr></thead><tbody>{dispositivos.map((d) => <tr key={d.id}><td>{d.codigo}</td><td>{d.nome}</td><td>{d.no_codigo || d.no || "-"}</td><td>{d.sala_nome || d.sala || "-"}</td><td>{d.interscity_uuid || "-"}</td></tr>)}</tbody></table></div></section>
    </section>
  );
}

export function MapaDispositivos({ status }: { status: DispositivoStatus[] }) {
  const [selecionado, setSelecionado] = useState<DispositivoStatus | null>(null);

  return (
    <section className="panel map-panel">
      <div className="panel-header"><div><h3>Mapa operacional</h3><p>Visao demonstrativa das ESP32 com localizacao e recurso IntersCity cadastrado.</p></div><span className="badge info">Atualizacao manual</span></div>
      <div className="mapa-campus">
        {status.map((dispositivo, indice) => (
          <button key={dispositivo.id} type="button" onClick={() => setSelecionado(dispositivo)} className="map-pin idle" style={{ left: `${18 + (indice % 4) * 20}%`, top: `${24 + Math.floor(indice / 4) * 22}%` }}>
            <strong>{dispositivo.nome}</strong>
            <span>{dispositivo.sala || "Sala nao definida"}</span>
            <small>{dispositivo.latitude}, {dispositivo.longitude}</small>
          </button>
        ))}
        {status.length === 0 && <p className="map-empty">Nenhum dispositivo cadastrado.</p>}
      </div>
      {selecionado && <div className="map-detail"><strong>{selecionado.codigo}</strong><span>Predio: {selecionado.predio || "-"}</span><span>Sala: {selecionado.sala || "-"}</span><span>UUID IntersCity: {selecionado.interscity_uuid || "-"}</span></div>}
    </section>
  );
}

