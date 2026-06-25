import { describe, expect, it } from "vitest";
import { lessonDetailViewForRole } from "./lessonDetailUtils";

describe("lesson detail utils", () => {
  it("dispatches detail pages by user role", () => {
    expect(lessonDetailViewForRole("ALUNO")).toBe("ALUNO");
    expect(lessonDetailViewForRole("PROFESSOR")).toBe("PROFESSOR");
    expect(lessonDetailViewForRole("ADMINISTRADOR")).toBe("PROFESSOR");
  });
});
