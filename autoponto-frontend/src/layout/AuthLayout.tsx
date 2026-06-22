import type { ReactNode } from "react";
import { ThemeToggleButton } from "../components/common/ThemeToggleButton";

export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <main className="auth-page">
      <div className="auth-card">
        {children}
      </div>
      <div className="auth-theme">
        <ThemeToggleButton />
      </div>
    </main>
  );
}
