import type { KeyboardEvent } from "react";
import { IconButton } from "../../../shared/ui/IconButton";
import { ChevronRightIcon } from "../../../shared/ui/icons";
import type {
  AulaCalendario,
  CalendarioVisualizacao,
} from "../../../shared/types";
import {
  buildMonthCells,
  getCalendarEventClass,
} from "../../../shared/domain/studentCalendarUtils";

const WEEKDAYS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];

type LessonMonthCalendarProps = {
  year: number;
  month: number;
  lessons: AulaCalendario[];
  visualizacao: CalendarioVisualizacao;
  onNextMonth: () => void;
  onOpenLesson: (lesson: AulaCalendario) => void;
  onPreviousMonth: () => void;
  onSelectDate: (dateKey: string) => void;
};

function monthTitle(year: number, month: number) {
  return new Intl.DateTimeFormat("pt-BR", {
    month: "long",
    year: "numeric",
  }).format(new Date(year, month, 1));
}

function activateDate(
  event: KeyboardEvent<HTMLDivElement>,
  callback: () => void,
) {
  if (event.key !== "Enter" && event.key !== " ") return;
  event.preventDefault();
  callback();
}

export function LessonMonthCalendar({
  year,
  month,
  lessons,
  visualizacao,
  onNextMonth,
  onOpenLesson,
  onPreviousMonth,
  onSelectDate,
}: LessonMonthCalendarProps) {
  const cells = buildMonthCells(year, month, lessons);

  return (
    <section className="card calendar-card" aria-label="Calendário de aulas">
      <div className="calendar-toolbar">
        <div className="nav-btns">
          <IconButton
            label="Mês anterior"
            icon={<ChevronRightIcon className="calendar-prev-icon" />}
            onClick={onPreviousMonth}
          />
          <IconButton
            label="Próximo mês"
            icon={<ChevronRightIcon />}
            onClick={onNextMonth}
          />
        </div>
        <div className="calendar-month">{monthTitle(year, month)}</div>
        <div className="spacer" />
      </div>
      <div className="calendar-scroll">
        <div className="calendar-grid">
          {WEEKDAYS.map((weekday) => (
            <div className="dow" key={weekday}>
              {weekday}
            </div>
          ))}
          {cells.map((cell) => {
            const className = [
              "calendar-day",
              !cell.currentMonth ? "muted" : "",
              cell.today ? "today" : "",
            ]
              .filter(Boolean)
              .join(" ");
            const openDay = () => {
              if (cell.currentMonth) onSelectDate(cell.dateKey);
            };

            return (
              <div
                aria-label={`Dia ${cell.day}`}
                className={className}
                key={cell.dateKey}
                onClick={openDay}
                onKeyDown={(event) => activateDate(event, openDay)}
                role={cell.currentMonth ? "button" : undefined}
                tabIndex={cell.currentMonth ? 0 : undefined}
              >
                <span className="day-num">{cell.day}</span>
                {cell.lessons.map((lesson) => (
                  <button
                    className={getCalendarEventClass(lesson, visualizacao)}
                    key={lesson.aula_id}
                    onClick={(event) => {
                      event.stopPropagation();
                      onOpenLesson(lesson);
                    }}
                    type="button"
                  >
                    {lesson.disciplina}
                  </button>
                ))}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
