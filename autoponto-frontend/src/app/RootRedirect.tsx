import { useEffect, useState } from "react";
import { Navigate } from "react-router";
import { carregarSessaoAutenticada } from "../api";
import type { MeResponse } from "../types";
import { destinoPadrao } from "./navigation";

export function RootRedirect() {
  const [me, setMe] = useState<MeResponse | null | undefined>(undefined);

  useEffect(() => {
    let active = true;
    carregarSessaoAutenticada()
      .then((session) => {
        if (active) setMe(session);
      })
      .catch(() => {
        if (active) setMe(null);
      });
    return () => {
      active = false;
    };
  }, []);

  if (me === undefined) {
    return (
      <main className="loading-page">
        Carregando AutoPonto...
      </main>
    );
  }

  return <Navigate to={me ? destinoPadrao(me) : "/signin"} replace />;
}
