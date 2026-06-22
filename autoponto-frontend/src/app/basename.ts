export function normalizarBasename(base: string): string {
  const valor = base.trim();
  if (!valor || valor === "/") return "/";

  const comBarraInicial = valor.startsWith("/") ? valor : `/${valor}`;
  return comBarraInicial.replace(/\/+$/, "");
}

export const routerBasename = normalizarBasename(import.meta.env.BASE_URL);
