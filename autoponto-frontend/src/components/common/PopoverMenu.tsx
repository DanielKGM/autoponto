import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

export type PopoverMenuItem = {
  label: string;
  onSelect: () => void;
  danger?: boolean;
};

type PopoverMenuProps = {
  anchor: HTMLElement | null;
  items: PopoverMenuItem[];
  open: boolean;
  onClose: () => void;
};

export function PopoverMenu({ anchor, items, open, onClose }: PopoverMenuProps) {
  const menuRef = useRef<HTMLDivElement | null>(null);
  const [position, setPosition] = useState({ top: 0, left: 0 });

  useLayoutEffect(() => {
    if (!open || !anchor || !menuRef.current) return;
    const rect = anchor.getBoundingClientRect();
    const menu = menuRef.current;
    const margin = 6;
    const width = menu.offsetWidth;
    const height = menu.offsetHeight;
    let top = rect.bottom + margin;
    let left = rect.right - width;
    if (top + height > window.innerHeight - 8) top = rect.top - height - margin;
    left = Math.max(8, Math.min(left, window.innerWidth - width - 8));
    setPosition({ top: Math.round(top), left: Math.round(left) });
  }, [anchor, items, open]);

  useEffect(() => {
    if (!open) return undefined;

    function closeFromOutside(event: MouseEvent) {
      const target = event.target as Node;
      if (menuRef.current?.contains(target) || anchor?.contains(target)) return;
      onClose();
    }

    function closeFromKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    document.addEventListener("mousedown", closeFromOutside);
    document.addEventListener("keydown", closeFromKey);
    window.addEventListener("scroll", onClose, true);
    window.addEventListener("resize", onClose);
    return () => {
      document.removeEventListener("mousedown", closeFromOutside);
      document.removeEventListener("keydown", closeFromKey);
      window.removeEventListener("scroll", onClose, true);
      window.removeEventListener("resize", onClose);
    };
  }, [anchor, onClose, open]);

  useEffect(() => {
    if (!open) return;
    const first = menuRef.current?.querySelector<HTMLButtonElement>(".menu-item");
    first?.focus();
  }, [open]);

  useEffect(() => {
    if (!open || !anchor) return undefined;
    anchor.setAttribute("aria-expanded", "true");
    return () => anchor.setAttribute("aria-expanded", "false");
  }, [anchor, open]);

  if (!open || !anchor) return null;

  return createPortal(
    <div
      className="menu-popover"
      role="menu"
      ref={menuRef}
      style={{ top: position.top, left: position.left }}
    >
      {items.map((item) => (
        <button
          type="button"
          className={`menu-item ${item.danger ? "menu-item-danger" : ""}`}
          role="menuitem"
          key={item.label}
          onClick={() => {
            onClose();
            item.onSelect();
          }}
        >
          {item.label}
        </button>
      ))}
    </div>,
    document.body,
  );
}
