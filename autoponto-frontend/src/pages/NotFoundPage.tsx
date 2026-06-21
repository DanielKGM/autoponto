import { Link } from "react-router";
import { PageMeta } from "../components/common/PageMeta";

export function NotFoundPage() {
  return (
    <>
      <PageMeta title="404 | AutoPonto" description="Pagina nao encontrada." />
      <main className="relative grid min-h-[100dvh] place-items-center overflow-hidden bg-white p-6 dark:bg-gray-900">
        <div className="absolute inset-0 opacity-50 [background-image:linear-gradient(rgba(29,185,84,.12)_1px,transparent_1px),linear-gradient(90deg,rgba(29,185,84,.12)_1px,transparent_1px)] [background-size:48px_48px]" />
        <section className="relative mx-auto grid w-full max-w-md gap-8 text-center">
          <img src="/images/logo/logo-claro.svg" alt="AutoPonto" className="mx-auto h-auto w-[190px] dark:hidden" />
          <img src="/images/logo/logo-escuro.svg" alt="AutoPonto" className="mx-auto hidden h-auto w-[190px] dark:block" />
          <div>
            <p className="text-8xl font-bold tracking-tight text-gray-800 dark:text-white/90">404</p>
            <h1 className="mt-4 text-title-sm font-semibold text-gray-800 dark:text-white/90">Pagina nao encontrada</h1>
            <p className="mt-3 text-base text-gray-500 dark:text-gray-400">A rota solicitada nao existe no AutoPonto.</p>
          </div>
          <Link to="/" className="mx-auto inline-flex min-h-11 items-center justify-center rounded-lg border border-gray-300 bg-white px-5 py-3 text-sm font-medium text-gray-700 shadow-theme-xs hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-white/5">
            Voltar ao inicio
          </Link>
        </section>
      </main>
    </>
  );
}
