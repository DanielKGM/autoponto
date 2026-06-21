import { useSidebar } from "../context/SidebarContext";

export function Backdrop() {
  const { isMobileOpen, closeMobileSidebar } = useSidebar();

  if (!isMobileOpen) return null;

  return <div className="fixed inset-0 z-40 bg-gray-900/50 lg:hidden" onClick={closeMobileSidebar} />;
}
