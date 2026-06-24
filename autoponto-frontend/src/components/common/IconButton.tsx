import type { ButtonHTMLAttributes, ReactNode } from "react";

type IconButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  label: string;
  icon: ReactNode;
  variant?: "default" | "danger" | "success" | "primary";
};

export function IconButton({
  label,
  icon,
  variant = "default",
  className = "",
  ...props
}: IconButtonProps) {
  const variantClass = variant === "default" ? "" : `card-opt-btn-${variant}`;
  return (
    <button
      type="button"
      aria-label={label}
      data-tooltip={label}
      className={`card-opt-btn ${variantClass} ${className}`.trim()}
      {...props}
    >
      {icon}
    </button>
  );
}
