import {
  useEffect,
  useRef,
  type KeyboardEvent,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";
import { CloseIcon } from "./icons";

type ModalProps = {
  open: boolean;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  size?: "sm" | "md" | "lg";
  onClose: () => void;
};

const FOCUSABLE =
  'button:not([disabled]), [href], input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function Modal({
  open,
  title,
  children,
  footer,
  size = "md",
  onClose,
}: ModalProps) {
  const dialogRef = useRef<HTMLDivElement | null>(null);
  const bodyRef = useRef<HTMLDivElement | null>(null);
  const previousFocusRef = useRef<Element | null>(null);
  const onCloseRef = useRef(onClose);

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    if (!open) return undefined;
    previousFocusRef.current = document.activeElement;
    document.body.classList.add("modal-open");
    const frame = window.requestAnimationFrame(() => {
      const firstInBody = bodyRef.current?.querySelector<HTMLElement>(FOCUSABLE);
      const firstAction = dialogRef.current?.querySelector<HTMLElement>(".modal-footer .btn-primary, .modal-footer .btn-danger");
      const closeButton = dialogRef.current?.querySelector<HTMLElement>(".modal-close");
      (firstInBody || firstAction || closeButton)?.focus();
    });

    function handleKeydown(event: globalThis.KeyboardEvent) {
      if (event.key === "Escape") {
        event.stopPropagation();
        onCloseRef.current();
      }
    }

    document.addEventListener("keydown", handleKeydown);
    return () => {
      window.cancelAnimationFrame(frame);
      document.removeEventListener("keydown", handleKeydown);
      document.body.classList.remove("modal-open");
      const focusBack = previousFocusRef.current as HTMLElement | null;
      focusBack?.focus?.();
      previousFocusRef.current = null;
    };
  }, [open]);

  if (!open) return null;

  function trapFocus(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key !== "Tab") return;
    const focusable = dialogRef.current?.querySelectorAll<HTMLElement>(FOCUSABLE);
    if (!focusable?.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  return createPortal(
    <div className="modal-backdrop show" onMouseDown={(event) => {
      if (event.target === event.currentTarget) onCloseRef.current();
    }}>
      <div
        className={`modal-dialog modal-${size}`}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        ref={dialogRef}
        onKeyDown={trapFocus}
      >
        <div className="modal-header">
          <h2 className="modal-title">{title}</h2>
          <button type="button" className="modal-close" aria-label="Fechar" onClick={() => onCloseRef.current()}>
            <CloseIcon />
          </button>
        </div>
        <div className="modal-body" ref={bodyRef}>{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>,
    document.body,
  );
}
