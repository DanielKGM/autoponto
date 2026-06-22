import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";
import { carregarSessaoAutenticada, detalheErro, login } from "../api";
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
  const [checkingSession, setCheckingSession] = useState(true);
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const next = params.get("next");

  useEffect(() => {
    let active = true;

    async function redirectAuthenticated() {
      try {
        const me = await carregarSessaoAutenticada();
        if (active && me) {
          navigate(destinoAposLogin(me, next), { replace: true });
        }
      } finally {
        if (active) setCheckingSession(false);
      }
    }

    void redirectAuthenticated();
    return () => {
      active = false;
    };
  }, [navigate, next]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const me = await login(username, password);
      navigate(destinoAposLogin(me, next), { replace: true });
    } catch (err) {
      setError(detalheErro(err));
    } finally {
      setLoading(false);
    }
  }

  const accessMailto = `mailto:daniel.cgm@discente.ufma.br,danielgaldez10@hotmail.com?subject=${encodeURIComponent(
    "Solicitacao de acesso ao AutoPonto",
  )}&body=${encodeURIComponent(
    "Olá,\n\nSolicito acesso ao AutoPonto.\n\nNickname:\nNome completo:\nMatricula:\nDisciplinas:\n\nObrigado.",
  )}`;

  if (checkingSession) {
    return <main className="loading-page">Verificando sessao...</main>;
  }

  return (
    <>
      <PageMeta
        title="Entrar | AutoPonto"
        description="Acesso ao painel AutoPonto."
      />
      <AuthLayout>
        <div className="auth-brand">
          <BrandLogo size="lg" />
        </div>
        <h1 className="auth-title">Entrar</h1>
        <p className="auth-subtitle">
          Use seu usuario e senha para acessar o painel.
        </p>

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

        <div className="auth-footer">
          Não possui um cadastro?{" "}
          <a href={accessMailto}>
            Solicite seu acesso via e-mail institucional
          </a>
        </div>
        <div className="auth-footer auth-footer-secondary">
          <Link to="/mapa-iot">Acessar mapa de dispositivos</Link>
        </div>
      </AuthLayout>
    </>
  );
}
