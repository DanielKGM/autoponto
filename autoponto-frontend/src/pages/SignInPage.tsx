import { useState, type FormEvent } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { detalheErro, login } from "../api";
import { BrandLogo } from "../components/common/BrandLogo";
import { PageMeta } from "../components/common/PageMeta";
import { Button } from "../components/ui/Button";
import { AuthLayout } from "../layout/AuthLayout";
import { destinoAposLogin } from "../app/navigation";
import { LockIcon, UserIcon } from "../components/icons";

export function SignInPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [params] = useSearchParams();
  const navigate = useNavigate();

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const me = await login(username, password);
      navigate(destinoAposLogin(me, params.get("next")), { replace: true });
    } catch (err) {
      setError(detalheErro(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageMeta title="Entrar | AutoPonto" description="Acesso ao painel AutoPonto." />
      <AuthLayout>
        <div className="auth-brand">
          <BrandLogo size="lg" />
        </div>
        <h1 className="auth-title">Entrar</h1>
        <p className="auth-subtitle">Use seu usuario e senha para acessar o painel.</p>

        <form onSubmit={submit}>
          <div className="form-group">
            <label className="form-label" htmlFor="username">
              Usuario
            </label>
            <div className="input-group">
              <UserIcon className="input-icon" />
              <input
                id="username"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                autoComplete="username"
                required
                className="form-control"
                placeholder="usuario"
              />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="password">
              Senha
            </label>
            <div className="input-group">
              <LockIcon className="input-icon" />
              <input
                id="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                type="password"
                autoComplete="current-password"
                required
                className="form-control"
                placeholder="********"
              />
            </div>
          </div>
          {error && <div className="alert alert-error">{error}</div>}
          <Button type="submit" disabled={loading} className="btn-block btn-lg">
            {loading ? "Entrando..." : "Entrar"}
          </Button>
        </form>
      </AuthLayout>
    </>
  );
}
