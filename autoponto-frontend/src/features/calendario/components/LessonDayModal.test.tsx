import { describe, expect, it } from "vitest";
import { lessonDayColumnKeys } from "./LessonDayModal";

describe("LessonDayModal", () => {
  it("uses student-focused status columns for aluno view", () => {
    expect(lessonDayColumnKeys("ALUNO")).toEqual([
      "disciplina",
      "horario",
      "sala",
      "status_aula",
      "status_aluno",
      "acao",
    ]);
  });

  it("uses class status columns for professor view", () => {
    expect(lessonDayColumnKeys("PROFESSOR")).toEqual([
      "disciplina",
      "turma",
      "horario",
      "sala",
      "status_aula",
      "acao",
    ]);
  });
});
