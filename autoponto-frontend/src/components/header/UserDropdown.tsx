import { useEffect, useRef, useState } from "react";
import { Link } from "react-router";
import { useSession } from "../../app/session";
import { LogOutIcon, UserIcon } from "../icons";

function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("") || "AP";
}

export function UserDropdown() {
  const { me, signOut } = useSession();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const nome = me.usuario.nome_completo || me.usuario.username;

  function closeDropdown() {
    setIsOpen(false);
  }

  useEffect(() => {
    if (!isOpen) return;

    function handlePointerDown(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        closeDropdown();
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") closeDropdown();
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  return (
    <div className="dropdown" ref={menuRef}>
      <button
        type="button"
        onClick={() => setIsOpen((current) => !current)}
        className="tb-avatar"
        aria-label="Abrir menu do usuario"
        aria-expanded={isOpen}
      >
        {initials(nome)}
      </button>

      {isOpen && (
        <div className="user-menu" role="menu">
          <div className="user-menu-header">
            <span className="user-menu-name">{nome}</span>
            <span className="user-menu-email">{me.usuario.email || me.usuario.username}</span>
          </div>
          <Link to="/app/perfil" onClick={closeDropdown} className="menu-item" role="menuitem">
            <UserIcon />
            Perfil
          </Link>
          <button
            type="button"
            onClick={() => {
              closeDropdown();
              signOut();
            }}
            className="menu-item"
            role="menuitem"
          >
            <LogOutIcon />
            Sair
          </button>
        </div>
      )}
    </div>
  );
}
