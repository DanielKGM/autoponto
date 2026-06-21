import { useState } from "react";
import { Link } from "react-router";
import { BrandLogo } from "../components/common/BrandLogo";
import { ThemeToggleButton } from "../components/common/ThemeToggleButton";
import { UserDropdown } from "../components/header/UserDropdown";
import { useSidebar } from "../context/SidebarContext";

export function AppHeader() {
  const [isApplicationMenuOpen, setApplicationMenuOpen] = useState(false);
  const { isMobileOpen, toggleMobileSidebar, toggleSidebar } = useSidebar();

  function toggleMenu() {
    if (window.innerWidth >= 1024) {
      toggleSidebar();
    } else {
      toggleMobileSidebar();
    }
  }

  return (
    <header className="sticky top-0 z-[70] flex w-full border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900 lg:border-b">
      <div className="flex grow flex-col items-center justify-between lg:flex-row lg:px-6">
        <div className="flex w-full items-center justify-between gap-2 border-b border-gray-200 px-3 py-3 dark:border-gray-800 sm:gap-4 lg:justify-normal lg:border-b-0 lg:px-0 lg:py-4">
          <button
            type="button"
            onClick={toggleMenu}
            aria-label="Alternar menu"
            className="grid h-10 w-10 place-items-center rounded-lg border border-gray-200 text-gray-500 transition hover:bg-gray-100 hover:text-gray-700 dark:border-gray-800 dark:text-gray-400 dark:hover:bg-gray-800 lg:h-11 lg:w-11"
          >
            {isMobileOpen ? (
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path
                  fillRule="evenodd"
                  clipRule="evenodd"
                  d="M6.22 7.28a.75.75 0 0 1 1.06-1.06L12 10.94l4.72-4.72a.75.75 0 1 1 1.06 1.06L13.06 12l4.72 4.72a.75.75 0 1 1-1.06 1.06L12 13.06l-4.72 4.72a.75.75 0 0 1-1.06-1.06L10.94 12 6.22 7.28Z"
                  fill="currentColor"
                />
              </svg>
            ) : (
              <svg width="16" height="12" viewBox="0 0 16 12" fill="none" aria-hidden="true">
                <path
                  fillRule="evenodd"
                  clipRule="evenodd"
                  d="M.58 1c0-.41.34-.75.75-.75h13.34a.75.75 0 0 1 0 1.5H1.33A.75.75 0 0 1 .58 1Zm0 10c0-.41.34-.75.75-.75h13.34a.75.75 0 0 1 0 1.5H1.33a.75.75 0 0 1-.75-.75ZM1.33 5.25a.75.75 0 0 0 0 1.5H8a.75.75 0 0 0 0-1.5H1.33Z"
                  fill="currentColor"
                />
              </svg>
            )}
          </button>
          <Link to="/" className="lg:hidden">
            <BrandLogo size="sm" />
          </Link>

          <button
            type="button"
            onClick={() => setApplicationMenuOpen((current) => !current)}
            aria-label="Alternar menu da aplicacao"
            className="grid h-10 w-10 place-items-center rounded-lg text-gray-700 transition hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800 lg:hidden"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path
                fillRule="evenodd"
                clipRule="evenodd"
                d="M6 10.5a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3Zm6 0a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3Zm6 0a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3Z"
                fill="currentColor"
              />
            </svg>
          </button>
        </div>
        <div
          className={`${
            isApplicationMenuOpen ? "flex" : "hidden"
          } w-full items-center justify-between gap-4 px-5 py-4 shadow-theme-md lg:flex lg:w-auto lg:justify-end lg:px-0 lg:py-0 lg:shadow-none`}
        >
          <div className="flex items-center gap-2">
            <ThemeToggleButton />
          </div>
          <UserDropdown />
        </div>
      </div>
    </header>
  );
}
