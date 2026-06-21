import { useState, type FormEvent } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { detalheErro, login } from "../api";
import { BrandLogo } from "../components/common/BrandLogo";
import { PageMeta } from "../components/common/PageMeta";
import { Button } from "../components/ui/Button";
import { AuthLayout } from "../layout/AuthLayout";
import { destinoAposLogin } from "../app/navigation";

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
        <section className="w-full max-w-md">
          <div className="mb-8">
            <BrandLogo size="lg" className="mb-8" />
            <h1 className="mb-2 text-title-sm font-semibold text-gray-800 dark:text-white/90 sm:text-title-md">Entrar</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">Use seu usuario e senha para acessar o painel.</p>
          </div>
          <form onSubmit={submit} className="space-y-6">
            <label className="grid gap-2 text-sm font-medium text-gray-700 dark:text-gray-300">
              Usuario
              <input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                autoComplete="username"
                required
                className="h-11 rounded-lg border border-gray-300 bg-transparent px-4 py-2.5 text-sm text-gray-800 shadow-theme-xs outline-none transition placeholder:text-gray-400 focus:border-brand-300 focus:ring-4 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
              />
            </label>
            <label className="grid gap-2 text-sm font-medium text-gray-700 dark:text-gray-300">
              Senha
              <input
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                type="password"
                autoComplete="current-password"
                required
                className="h-11 rounded-lg border border-gray-300 bg-transparent px-4 py-2.5 text-sm text-gray-800 shadow-theme-xs outline-none transition placeholder:text-gray-400 focus:border-brand-300 focus:ring-4 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
              />
            </label>
            {error && <div className="rounded-lg border border-error-500/20 bg-error-50 px-4 py-3 text-sm font-medium text-error-500">{error}</div>}
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? "Entrando..." : "Entrar"}
            </Button>
          </form>
        </section>
      </AuthLayout>
    </>
  );
}
