import { useTheme } from "../../context/ThemeContext";
import { MoonIcon, SunIcon } from "../icons";

export function ThemeToggleButton() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="tb-btn theme-toggle"
      aria-label={theme === "dark" ? "Usar tema claro" : "Usar tema escuro"}
      data-tooltip={theme === "dark" ? "Usar tema claro" : "Usar tema escuro"}
    >
      {theme === "dark" ? <SunIcon /> : <MoonIcon />}
    </button>
  );
}
