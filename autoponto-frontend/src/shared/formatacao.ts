export function hojeIso(): string {
  return new Date().toISOString().slice(0, 10);
}

export function formatarData(valor: string): string {
  return new Intl.DateTimeFormat("pt-BR", { timeZone: "UTC" }).format(new Date(`${valor}T00:00:00Z`));
}

export function formatarHora(valor: string): string {
  return new Intl.DateTimeFormat("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(valor));
}
