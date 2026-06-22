import { PageMeta } from "../components/common/PageMeta";
import { useSession } from "../app/session";

export function ProfilePage() {
  const { me } = useSession();
  const fields = [
    ["Usuario", me.usuario.username],
    ["Nome", me.usuario.nome_completo || "-"],
    ["Papel", me.usuario.papel],
    ["Matricula", me.usuario.matricula || "-"],
    ["Email", me.usuario.email || "-"],
  ];

  return (
    <>
      <PageMeta title="Perfil | AutoPonto" description="Perfil do usuario autenticado." />
      <div className="page-header">
        <div className="page-pretitle">Conta</div>
        <h1 className="page-title">Perfil</h1>
      </div>
      <section className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Dados do usuario</div>
            <div className="card-subtitle">Resumo da sessao autenticada.</div>
          </div>
        </div>
        <div className="card-body profile-grid">
          {fields.map(([label, value]) => (
            <div key={label} className="profile-field">
              <span className="profile-label">{label}</span>
              <strong className="profile-value">{value}</strong>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
