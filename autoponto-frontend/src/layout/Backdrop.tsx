import { useSidebar } from "../context/SidebarContext";

export function Backdrop() {
  const { isMobileOpen, closeMobileSidebar } = useSidebar();

  if (!isMobileOpen) return null;

  return <div className="sidebar-backdrop" onClick={closeMobileSidebar} />;
}
