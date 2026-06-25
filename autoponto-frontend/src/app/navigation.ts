import type { MeResponse } from "../shared/types";

export type AreaApp = "aluno" | "professor" | "admin" | "calendario" | "mapa" | "perfil";

export type NavChild = {
  area: AreaApp;
  label: string;
  path: string;
};

export type NavItem = {
  area: AreaApp;
  label: string;
  path: string;
  children?: NavChild[];
};

const AREAS_PRIVADAS: AreaApp[] = ["aluno", "professor", "admin"];

const ROTULOS: Record<AreaApp, string> = {
  aluno: "Aluno",
  professor: "Professor",
  admin: "Admin",
  calendario: "Calendário",
  mapa: "Mapa IoT",
  perfil: "Perfil",
};

const ALUNO_CHILDREN: NavChild[] = [
  { area: "aluno", label: "Dashboard", path: "/app/aluno" },
  { area: "calendario", label: "Calendário", path: "/app/calendario" },
  { area: "aluno", label: "Biometria", path: "/app/aluno/biometria" },
];

const PROFESSOR_CHILDREN: NavChild[] = [
  { area: "professor", label: "Dashboard", path: "/app/professor" },
  { area: "calendario", label: "Calendário", path: "/app/calendario" },
];

const ADMIN_CHILDREN: NavChild[] = [
  { area: "admin", label: "Acadêmico", path: "/app/admin/academico" },
  { area: "admin", label: "IoT", path: "/app/admin/iot" },
];

export function areaInicial(me: MeResponse): Exclude<AreaApp, "calendario" | "mapa" | "perfil"> {
  if (me.permissoes.areas.includes("admin")) return "admin";
  if (me.permissoes.areas.includes("professor")) return "professor";
  return "aluno";
}

export function pathDaArea(area: AreaApp): string {
  if (area === "admin") return "/app/admin/academico";
  if (area === "mapa") return "/app/mapa-iot";
  if (area === "calendario") return "/app/calendario";
  if (area === "aluno") return "/app/aluno";
  return `/app/${area}`;
}

export function usuarioPodeAcessarArea(me: MeResponse, area: AreaApp): boolean {
  if (area === "mapa" || area === "perfil") return true;
  if (area === "calendario") {
    return me.permissoes.areas.some((item) => item === "aluno" || item === "professor" || item === "admin");
  }
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
    children:
      area === "admin"
        ? ADMIN_CHILDREN
        : area === "aluno"
          ? ALUNO_CHILDREN
          : area === "professor"
            ? PROFESSOR_CHILDREN
            : undefined,
  }));
}

export function destinoPadrao(me: MeResponse): string {
  return pathDaArea(areaInicial(me));
}

function areaDoPath(path: string): AreaApp | null {
  if (path === "/mapa-iot" || path === "/app/mapa-iot") return "mapa";
  if (path === "/app/calendario") return "calendario";
  if (path === "/app/turmas" || path.startsWith("/app/turmas/")) return "calendario";
  if (path === "/app/aluno" || path.startsWith("/app/aluno/")) return "aluno";
  if (path === "/app/professor") return "professor";
  if (path === "/app/admin" || path.startsWith("/app/admin/")) return "admin";
  if (path === "/app/perfil") return "perfil";
  return null;
}

export function rotuloDoPath(me: MeResponse, path: string): string {
  for (const item of itensNavegacao(me)) {
    const child = item.children?.find((subitem) => subitem.path === path);
    if (child) return child.label;
    if (item.path === path) return item.label;
  }
  return "AutoPonto";
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
