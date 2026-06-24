import type { ReactNode } from "react";
import { NoDataIcon } from "../icons";

type EmptyStateProps = {
  title: string;
  text: string;
  action?: ReactNode;
  icon?: ReactNode;
};

export function EmptyState({
  title,
  text,
  action,
  icon = <NoDataIcon />,
}: EmptyStateProps) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">{icon}</div>
      <div className="empty-state-title">{title}</div>
      <div className="empty-state-text">{text}</div>
      {action && <div className="empty-state-actions">{action}</div>}
    </div>
  );
}
