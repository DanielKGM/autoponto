import { EmptyState } from "../components/common/EmptyState";
import { PageMeta } from "../components/common/PageMeta";

export function TeacherPage() {
  return (
    <>
      <PageMeta
        title="Professor | AutoPonto"
        description="Área do professor no AutoPonto."
      />
      <div className="card">
        <EmptyState
          title="Área do professor"
          text="As próximas ferramentas do professor serão exibidas aqui."
        />
      </div>
    </>
  );
}
