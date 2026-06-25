import { Link } from "react-router";
import { PageMeta } from "../../../shared/ui/PageMeta";
import { AdminIcon } from "../../../shared/ui/icons";

export function NotFoundPage() {
  return (
    <>
      <PageMeta title="404 | AutoPonto" description="Pagina nao encontrada." />
      <main className="error-page">
        <section className="error-content">
          <div className="error-code">404</div>
          <h1 className="error-title">Pagina nao encontrada</h1>
          <p className="error-message">A rota solicitada nao existe no AutoPonto ou foi movida.</p>
          <div className="error-actions">
            <Link to="/" className="btn btn-primary">
              <AdminIcon />
              Voltar ao inicio
            </Link>
            <button type="button" className="btn btn-outline" onClick={() => history.back()}>
              Voltar
            </button>
          </div>
        </section>
      </main>
    </>
  );
}
