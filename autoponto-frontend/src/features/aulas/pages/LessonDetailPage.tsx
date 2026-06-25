import { Link, useParams } from "react-router";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { PageMeta } from "../../../shared/ui/PageMeta";

export function LessonDetailPage() {
  const { aulaId } = useParams();

  return (
    <>
      <PageMeta
        title="Abrir aula pelo calendário | AutoPonto"
        description="A rota antiga de aula precisa do vínculo com a turma."
      />
      <div className="page-header">
        <div className="page-pretitle">Aula</div>
        <h1 className="page-title">Abra a aula pelo calendário</h1>
      </div>
      <div className="card">
        <EmptyState
          title="Link incompleto"
          text={`A aula ${aulaId || ""} precisa do identificador da turma. Acesse o calendário e selecione a aula novamente.`}
          action={(
            <Link className="btn btn-primary btn-sm" to="/app/calendario">
              Ir ao calendário
            </Link>
          )}
        />
      </div>
    </>
  );
}
