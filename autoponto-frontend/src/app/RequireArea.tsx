import type { ReactNode } from "react";
import { Navigate } from "react-router";
import { destinoPadrao, usuarioPodeAcessarArea, type AreaApp } from "./navigation";
import { useSession } from "./session";

export function RequireArea({ area, children }: { area: AreaApp; children: ReactNode }) {
  const { me } = useSession();
  if (!usuarioPodeAcessarArea(me, area)) {
    return <Navigate to={destinoPadrao(me)} replace />;
  }
  return children;
}
