import { describe, expect, it } from "vitest";
import {
  areaInicial,
  destinoAposLogin,
  itensNavegacao,
  rotuloDoPath,
  usuarioPodeAcessarArea,
} from "./navigation";
import type { MeResponse } from "../shared/types";

function me(areas: string[], papel: MeResponse["usuario"]["papel"] = "ALUNO"): MeResponse {
  return {
    usuario: {
      id: "usuario-1",
      username: "demo",
      email: "demo@autoponto.local",
      nome_completo: "Usuário Demo",
      matricula: "2026001",
      papel,
    },
    permissoes: {
      areas,
      pode_administrar: areas.includes("admin"),
      pode_emitir_relatorios: areas.includes("professor"),
      pode_cadastrar_biometria_propria: areas.includes("aluno"),
    },
  };
}

describe("navigation rules", () => {
  it("prioritizes admin, then professor, then aluno as the initial area", () => {
    expect(areaInicial(me(["aluno"]))).toBe("aluno");
    expect(areaInicial(me(["aluno", "professor"], "PROFESSOR"))).toBe("professor");
    expect(areaInicial(me(["aluno", "professor", "admin"], "ADMINISTRADOR"))).toBe("admin");
  });

  it("builds dashboards and calendar inside student and teacher menus", () => {
    expect(itensNavegacao(me(["aluno", "admin"], "ADMINISTRADOR")).map((item) => item.label)).toEqual([
      "Aluno",
      "Admin",
      "Mapa IoT",
      "Perfil",
    ]);
    expect(
      itensNavegacao(me(["aluno"])).find((item) => item.area === "aluno")?.children?.map((item) => item.label),
    ).toEqual(["Dashboard", "Calendário", "Biometria"]);
    expect(
      itensNavegacao(me(["professor"], "PROFESSOR"))
        .find((item) => item.area === "professor")
        ?.children?.map((item) => item.label),
    ).toEqual(["Dashboard", "Calendário"]);
    expect(itensNavegacao(me(["aluno"])).find((item) => item.area === "aluno")?.path).toBe("/app/aluno");
    expect(itensNavegacao(me(["aluno"])).find((item) => item.area === "calendario")).toBeUndefined();
    expect(
      itensNavegacao(me(["admin"], "ADMINISTRADOR")).find((item) => item.area === "admin")?.children?.map((item) => item.label),
    ).toEqual(["Acadêmico", "IoT"]);
  });

  it("checks protected area access without restricting calendar, map or profile", () => {
    const usuario = me(["professor"], "PROFESSOR");

    expect(usuarioPodeAcessarArea(usuario, "professor")).toBe(true);
    expect(usuarioPodeAcessarArea(usuario, "admin")).toBe(false);
    expect(usuarioPodeAcessarArea(usuario, "calendario")).toBe(true);
    expect(usuarioPodeAcessarArea(usuario, "mapa")).toBe(true);
    expect(usuarioPodeAcessarArea(usuario, "perfil")).toBe(true);
  });

  it("respects a safe next path after sign in", () => {
    expect(destinoAposLogin(me(["professor"], "PROFESSOR"), "/app/perfil")).toBe("/app/perfil");
    expect(destinoAposLogin(me(["professor"], "PROFESSOR"), "/app/calendario")).toBe("/app/calendario");
    expect(destinoAposLogin(me(["professor"], "PROFESSOR"), "/app/turmas/turma-1/aulas/aula-1")).toBe("/app/turmas/turma-1/aulas/aula-1");
    expect(destinoAposLogin(me(["professor"], "PROFESSOR"), "https://externo.test")).toBe("/app/professor");
    expect(destinoAposLogin(me(["professor"], "PROFESSOR"), "/app/admin")).toBe("/app/professor");
    expect(destinoAposLogin(me(["aluno"]), "/app/calendario")).toBe("/app/calendario");
    expect(destinoAposLogin(me(["aluno"]))).toBe("/app/aluno");
    expect(destinoAposLogin(me(["aluno"]), "/app/aluno/biometria")).toBe("/app/aluno/biometria");
    expect(destinoAposLogin(me(["admin"], "ADMINISTRADOR"), "/app/admin/iot")).toBe("/app/admin/iot");
  });

  it("finds labels inside nested navigation", () => {
    expect(rotuloDoPath(me(["aluno"]), "/app/calendario")).toBe("Calendário");
    expect(rotuloDoPath(me(["aluno"]), "/app/aluno")).toBe("Dashboard");
    expect(rotuloDoPath(me(["aluno"]), "/app/aluno/biometria")).toBe("Biometria");
    expect(rotuloDoPath(me(["admin"], "ADMINISTRADOR"), "/app/admin/academico")).toBe("Acadêmico");
    expect(rotuloDoPath(me(["admin"], "ADMINISTRADOR"), "/app/admin/iot")).toBe("IoT");
  });
});
