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

function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("") || "AP";
}

export function AppSidebar() {
  const { me } = useSession();
  const { isMobileOpen, closeMobileSidebar } = useSidebar();
  const location = useLocation();
  const nome = me.usuario.nome_completo || me.usuario.username;

  function isActive(path: string) {
    return location.pathname === path;
  }

  return (
    <aside
      className={`sidebar ${isMobileOpen ? "open" : ""}`}
      aria-label="Navegacao principal"
    >
      <Link to="/" onClick={closeMobileSidebar} className="sidebar-brand">
        <BrandLogo size="md" tone="onDark" />
      </Link>

      <nav className="sidebar-nav">
        <div className="nav-group">
          <div className="nav-label">Menu</div>
          <ul className="nav-list">
          {itensNavegacao(me).map((item) => (
            <li key={item.path}>
              <Link
                to={item.path}
                onClick={closeMobileSidebar}
                className={`nav-link ${isActive(item.path) ? "active" : ""}`}
                data-rail-label={item.label}
              >
                <span className="icon">
                  {icons[item.area]}
                </span>
                <span className="nav-text">{item.label}</span>
              </Link>
            </li>
          ))}
          </ul>
        </div>
      </nav>

      <div className="sidebar-footer">
        <Link to="/app/perfil" className="sidebar-user" onClick={closeMobileSidebar}>
          <span className="avatar">
            {initials(nome)}
            <span className="online" />
          </span>
          <span className="sidebar-user-info">
            <span className="name">{nome}</span>
            <span className="role">{me.usuario.papel}</span>
          </span>
        </Link>
      </div>
    </aside>
  );
}
