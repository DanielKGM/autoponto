import type {
  AulaCalendario,
  AulaStatus,
  CalendarioVisualizacao,
  StatusAlunoCalendario,
} from "../types";

export type CalendarCell = {
  date: Date;
  dateKey: string;
  day: number;
  currentMonth: boolean;
  today: boolean;
  lessons: AulaCalendario[];
};

export const LESSON_STATUS_LABELS: Record<AulaStatus, string> = {
  PLANEJADA: "Planejada",
  ABERTA: "Aberta",
  FECHADA: "Fechada",
  CANCELADA: "Cancelada",
};

export const STUDENT_STATUS_LABELS: Record<StatusAlunoCalendario, string> = {
  PRESENTE: "Presente",
  AUSENTE: "Ausente",
  PENDENTE: "Pendente",
  NAO_APLICAVEL: "Não aplicável",
};

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

export function dateKey(year: number, month: number, day: number): string {
  return `${year}-${pad(month + 1)}-${pad(day)}`;
}

function keyFromDate(value: Date): string {
  return dateKey(value.getFullYear(), value.getMonth(), value.getDate());
}

export function monthRange(
  year: number,
  month: number,
): { inicio: string; fim: string } {
  return {
    inicio: dateKey(year, month, 1),
    fim: dateKey(year, month, new Date(year, month + 1, 0).getDate()),
  };
}

export function buildMonthCells(
  year: number,
  month: number,
  lessons: AulaCalendario[],
  today = new Date(),
): CalendarCell[] {
  const first = new Date(year, month, 1);
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const leading = (first.getDay() + 6) % 7;
  const todayKey = keyFromDate(today);
  const lessonsByDate = lessons.reduce<Map<string, AulaCalendario[]>>(
    (map, lesson) => {
      const list = map.get(lesson.data) || [];
      list.push(lesson);
      map.set(lesson.data, list);
      return map;
    },
    new Map(),
  );

  return Array.from({ length: 42 }, (_, index) => {
    const dayOffset = index - leading + 1;
    const cellDate = new Date(year, month, dayOffset);
    const cellKey = keyFromDate(cellDate);
    return {
      date: cellDate,
      dateKey: cellKey,
      day: cellDate.getDate(),
      currentMonth: dayOffset >= 1 && dayOffset <= daysInMonth,
      today: cellKey === todayKey,
      lessons: lessonsByDate.get(cellKey) || [],
    };
  });
}

export function getLessonEventClass(status: AulaStatus): string {
  const color = {
    CANCELADA: "red",
    FECHADA: "green",
    ABERTA: "yellow",
    PLANEJADA: "muted",
  }[status];
  return `calendar-event ${color}`;
}

export function getStudentStatusClass(status: StatusAlunoCalendario): string {
  const color = {
    PRESENTE: "green",
    AUSENTE: "red",
    PENDENTE: "muted",
    NAO_APLICAVEL: "muted",
  }[status];
  return `status status-${color}`;
}

export function getStudentEventClass(status: StatusAlunoCalendario): string {
  const color = {
    PRESENTE: "green",
    AUSENTE: "red",
    PENDENTE: "muted",
    NAO_APLICAVEL: "muted",
  }[status];
  return `calendar-event ${color}`;
}

export function getCalendarEventClass(
  lesson: AulaCalendario,
  visualizacao: CalendarioVisualizacao,
): string {
  if (visualizacao === "ALUNO" && lesson.status_aluno) {
    return getStudentEventClass(lesson.status_aluno);
  }
  return getLessonEventClass(lesson.status_aula);
}

export function lessonDetailPath(turmaId: string, aulaId: string): string {
  return `/app/turmas/${turmaId}/aulas/${aulaId}`;
}

export function turmaPath(turmaId: string): string {
  return `/app/turmas/${turmaId}`;
}

export function formatTimeRange(start: string, end: string): string {
  const formatter = new Intl.DateTimeFormat("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
  });
  return `${formatter.format(new Date(start))} - ${formatter.format(new Date(end))}`;
}
