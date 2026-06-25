import type { ReactNode } from "react";

type StatCardProps = {
  label: string;
  value: ReactNode;
  icon?: ReactNode;
  tone?: "teal" | "blue" | "green" | "yellow" | "red";
  subtext?: ReactNode;
};

export function StatCard({
  label,
  value,
  icon,
  tone = "teal",
  subtext,
}: StatCardProps) {
  return (
    <div className="card stat-card">
      <div className="stat">
        {icon && <div className={`stat-icon ${tone}`}>{icon}</div>}
        <div className="stat-content">
          <div className="stat-label">{label}</div>
          <div className="stat-value-row">
            <strong className="stat-value">{value}</strong>
          </div>
          {subtext && <div className="stat-subtext">{subtext}</div>}
        </div>
      </div>
    </div>
  );
}
