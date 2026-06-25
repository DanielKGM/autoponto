import { EmptyState } from "../../../shared/ui/EmptyState";
import { PageMeta } from "../../../shared/ui/PageMeta";

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
