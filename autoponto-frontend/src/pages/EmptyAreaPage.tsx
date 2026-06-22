import { PageMeta } from "../components/common/PageMeta";

type EmptyAreaPageProps = {
  title: string;
  description: string;
};

export function EmptyAreaPage({ title, description }: EmptyAreaPageProps) {
  return (
    <>
      <PageMeta title={`${title} | AutoPonto`} description={description} />
      <div className="page-header">
        <div className="page-pretitle">Area</div>
        <h1 className="page-title">{title}</h1>
      </div>
      <section className="card">
        <div className="card-body empty-card">
          <div>
            <div className="empty-card-title">{title}</div>
            <p className="empty-card-description">{description}</p>
          </div>
        </div>
      </section>
    </>
  );
}
