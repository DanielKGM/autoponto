import type { MeResponse } from "../../types";

export function PerfilPainel({ me }: { me: MeResponse }) {
  return (
    <section className="page-grid">
      <header className="page-title"><h2>Perfil</h2><p>Dados principais da conta autenticada.</p></header>
      <section className="panel profile-grid">
        <div><span className="field-label">Usuario</span><strong>{me.usuario.username}</strong></div>
        <div><span className="field-label">Nome</span><strong>{me.usuario.nome_completo || "-"}</strong></div>
        <div><span className="field-label">Papel</span><strong>{me.usuario.papel}</strong></div>
        <div><span className="field-label">Matricula</span><strong>{me.usuario.matricula || "-"}</strong></div>
        <div><span className="field-label">Email</span><strong>{me.usuario.email || "-"}</strong></div>
      </section>
    </section>
  );
}
