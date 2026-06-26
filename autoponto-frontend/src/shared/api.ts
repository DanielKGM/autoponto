import type { MeResponse } from "./types";

const API_URL_ENV = import.meta.env.VITE_API_URL;
if (!API_URL_ENV) {
  throw new Error("VITE_API_URL obrigatoria no .env da raiz.");
}
const API_URL = API_URL_ENV.replace(/\/+$/, "");
let accessToken: string | null = null;

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(status: number, data: unknown) {
    super(
      typeof data === "object" && data && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : "Erro na API",
    );
    this.status = status;
    this.data = data;
  }
}

type ApiOptions = RequestInit & {
  skipAuth?: boolean;
  retryOnUnauthorized?: boolean;
};

export type ListaApi<T> =
  | T[]
  | {
      count?: number;
      next?: string | null;
      previous?: string | null;
      results: T[];
    };

export function getAccessToken(): string | null {
  return accessToken;
}

export function salvarAccessToken(access: string): void {
  accessToken = access;
}

export function limparTokens(): void {
  accessToken = null;
}

async function tentarRefresh(): Promise<boolean> {
  const resposta = await fetch(`${API_URL}/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({}),
  });
  if (!resposta.ok) {
    limparTokens();
    return false;
  }
  const dados = (await resposta.json()) as { access: string };
  salvarAccessToken(dados.access);
  return true;
}

export async function apiFetch<T>(
  path: string,
  options: ApiOptions = {},
): Promise<T> {
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
    credentials: "include",
  });

  if (
    resposta.status === 401 &&
    options.retryOnUnauthorized !== false &&
    !options.skipAuth
  ) {
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

export function apiPathFromUrl(
  value: string | null | undefined,
): string | null {
  if (!value) return null;
  const fallbackOrigin =
    typeof window === "undefined" ? "http://localhost" : window.location.origin;
  const url = new URL(value, fallbackOrigin);
  let basePath = "";
  try {
    basePath = new URL(API_URL, fallbackOrigin).pathname.replace(/\/+$/, "");
  } catch {
    basePath = API_URL.startsWith("/") ? API_URL.replace(/\/+$/, "") : "";
  }
  const pathname =
    basePath && url.pathname.startsWith(`${basePath}/`)
      ? url.pathname.slice(basePath.length)
      : url.pathname;
  return `${pathname}${url.search}`;
}

export async function login(
  username: string,
  password: string,
): Promise<MeResponse> {
  const tokens = await apiFetch<{ access: string }>("/auth/token/", {
    method: "POST",
    skipAuth: true,
    body: JSON.stringify({ username, password }),
  });
  salvarAccessToken(tokens.access);
  try {
    return await apiFetch<MeResponse>("/me/");
  } catch (erro) {
    await logout();
    throw erro;
  }
}

export async function carregarSessaoAutenticada(): Promise<MeResponse | null> {
  if (!getAccessToken()) {
    const atualizado = await tentarRefresh();
    if (!atualizado) {
      return null;
    }
  }
  return apiFetch<MeResponse>("/me/");
}

export async function logout(): Promise<void> {
  try {
    await apiFetch<void>("/auth/logout/", {
      method: "POST",
      retryOnUnauthorized: false,
    });
  } catch {
    // A sessão local deve sumir mesmo se o cookie já tiver expirado.
  } finally {
    limparTokens();
  }
}

export function normalizarLista<T>(dados: ListaApi<T>): T[] {
  return Array.isArray(dados) ? dados : dados.results;
}

export function detalheErro(erro: unknown): string {
  if (erro instanceof ApiError) {
    if (erro.status === 409) {
      return erro.message || "Conflito de dados.";
    }
    if (erro.status === 403) {
      return "Autenticação incorreta.";
    }
    if (erro.status === 401) {
      return "Sessao expirada. Entre novamente.";
    }
    if (erro.status === 400) {
      return (
        erro.message ||
        "Dados invalidos. Revise as informacoes e tente novamente."
      );
    }
    if (erro.status === 413) {
      return "Envio muito grande. Reduza a quantidade ou o tamanho das imagens e tente novamente.";
    }
    return erro.message || "Falha ao processar a solicitacao.";
  }
  return erro instanceof Error ? erro.message : "Erro inesperado.";
}
