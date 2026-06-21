import { PageMeta } from "../components/common/PageMeta";
import { useSession } from "../app/session";

export function ProfilePage() {
  const { me } = useSession();
  const fields = [
    ["Usuario", me.usuario.username],
    ["Nome", me.usuario.nome_completo || "-"],
    ["Papel", me.usuario.papel],
    ["Matricula", me.usuario.matricula || "-"],
    ["Email", me.usuario.email || "-"],
  ];

  return (
    <>
      <PageMeta title="Perfil | AutoPonto" description="Perfil do usuario autenticado." />
      <section className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03] lg:p-6">
        <h1 className="mb-6 text-lg font-semibold text-gray-800 dark:text-white/90">Perfil</h1>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {fields.map(([label, value]) => (
            <div key={label} className="rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-white/[0.03]">
              <span className="text-xs font-semibold uppercase tracking-wide text-gray-400">{label}</span>
              <strong className="mt-2 block break-words text-sm font-semibold text-gray-800 dark:text-white/90">{value}</strong>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
