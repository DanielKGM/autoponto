import { useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router";
import { carregarSessaoAutenticada, logout } from "../api";
import { AppLayout } from "../layout/AppLayout";
import type { MeResponse } from "../types";
import { SessionProvider } from "./session";

export function ProtectedLayout() {
  const [me, setMe] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);
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

  function signOut() {
    void logout();
    setMe(null);
  }

  if (loading) {
    return (
      <main className="loading-page">
        Carregando AutoPonto...
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
