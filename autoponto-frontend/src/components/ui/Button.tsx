import type { ButtonHTMLAttributes, ReactNode } from "react";
import { twMerge } from "tailwind-merge";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: "primary" | "secondary" | "ghost";
};

const variants = {
  primary: "bg-brand-500 text-white hover:bg-brand-600 focus:ring-brand-500/20",
  secondary:
    "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 focus:ring-gray-500/10 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-white/5",
  ghost:
    "text-gray-600 hover:bg-gray-100 hover:text-gray-800 focus:ring-gray-500/10 dark:text-gray-300 dark:hover:bg-white/5 dark:hover:text-white",
};

export function Button({ children, className, variant = "primary", type = "button", ...props }: ButtonProps) {
  return (
    <button
      type={type}
      className={twMerge(
        "inline-flex min-h-11 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium shadow-theme-xs transition focus:outline-none focus:ring-4 disabled:cursor-not-allowed disabled:opacity-60",
        variants[variant],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
