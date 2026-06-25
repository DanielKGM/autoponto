import type { PapelUsuario } from "../../shared/types";

export type LessonDetailView = "ALUNO" | "PROFESSOR";

export function lessonDetailViewForRole(role: PapelUsuario): LessonDetailView {
  return role === "ALUNO" ? "ALUNO" : "PROFESSOR";
}
