import { Helmet } from "react-helmet-async";

type PageMetaProps = {
  title: string;
  description?: string;
};

export function PageMeta({ title, description = "AutoPonto" }: PageMetaProps) {
  return (
    <Helmet>
      <title>{title}</title>
      <meta name="description" content={description} />
    </Helmet>
  );
}
