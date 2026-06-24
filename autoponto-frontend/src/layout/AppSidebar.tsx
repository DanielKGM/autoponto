import { Link, useLocation, useNavigate } from "react-router";
import { useState, type ReactNode } from "react";
import { BrandLogo } from "../components/common/BrandLogo";
import { PopoverMenu, type PopoverMenuItem } from "../components/common/PopoverMenu";
import { AdminIcon, ChevronRightIcon, GraduationIcon, MapIcon, TeacherIcon, UserIcon } from "../components/icons";
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

const SUBMENU_STATE_KEY = "autoponto:nav-open";

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
  const { isMobileOpen, isRail, closeMobileSidebar } = useSidebar();
  const location = useLocation();
  const navigate = useNavigate();
  const [openTree, setOpenTree] = useState<string | false | null>(() => {
    if (typeof window === "undefined") return null;
    const stored = sessionStorage.getItem(SUBMENU_STATE_KEY);
    if (stored === "__closed") return false;
    return stored;
  });
  const [flyout, setFlyout] = useState<{
    anchor: HTMLElement;
    items: PopoverMenuItem[];
  } | null>(null);
  const nome = me.usuario.nome_completo || me.usuario.username;

  function isActive(path: string) {
    return location.pathname === path;
  }

  function isTreeOpen(itemPath: string, hasActiveChild: boolean) {
    return openTree === null ? hasActiveChild : openTree === itemPath;
  }

  function setStoredOpenTree(next: string | false | null) {
    setOpenTree(next);
    if (next === false) {
      sessionStorage.setItem(SUBMENU_STATE_KEY, "__closed");
    } else if (next) {
      sessionStorage.setItem(SUBMENU_STATE_KEY, next);
    } else {
      sessionStorage.removeItem(SUBMENU_STATE_KEY);
    }
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
            {itensNavegacao(me).map((item) => {
              const hasChildren = Boolean(item.children?.length);
              const hasActiveChild = Boolean(item.children?.some((child) => isActive(child.path)));
              const treeOpen = isTreeOpen(item.path, hasActiveChild);

              if (hasChildren) {
                return (
                  <li
                    key={item.path}
                    className={`nav-tree ${treeOpen ? "open" : ""} ${hasActiveChild ? "has-active" : ""}`}
                  >
                    <button
                      type="button"
                      className="nav-link nav-toggle"
                      data-rail-label={item.label}
                      aria-expanded={treeOpen}
                      onClick={(event) => {
                        if (isRail && window.innerWidth > 768) {
                          if (flyout?.anchor === event.currentTarget) {
                            setFlyout(null);
                            return;
                          }
                          setFlyout({
                            anchor: event.currentTarget,
                            items: item.children!.map((child) => ({
                              label: child.label,
                              onSelect: () => navigate(child.path),
                            })),
                          });
                          return;
                        }
                        setStoredOpenTree(treeOpen ? false : item.path);
                      }}
                    >
                      <span className="icon">{icons[item.area]}</span>
                      <span className="nav-text">{item.label}</span>
                      <ChevronRightIcon className="nav-chev" />
                    </button>
                    <div className="nav-sub">
                      <div className="nav-sub-inner">
                        {item.children?.map((child) => (
                          <Link
                            key={child.path}
                            to={child.path}
                            onClick={closeMobileSidebar}
                            className={`nav-sublink ${isActive(child.path) ? "active" : ""}`}
                          >
                            {child.label}
                          </Link>
                        ))}
                      </div>
                    </div>
                  </li>
                );
              }

              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    onClick={closeMobileSidebar}
                    className={`nav-link ${isActive(item.path) ? "active" : ""}`}
                    data-rail-label={item.label}
                  >
                    <span className="icon">{icons[item.area]}</span>
                    <span className="nav-text">{item.label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      </nav>

      <PopoverMenu
        anchor={flyout?.anchor || null}
        items={flyout?.items || []}
        open={Boolean(flyout)}
        onClose={() => setFlyout(null)}
      />

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
