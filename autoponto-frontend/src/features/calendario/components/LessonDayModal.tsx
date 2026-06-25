import { useMemo } from "react";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { IconButton } from "../../../shared/ui/IconButton";
import { Modal } from "../../../shared/ui/Modal";
import { SimpleTable, type SimpleTableColumn } from "../../../shared/ui/SimpleTable";
import { ChevronRightIcon } from "../../../shared/ui/icons";
import type { AulaCalendario, CalendarioVisualizacao } from "../../../shared/types";
import {
  formatTimeRange,
  getLessonEventClass,
  getStudentStatusClass,
  LESSON_STATUS_LABELS,
  STUDENT_STATUS_LABELS,
} from "../../../shared/domain/studentCalendarUtils";

type LessonDayModalProps = {
  dateLabel: string;
  lessons: AulaCalendario[];
  visualizacao: CalendarioVisualizacao;
  open: boolean;
  onClose: () => void;
  onOpenLesson: (lesson: AulaCalendario) => void;
};

export function lessonDayColumnKeys(
  visualizacao: CalendarioVisualizacao,
): string[] {
  if (visualizacao === "ALUNO") {
    return [
      "disciplina",
      "horario",
      "sala",
      "status_aula",
      "status_aluno",
      "acao",
    ];
  }
  return ["disciplina", "turma", "horario", "sala", "status_aula", "acao"];
}

export function LessonDayModal({
  dateLabel,
  lessons,
  visualizacao,
  open,
  onClose,
  onOpenLesson,
}: LessonDayModalProps) {
  const columns = useMemo<SimpleTableColumn<AulaCalendario>[]>(
    () =>
      lessonDayColumnKeys(visualizacao).map((key) => ({
        key,
        ...columnByKey(key, onOpenLesson),
      })),
    [onOpenLesson, visualizacao],
  );

  return (
    <Modal open={open} title={dateLabel} size="lg" onClose={onClose}>
      <SimpleTable
        columns={columns}
        rows={lessons}
        rowKey={(lesson) => lesson.aula_id}
        emptyState={
          <EmptyState
            title="Nenhuma aula"
            text="Não há aulas registradas para este dia."
          />
        }
      />
    </Modal>
  );
}

function columnByKey(
  key: string,
  onOpenLesson: (lesson: AulaCalendario) => void,
): Omit<SimpleTableColumn<AulaCalendario>, "key"> {
  const columns: Record<
    string,
    Omit<SimpleTableColumn<AulaCalendario>, "key">
  > = {
    disciplina: {
      label: "Disciplina",
      render: (lesson) => (
        <div>
          <span className="cell-strong">{lesson.disciplina}</span>
          <div className="lesson-table-subtext">Turma {lesson.turma}</div>
        </div>
      ),
    },
    horario: {
      label: "Horário",
      render: (lesson) => formatTimeRange(lesson.inicio, lesson.fim),
    },
    turma: {
      label: "Turma",
    },
    sala: {
      label: "Sala",
      align: "center",
    },
    status_aula: {
      label: "Aula",
      align: "center",
      render: (lesson) => (
        <span className={getLessonEventClass(lesson.status_aula)}>
          {LESSON_STATUS_LABELS[lesson.status_aula]}
        </span>
      ),
    },
    status_aluno: {
      label: "Presença",
      align: "center",
      render: (lesson) =>
        lesson.status_aluno ? (
          <span className={getStudentStatusClass(lesson.status_aluno)}>
            {STUDENT_STATUS_LABELS[lesson.status_aluno]}
          </span>
        ) : (
          "-"
        ),
    },
    acao: {
      label: "",
      align: "center",
      className: "lesson-day-action-cell",
      width: "56px",
      render: (lesson) => (
        <span className="lesson-day-action">
          <IconButton
            label={`Abrir ${lesson.disciplina}`}
            icon={<ChevronRightIcon />}
            showTooltip={false}
            onClick={() => onOpenLesson(lesson)}
          />
        </span>
      ),
    },
  };
  return columns[key];
}
