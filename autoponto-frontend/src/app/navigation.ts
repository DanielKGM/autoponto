import type { MeResponse } from "../types";

export type AreaApp = "aluno" | "professor" | "admin" | "mapa" | "perfil";

export type NavItem = {
  area: AreaApp;
  label: string;
  path: string;
};

const AREAS_PRIVADAS: AreaApp[] = ["aluno", "professor", "admin"];

const ROTULOS: Record<AreaApp, string> = {
  aluno: "Aluno",
  professor: "Professor",
  admin: "Admin",
  mapa: "Mapa IoT",
  perfil: "Perfil",
};

export function areaInicial(me: MeResponse): Exclude<AreaApp, "mapa" | "perfil"> {
  if (me.permissoes.areas.includes("admin")) return "admin";
  if (me.permissoes.areas.includes("professor")) return "professor";
  return "aluno";
}

export function pathDaArea(area: AreaApp): string {
  if (area === "mapa") return "/app/mapa-iot";
  return `/app/${area}`;
}

export function usuarioPodeAcessarArea(me: MeResponse, area: AreaApp): boolean {
  if (area === "mapa" || area === "perfil") return true;
  return me.permissoes.areas.includes(area);
}

export function itensNavegacao(me: MeResponse): NavItem[] {
  const areasAutorizadas = AREAS_PRIVADAS.filter((area) =>
    me.permissoes.areas.includes(area),
  );
  const areas: AreaApp[] = [...areasAutorizadas, "mapa", "perfil"];
  return areas.map((area) => ({
    area,
    label: ROTULOS[area],
    path: pathDaArea(area),
  }));
}

export function destinoPadrao(me: MeResponse): string {
  return pathDaArea(areaInicial(me));
}

function areaDoPath(path: string): AreaApp | null {
  if (path === "/mapa-iot" || path === "/app/mapa-iot") return "mapa";
  if (path === "/app/aluno") return "aluno";
  if (path === "/app/professor") return "professor";
  if (path === "/app/admin") return "admin";
  if (path === "/app/perfil") return "perfil";
  return null;
}

export function destinoAposLogin(me: MeResponse, next?: string | null): string {
  if (!next || !next.startsWith("/") || next.startsWith("//")) {
    return destinoPadrao(me);
  }
  const area = areaDoPath(next);
  if (!area || !usuarioPodeAcessarArea(me, area)) {
    return destinoPadrao(me);
  }
  return next;
}
