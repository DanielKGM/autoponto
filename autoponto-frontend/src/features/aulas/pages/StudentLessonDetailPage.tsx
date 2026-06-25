import { EmptyState } from "../../../shared/ui/EmptyState";
import { PageMeta } from "../../../shared/ui/PageMeta";

type StudentLessonDetailPageProps = {
  aulaId?: string;
};

export function StudentLessonDetailPage({ aulaId }: StudentLessonDetailPageProps) {
  return (
    <>
      <PageMeta
        title="Minha aula | AutoPonto"
        description="Detalhe da aula para o aluno no AutoPonto."
      />
      <div className="page-header">
        <div className="page-pretitle">Aluno</div>
        <h1 className="page-title">Minha aula</h1>
        <p className="page-description">Esta visão exibirá presença, situação da aula e informações rápidas do aluno.</p>
      </div>
      <div className="card">
        <EmptyState
          title="Detalhe do aluno em construção"
          text={`A aula ${aulaId || ""} será exibida aqui na visão do aluno.`}
        />
      </div>
    </>
  );
}
