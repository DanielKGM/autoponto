import { describe, expect, it } from "vitest";
import type { AulaCalendario } from "../types";
import {
  buildMonthCells,
  getCalendarEventClass,
  getLessonEventClass,
  getStudentStatusClass,
  lessonDetailPath,
} from "./studentCalendarUtils";

const baseLesson: AulaCalendario = {
  aula_id: "aula-1",
  turma_id: "turma-1",
  disciplina: "Sistemas Distribuídos",
  turma: "A",
  periodo_letivo: "2026.1",
  data: "2026-06-15",
  inicio: "2026-06-15T08:00:00-03:00",
  fim: "2026-06-15T10:00:00-03:00",
  sala: "Sala 101",
  status_aula: "ABERTA",
  status_aluno: "PENDENTE",
  presenca_id: null,
  registrado_em: null,
};

describe("calendar utils", () => {
  it("builds a fixed 42-cell month grid and groups lessons by date", () => {
    const cells = buildMonthCells(2026, 5, [baseLesson]);

    expect(cells).toHaveLength(42);
    expect(cells[0]).toMatchObject({ day: 1, dateKey: "2026-06-01", currentMonth: true });
    expect(cells[14].dateKey).toBe("2026-06-15");
    expect(cells[14].lessons.map((lesson) => lesson.aula_id)).toEqual(["aula-1"]);
    expect(cells[cells.length - 1]).toMatchObject({ dateKey: "2026-07-12", currentMonth: false });
  });

  it("maps lesson status to calendar event colors", () => {
    expect(getLessonEventClass("CANCELADA")).toBe("calendar-event red");
    expect(getLessonEventClass("FECHADA")).toBe("calendar-event green");
    expect(getLessonEventClass("ABERTA")).toBe("calendar-event yellow");
    expect(getLessonEventClass("PLANEJADA")).toBe("calendar-event muted");
  });

  it("maps student status to status label colors", () => {
    expect(getStudentStatusClass("PRESENTE")).toBe("status status-green");
    expect(getStudentStatusClass("AUSENTE")).toBe("status status-red");
    expect(getStudentStatusClass("PENDENTE")).toBe("status status-muted");
    expect(getStudentStatusClass("NAO_APLICAVEL")).toBe("status status-muted");
  });

  it("uses student presence for aluno event colors", () => {
    expect(getCalendarEventClass({ ...baseLesson, status_aluno: "PRESENTE" }, "ALUNO")).toBe("calendar-event green");
    expect(getCalendarEventClass({ ...baseLesson, status_aluno: "AUSENTE" }, "ALUNO")).toBe("calendar-event red");
    expect(getCalendarEventClass({ ...baseLesson, status_aluno: "PENDENTE" }, "ALUNO")).toBe("calendar-event muted");
  });

  it("uses lesson status for professor event colors", () => {
    expect(getCalendarEventClass({ ...baseLesson, status_aula: "FECHADA", status_aluno: null }, "PROFESSOR")).toBe("calendar-event green");
    expect(getCalendarEventClass({ ...baseLesson, status_aula: "CANCELADA", status_aluno: null }, "PROFESSOR")).toBe("calendar-event red");
  });

  it("builds a stable turma/aula detail path", () => {
    expect(lessonDetailPath("turma-1", "aula-1")).toBe("/app/turmas/turma-1/aulas/aula-1");
  });
});
