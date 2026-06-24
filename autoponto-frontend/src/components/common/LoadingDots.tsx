type LoadingDotsProps = {
  label?: string;
};

export function LoadingDots({ label }: LoadingDotsProps) {
  return (
    <span className="loading-dots-wrap">
      {label && <span>{label}</span>}
      <span className="spinner-dots" aria-hidden="true">
        <span />
        <span />
        <span />
      </span>
    </span>
  );
}
