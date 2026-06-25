import { EmptyState } from "../../../shared/ui/EmptyState";
import { PageMeta } from "../../../shared/ui/PageMeta";

type TeacherLessonDetailPageProps = {
  aulaId?: string;
};

export function TeacherLessonDetailPage({ aulaId }: TeacherLessonDetailPageProps) {
  return (
    <>
      <PageMeta
        title="Aula da turma | AutoPonto"
        description="Detalhe da aula para professor no AutoPonto."
      />
      <div className="page-header">
        <div className="page-pretitle">Professor</div>
        <h1 className="page-title">Aula da turma</h1>
        <p className="page-description">Esta visão exibirá chamada, status da aula e acompanhamento da turma.</p>
      </div>
      <div className="card">
        <EmptyState
          title="Detalhe do professor em construção"
          text={`A aula ${aulaId || ""} será exibida aqui na visão do professor.`}
        />
      </div>
    </>
  );
}
