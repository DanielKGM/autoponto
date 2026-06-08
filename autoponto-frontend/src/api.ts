import type { MeResponse } from "./types";

const API_URL = (import.meta.env.VITE_API_URL || "/api").replace(/\/+$/, "");
const ACCESS_KEY = "autoponto_access";
const REFRESH_KEY = "autoponto_refresh";

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(status: number, data: unknown) {
    super(typeof data === "object" && data && "detail" in data ? String((data as { detail: unknown }).detail) : "Erro na API");
    this.status = status;
    this.data = data;
  }
}

type ApiOptions = RequestInit & {
  skipAuth?: boolean;
  retryOnUnauthorized?: boolean;
};

export function getAccessToken(): string | null {
  return window.sessionStorage.getItem(ACCESS_KEY);
}

export function salvarTokens(access: string, refresh: string): void {
  window.sessionStorage.setItem(ACCESS_KEY, access);
  window.sessionStorage.setItem(REFRESH_KEY, refresh);
}

export function limparTokens(): void {
  window.sessionStorage.removeItem(ACCESS_KEY);
  window.sessionStorage.removeItem(REFRESH_KEY);
}

async function tentarRefresh(): Promise<boolean> {
  const refresh = window.sessionStorage.getItem(REFRESH_KEY);
  if (!refresh) {
    return false;
  }

  const resposta = await fetch(`${API_URL}/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!resposta.ok) {
    limparTokens();
    return false;
  }
  const dados = (await resposta.json()) as { access: string };
  window.sessionStorage.setItem(ACCESS_KEY, dados.access);
  return true;
}

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const bodyIsFormData = options.body instanceof FormData;
  if (!headers.has("Content-Type") && options.body && !bodyIsFormData) {
    headers.set("Content-Type", "application/json");
  }
  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  const token = getAccessToken();
  if (token && !options.skipAuth) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const resposta = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (resposta.status === 401 && options.retryOnUnauthorized !== false && !options.skipAuth) {
    const atualizado = await tentarRefresh();
    if (atualizado) {
      return apiFetch<T>(path, { ...options, retryOnUnauthorized: false });
    }
  }

  if (!resposta.ok) {
    let dados: unknown = null;
    try {
      dados = await resposta.json();
    } catch {
      dados = { detail: resposta.statusText };
    }
    throw new ApiError(resposta.status, dados);
  }

  if (resposta.status === 204) {
    return undefined as T;
  }
  return (await resposta.json()) as T;
}

export async function login(username: string, password: string): Promise<MeResponse> {
  const tokens = await apiFetch<{ access: string; refresh: string }>("/auth/token/", {
    method: "POST",
    skipAuth: true,
    body: JSON.stringify({ username, password }),
  });
  salvarTokens(tokens.access, tokens.refresh);
  return apiFetch<MeResponse>("/me/");
}

export function normalizarLista<T>(dados: T[] | { results: T[] }): T[] {
  return Array.isArray(dados) ? dados : dados.results;
}

export function detalheErro(erro: unknown): string {
  if (erro instanceof ApiError) {
    if (erro.status === 409) {
      return erro.message || "Conflito de dados.";
    }
    if (erro.status === 403) {
      return "Acesso negado para esta operação.";
    }
    if (erro.status === 401) {
      return "Sessão expirada. Entre novamente.";
    }
    if (erro.data && typeof erro.data === "object") {
      return JSON.stringify(erro.data);
    }
    return erro.message;
  }
  return erro instanceof Error ? erro.message : "Erro inesperado.";
}
