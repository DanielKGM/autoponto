import { useState } from "react";
import { useSession } from "../../app/session";
import { ChevronDownIcon, LogOutIcon, UserIcon } from "../icons";
import { Dropdown } from "../ui/dropdown/Dropdown";
import { DropdownItem } from "../ui/dropdown/DropdownItem";

export function UserDropdown() {
  const { me, signOut } = useSession();
  const [isOpen, setIsOpen] = useState(false);
  const nome = me.usuario.nome_completo || me.usuario.username;

  function closeDropdown() {
    setIsOpen(false);
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen((current) => !current)}
        className="dropdown-toggle flex items-center text-gray-700 dark:text-gray-400"
      >
        <span className="mr-3 grid h-11 w-11 place-items-center overflow-hidden rounded-full bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
          <UserIcon className="size-5" />
        </span>
        <span className="mr-1 hidden max-w-[180px] truncate font-medium text-theme-sm xl:block">{nome}</span>
        <ChevronDownIcon className={`hidden size-5 transition-transform duration-200 xl:block ${isOpen ? "rotate-180" : ""}`} />
      </button>

      <Dropdown
        isOpen={isOpen}
        onClose={closeDropdown}
        className="mt-[17px] flex w-[260px] flex-col rounded-2xl p-3"
      >
        <div>
          <span className="block truncate font-medium text-gray-700 text-theme-sm dark:text-gray-300">{nome}</span>
          <span className="mt-0.5 block truncate text-theme-xs text-gray-500 dark:text-gray-400">
            {me.usuario.email || me.usuario.username}
          </span>
        </div>

        <ul className="flex flex-col gap-1 border-b border-gray-200 py-3 dark:border-gray-800">
          <li>
            <DropdownItem
              tag="a"
              to="/app/perfil"
              onItemClick={closeDropdown}
              className="flex items-center gap-3 rounded-lg px-3 py-2 font-medium text-gray-700 text-theme-sm hover:bg-gray-100 hover:text-gray-700 dark:text-gray-300 dark:hover:bg-white/5"
            >
              <UserIcon className="size-5 text-gray-500 dark:text-gray-400" />
              Perfil
            </DropdownItem>
          </li>
        </ul>

        <DropdownItem
          onClick={signOut}
          onItemClick={closeDropdown}
          className="mt-3 flex items-center gap-3 rounded-lg px-3 py-2 font-medium text-gray-700 text-theme-sm hover:bg-gray-100 hover:text-gray-700 dark:text-gray-300 dark:hover:bg-white/5"
        >
          <LogOutIcon className="size-5 text-gray-500 dark:text-gray-400" />
          Sair
        </DropdownItem>
      </Dropdown>
    </div>
  );
}
