import type { ButtonHTMLAttributes } from "react";

export function Botao({ children, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button {...props}>{children}</button>;
}
