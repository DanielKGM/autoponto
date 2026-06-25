import type {
  AulaStatus,
  StatusAlunoCalendario,
  StatusAlunoResumo,
} from "../types";
import {
  getStudentStatusClass,
  LESSON_STATUS_LABELS,
  STUDENT_STATUS_LABELS,
} from "./studentCalendarUtils";

export const SUMMARY_STATUS_LABELS: Record<StatusAlunoResumo, string> = {
  PRESENTE: "Presente",
  AUSENTE: "Ausente",
  PENDENTE: "Pendente",
};

export function statusAlunoClass(
  status: StatusAlunoResumo | StatusAlunoCalendario,
): string {
  return getStudentStatusClass(status as StatusAlunoCalendario);
}

export function statusAlunoLabel(
  status: StatusAlunoResumo | StatusAlunoCalendario,
): string {
  return (
    STUDENT_STATUS_LABELS[status as StatusAlunoCalendario] ||
    SUMMARY_STATUS_LABELS[status as StatusAlunoResumo]
  );
}

export function statusAulaClass(status: AulaStatus): string {
  const color = {
    PLANEJADA: "muted",
    ABERTA: "yellow",
    FECHADA: "green",
    CANCELADA: "red",
  }[status];
  return `status status-${color}`;
}

export function statusAulaLabel(status: AulaStatus): string {
  return LESSON_STATUS_LABELS[status];
}

export function formatDate(value: string): string {
  const [year, month, day] = value.split("-").map(Number);
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short" }).format(
    new Date(year, month - 1, day),
  );
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "-";
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

export function percentText(value: number): string {
  return `${Number.isFinite(value) ? value.toFixed(1).replace(".0", "") : "0"}%`;
}
