import type { ReactNode } from "react";
import { ThemeToggleButton } from "../components/common/ThemeToggleButton";
import { GitHubIcon } from "../components/icons";

export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <main className="auth-page">
      <div className="auth-card">
        {children}
      </div>
      <div className="auth-theme">
        <ThemeToggleButton />
        <a
          href="https://github.com/DanielKGM"
          target="_blank"
          rel="noreferrer"
          className="tb-btn"
          aria-label="Abrir GitHub"
          data-tooltip="GitHub"
        >
          <GitHubIcon />
        </a>
      </div>
    </main>
  );
}
