type ProgressBarProps = {
  value: number;
  tone?: "primary" | "green" | "yellow" | "red" | "blue";
};

const TONE_COLOR: Record<NonNullable<ProgressBarProps["tone"]>, string> = {
  primary: "var(--primary)",
  green: "var(--green)",
  yellow: "var(--yellow)",
  red: "var(--red)",
  blue: "var(--blue)",
};

export function ProgressBar({ value, tone = "primary" }: ProgressBarProps) {
  const width = Math.max(0, Math.min(100, value));
  return (
    <div className="progress-thin" aria-label={`${width}%`}>
      <div className="bar" style={{ width: `${width}%`, background: TONE_COLOR[tone] }} />
    </div>
  );
}
