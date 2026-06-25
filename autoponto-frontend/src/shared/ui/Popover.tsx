import type { ReactNode } from "react";

type PopoverProps = {
  children: ReactNode;
  title: string;
  text: string;
  className?: string;
};

export function Popover({ children, title, text, className }: PopoverProps) {
  return (
    <span className={`popover-trigger ${className || ""}`.trim()} tabIndex={0}>
      {children}
      <span className="popover-content">
        <span className="popover-title">{title}</span>
        <span className="popover-text">{text}</span>
      </span>
    </span>
  );
}
