import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router";
import { apiFetch, detalheErro } from "../../../shared/api";
import { useSession } from "../../../shared/session";
import { LessonDayModal } from "../components/LessonDayModal";
import { LessonMonthCalendar } from "../components/LessonMonthCalendar";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { PageMeta } from "../../../shared/ui/PageMeta";
import { Button } from "../../../shared/ui/Button";
import type {
  AulaCalendario,
  CalendarioAulasResponse,
  CalendarioVisualizacao,
} from "../../../shared/types";
import { lessonDetailPath, monthRange } from "../../../shared/domain/studentCalendarUtils";

function currentMonthStart() {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), 1);
}

function dateLabel(dateKey: string | null) {
  if (!dateKey) return "";
  const [year, month, day] = dateKey.split("-").map(Number);
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "full",
  }).format(new Date(year, month - 1, day));
}

function fallbackVisualizacao(papel: string): CalendarioVisualizacao {
  return papel === "ALUNO" ? "ALUNO" : "PROFESSOR";
}

export function LessonCalendarPage() {
  const { me } = useSession();
  const navigate = useNavigate();
  const [visibleMonth, setVisibleMonth] = useState(currentMonthStart);
  const [calendar, setCalendar] = useState<CalendarioAulasResponse | null>(
    null,
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const year = visibleMonth.getFullYear();
  const month = visibleMonth.getMonth();
  const lessons = calendar?.aulas ?? [];
  const visualizacao =
    calendar?.visualizacao ?? fallbackVisualizacao(me.usuario.papel);

  useEffect(() => {
    let active = true;
    const range = monthRange(year, month);
    setLoading(true);
    setError("");

    apiFetch<CalendarioAulasResponse>(
      `/me/calendario-aulas/?inicio=${range.inicio}&fim=${range.fim}`,
    )
      .then((response) => {
        if (active) setCalendar(response);
      })
      .catch((err) => {
        if (active) {
          setCalendar(null);
          setError(detalheErro(err));
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [month, year]);

  const selectedLessons = useMemo(
    () => lessons.filter((lesson) => lesson.data === selectedDate),
    [lessons, selectedDate],
  );

  function changeMonth(offset: number) {
    setVisibleMonth(
      (current) =>
        new Date(current.getFullYear(), current.getMonth() + offset, 1),
    );
    setSelectedDate(null);
  }

  function openLesson(lesson: AulaCalendario) {
    navigate(lessonDetailPath(lesson.turma_id, lesson.aula_id));
  }

  return (
    <>
      <PageMeta
        title="Calendário de aulas | AutoPonto"
        description="Calendário mensal de aulas."
      />
      <div className="page-header">
        <div className="page-header-row">
          <div>
            <div className="page-pretitle">Aulas</div>
            <h1 className="page-title">Calendário de aulas</h1>
            <p className="page-description">
              Acompanhe as aulas do mês conforme seu vínculo acadêmico.
            </p>
          </div>
          <div className="page-actions">
            <Button
              variant="secondary"
              onClick={() => {
                setVisibleMonth(currentMonthStart());
                setSelectedDate(null);
              }}
            >
              Hoje
            </Button>
          </div>
        </div>
      </div>

      {loading && (
        <div className="alert alert-info">Carregando aulas do mês...</div>
      )}
      {error && <div className="alert alert-error">{error}</div>}

      {!loading && !error && lessons.length === 0 && (
        <div className="calendar-empty-panel">
          <EmptyState
            title="Nenhuma aula no mês"
            text="Quando houver aulas cadastradas para o período, elas aparecerão no calendário."
          />
        </div>
      )}

      <LessonMonthCalendar
        year={year}
        month={month}
        lessons={lessons}
        visualizacao={visualizacao}
        onNextMonth={() => changeMonth(1)}
        onOpenLesson={openLesson}
        onPreviousMonth={() => changeMonth(-1)}
        onSelectDate={setSelectedDate}
      />

      <LessonDayModal
        dateLabel={dateLabel(selectedDate)}
        lessons={selectedLessons}
        visualizacao={visualizacao}
        open={selectedDate !== null}
        onClose={() => setSelectedDate(null)}
        onOpenLesson={openLesson}
      />
    </>
  );
}
