import { useMemo } from "react";
import { useLocation } from "react-router";
import { itensNavegacao } from "../app/navigation";
import { useSession } from "../app/session";
import { ThemeToggleButton } from "../components/common/ThemeToggleButton";
import { MenuIcon } from "../components/icons";
import { UserDropdown } from "../components/header/UserDropdown";
import { useSidebar } from "../context/SidebarContext";

export function AppHeader() {
  const { toggleMobileSidebar, toggleSidebar } = useSidebar();
  const { me } = useSession();
  const location = useLocation();
  const currentLabel = useMemo(() => {
    return itensNavegacao(me).find((item) => item.path === location.pathname)?.label || "AutoPonto";
  }, [location.pathname, me]);

  function toggleMenu() {
    if (window.innerWidth > 768) {
      toggleSidebar();
    } else {
      toggleMobileSidebar();
    }
  }

  return (
    <header className="topbar">
      <div className="topbar-left">
        <button type="button" onClick={toggleMenu} aria-label="Alternar menu" className="sidebar-toggle">
          <MenuIcon />
        </button>
        <div className="breadcrumb" aria-label="Caminho atual">
          <span>AutoPonto</span>
          <span className="sep">/</span>
          <span className="current">{currentLabel}</span>
        </div>
      </div>
      <div className="topbar-right">
        <ThemeToggleButton />
        <UserDropdown />
      </div>
    </header>
  );
}
