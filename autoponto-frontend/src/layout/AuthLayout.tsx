import type { ReactNode } from "react";
import { Link } from "react-router";
import { ThemeToggleButton } from "../components/common/ThemeToggleButton";

export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <main className="relative min-h-[100dvh] bg-white p-6 dark:bg-gray-900 sm:p-0">
      <div className="grid min-h-[100dvh] lg:grid-cols-[minmax(0,1fr)_minmax(420px,1fr)]">
        <section className="flex min-h-[calc(100dvh-48px)] items-center justify-center py-10 lg:min-h-[100dvh]">
          {children}
        </section>
        <aside className="relative hidden overflow-hidden bg-brand-950 lg:grid lg:place-items-center">
          <div className="absolute inset-0 opacity-30 [background-image:linear-gradient(rgba(255,255,255,.12)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.12)_1px,transparent_1px)] [background-size:46px_46px]" />
          <div className="relative mx-auto grid max-w-sm gap-6 px-10 text-center">
            <Link to="/" className="mx-auto block">
              <img src="/images/logo/logo-escuro.svg" alt="AutoPonto" className="h-auto w-[230px]" />
            </Link>
            <p className="text-base leading-7 text-white/65">
              Plataforma academica para presenca, biometria e operacao IoT de borda.
            </p>
          </div>
        </aside>
      </div>
      <div className="fixed bottom-6 right-6 z-50 hidden sm:block">
        <ThemeToggleButton />
      </div>
    </main>
  );
}
