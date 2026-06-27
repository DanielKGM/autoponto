import { useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router";
import { carregarSessaoAutenticada, logout } from "../shared/api";
import { LoadingDots } from "../shared/ui/LoadingDots";
import { AppLayout } from "../shell/AppLayout";
import type { MeResponse } from "../shared/types";
import { SessionProvider } from "../shared/session";

export function ProtectedLayout() {
  const [me, setMe] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [signingOut, setSigningOut] = useState(false);
  const location = useLocation();

  useEffect(() => {
    let active = true;

    async function loadSession() {
      try {
        const session = await carregarSessaoAutenticada();
        if (active) setMe(session);
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadSession();
    return () => {
      active = false;
    };
  }, []);

  async function signOut() {
    setSigningOut(true);
    await logout();
    setMe(null);
    setSigningOut(false);
  }

  if (loading || signingOut) {
    return (
      <main className="loading-page">
        <LoadingDots label={signingOut ? "Saindo da conta" : "Carregando AutoPonto"} />
      </main>
    );
  }

  if (!me) {
    const next = encodeURIComponent(`${location.pathname}${location.search}`);
    return <Navigate to={`/signin?next=${next}`} replace />;
  }

  return (
    <SessionProvider me={me} signOut={signOut}>
      <AppLayout />
    </SessionProvider>
  );
}
