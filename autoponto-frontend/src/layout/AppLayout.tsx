import { Outlet } from "react-router";
import { SidebarProvider } from "../context/SidebarContext";
import { AppHeader } from "./AppHeader";
import { AppSidebar } from "./AppSidebar";
import { Backdrop } from "./Backdrop";

function LayoutContent() {
  return (
    <>
      <AppSidebar />
      <Backdrop />
      <AppHeader />
      <main className="main" id="main-content">
        <div className="page-wrapper">
          <Outlet />
        </div>
      </main>
    </>
  );
}

export function AppLayout() {
  return (
    <SidebarProvider>
      <LayoutContent />
    </SidebarProvider>
  );
}
