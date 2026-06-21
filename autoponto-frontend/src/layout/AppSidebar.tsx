import { Link, useLocation } from "react-router";
import type { ReactNode } from "react";
import { BrandLogo } from "../components/common/BrandLogo";
import { AdminIcon, GraduationIcon, MapIcon, TeacherIcon, UserIcon } from "../components/icons";
import { useSession } from "../app/session";
import { itensNavegacao, type AreaApp } from "../app/navigation";
import { useSidebar } from "../context/SidebarContext";

const icons: Record<AreaApp, ReactNode> = {
  aluno: <GraduationIcon />,
  professor: <TeacherIcon />,
  admin: <AdminIcon />,
  mapa: <MapIcon />,
  perfil: <UserIcon />,
};

export function AppSidebar() {
  const { me } = useSession();
  const { isExpanded, isHovered, isMobileOpen, setIsHovered, closeMobileSidebar } = useSidebar();
  const location = useLocation();
  const expanded = isExpanded || isHovered || isMobileOpen;

  function isActive(path: string) {
    return location.pathname === path;
  }

  return (
    <aside
      className={`fixed left-0 top-0 z-50 mt-16 flex h-screen flex-col border-r border-gray-200 bg-white px-5 text-gray-900 transition-all duration-300 ease-in-out dark:border-gray-800 dark:bg-gray-900 lg:mt-0 ${
        isExpanded || isMobileOpen ? "w-[290px]" : isHovered ? "w-[290px]" : "w-[90px]"
      } ${isMobileOpen ? "translate-x-0" : "-translate-x-full"} lg:translate-x-0`}
      onMouseEnter={() => !isExpanded && setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className={`flex py-8 ${!isExpanded && !isHovered ? "lg:justify-center" : "justify-start"}`}>
        <Link to="/" onClick={closeMobileSidebar} className="block overflow-hidden">
          {expanded ? (
            <BrandLogo size="md" />
          ) : (
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-white shadow-theme-xs ring-1 ring-gray-200 dark:bg-gray-900 dark:ring-gray-800">
              <BrandLogo size="md" iconOnly />
            </span>
          )}
        </Link>
      </div>
      <div className="flex flex-col overflow-y-auto duration-300 ease-linear no-scrollbar">
        <nav className="mb-6">
          <h2 className={`mb-4 flex text-xs uppercase leading-5 text-gray-400 ${!isExpanded && !isHovered ? "lg:justify-center" : "justify-start"}`}>
          {expanded ? "Menu" : "..."}
          </h2>
          <ul className="flex flex-col gap-4">
          {itensNavegacao(me).map((item) => (
            <li key={item.path}>
              <Link
                to={item.path}
                onClick={closeMobileSidebar}
                className={`menu-item group ${isActive(item.path) ? "menu-item-active" : "menu-item-inactive"} ${
                  !isExpanded && !isHovered ? "lg:justify-center" : "lg:justify-start"
                }`}
              >
                <span className={`menu-item-icon-size ${isActive(item.path) ? "menu-item-icon-active" : "menu-item-icon-inactive"}`}>
                  {icons[item.area]}
                </span>
                {expanded && <span className="menu-item-text">{item.label}</span>}
              </Link>
            </li>
          ))}
          </ul>
        </nav>
      </div>
    </aside>
  );
}
