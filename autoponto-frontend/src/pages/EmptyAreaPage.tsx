import { PageMeta } from "../components/common/PageMeta";

type EmptyAreaPageProps = {
  title: string;
  description: string;
};

export function EmptyAreaPage({ title, description }: EmptyAreaPageProps) {
  return (
    <>
      <PageMeta title={`${title} | AutoPonto`} description={description} />
      <section className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03] lg:p-6">
        <div>
          <h1 className="text-lg font-semibold text-gray-800 dark:text-white/90">{title}</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{description}</p>
        </div>
      </section>
    </>
  );
}
