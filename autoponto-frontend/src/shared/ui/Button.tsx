import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: "primary" | "secondary" | "ghost";
};

const variants = {
  primary: "btn-primary",
  secondary: "btn-outline",
  ghost: "btn-ghost",
};

export function Button({ children, className, variant = "primary", type = "button", ...props }: ButtonProps) {
  return (
    <button
      type={type}
      className={["btn", variants[variant], className].filter(Boolean).join(" ")}
      {...props}
    >
      {children}
    </button>
  );
}
