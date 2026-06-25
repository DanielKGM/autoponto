import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

type SidebarContextType = {
  isRail: boolean;
  isMobileOpen: boolean;
  toggleSidebar: () => void;
  toggleMobileSidebar: () => void;
  closeMobileSidebar: () => void;
};

const SidebarContext = createContext<SidebarContextType | undefined>(undefined);

function initialRailMode(): boolean {
  if (typeof window === "undefined") return false;
  return localStorage.getItem("sidebar-rail") === "true";
}

export function SidebarProvider({ children }: { children: ReactNode }) {
  const [isRail, setIsRail] = useState(initialRailMode);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  useEffect(() => {
    localStorage.setItem("sidebar-rail", String(isRail));
    document.body.classList.toggle("sidebar-rail", isRail);
  }, [isRail]);

  useEffect(() => {
    document.body.classList.toggle("sidebar-open", isMobileOpen);
    return () => document.body.classList.remove("sidebar-open");
  }, [isMobileOpen]);

  useEffect(() => {
    function handleResize() {
      if (window.innerWidth > 768) setIsMobileOpen(false);
    }
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <SidebarContext.Provider
      value={{
        isMobileOpen,
        isRail,
        toggleSidebar: () => setIsRail((current) => !current),
        toggleMobileSidebar: () => setIsMobileOpen((current) => !current),
        closeMobileSidebar: () => setIsMobileOpen(false),
      }}
    >
      {children}
    </SidebarContext.Provider>
  );
}

export function useSidebar() {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error("useSidebar must be used within SidebarProvider");
  }
  return context;
}
