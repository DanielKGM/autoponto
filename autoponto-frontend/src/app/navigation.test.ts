import { describe, expect, it } from "vitest";
import {
  areaInicial,
  destinoAposLogin,
  itensNavegacao,
  rotuloDoPath,
  usuarioPodeAcessarArea,
} from "./navigation";
import type { MeResponse } from "../types";

function me(areas: string[]): MeResponse {
  return {
    usuario: {
      id: "usuario-1",
      username: "demo",
      email: "demo@autoponto.local",
      nome_completo: "Usuario Demo",
      matricula: "2026001",
      papel: "ALUNO",
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
    expect(areaInicial(me(["aluno", "professor"]))).toBe("professor");
    expect(areaInicial(me(["aluno", "professor", "admin"]))).toBe("admin");
  });

  it("builds the sidebar from authorized areas plus public map and profile", () => {
    expect(itensNavegacao(me(["aluno", "admin"])).map((item) => item.label)).toEqual([
      "Aluno",
      "Admin",
      "Mapa IoT",
      "Perfil",
    ]);
    expect(
      itensNavegacao(me(["admin"])).find((item) => item.area === "admin")?.children?.map((item) => item.label),
    ).toEqual(["Acadêmico", "IoT"]);
  });

  it("checks protected area access without restricting map or profile", () => {
    const usuario = me(["professor"]);

    expect(usuarioPodeAcessarArea(usuario, "professor")).toBe(true);
    expect(usuarioPodeAcessarArea(usuario, "admin")).toBe(false);
    expect(usuarioPodeAcessarArea(usuario, "mapa")).toBe(true);
    expect(usuarioPodeAcessarArea(usuario, "perfil")).toBe(true);
  });

  it("respects a safe next path after sign in", () => {
    expect(destinoAposLogin(me(["professor"]), "/app/perfil")).toBe("/app/perfil");
    expect(destinoAposLogin(me(["professor"]), "https://externo.test")).toBe("/app/professor");
    expect(destinoAposLogin(me(["professor"]), "/app/admin")).toBe("/app/professor");
    expect(destinoAposLogin(me(["admin"]), "/app/admin/iot")).toBe("/app/admin/iot");
  });

  it("finds labels inside nested navigation", () => {
    expect(rotuloDoPath(me(["admin"]), "/app/admin/academico")).toBe("Acadêmico");
    expect(rotuloDoPath(me(["admin"]), "/app/admin/iot")).toBe("IoT");
  });
});
