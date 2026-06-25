import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

type ToastVariant = "default" | "success" | "error" | "warning" | "info";
type ToastOptions = {
  variant?: ToastVariant;
  duration?: number;
};

type Toast = {
  id: number;
  message: string;
  variant: ToastVariant;
  visible: boolean;
};

type ToastContextValue = {
  showToast: (message: string, variantOrOptions?: ToastVariant | ToastOptions) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback(
    (message: string, variantOrOptions: ToastVariant | ToastOptions = "default") => {
      const options =
        typeof variantOrOptions === "string"
          ? { variant: variantOrOptions }
          : variantOrOptions;
      const variant = options.variant || "default";
      const duration = options.duration ?? 2600;
      const id = Date.now() + Math.floor(Math.random() * 1000);
      setToasts((current) => [...current, { id, message, variant, visible: false }]);
      window.requestAnimationFrame(() => {
        setToasts((current) =>
          current.map((toast) => (toast.id === id ? { ...toast, visible: true } : toast)),
        );
      });
      window.setTimeout(() => {
        setToasts((current) =>
          current.map((toast) => (toast.id === id ? { ...toast, visible: false } : toast)),
        );
        window.setTimeout(() => removeToast(id), 220);
      }, duration);
    },
    [removeToast],
  );

  const value = useMemo(() => ({ showToast }), [showToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toast-host" role="status" aria-live="polite" aria-atomic="false">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`toast toast-${toast.variant} ${toast.visible ? "show" : ""}`}
            onClick={() => {
              setToasts((current) =>
                current.map((item) => (item.id === toast.id ? { ...item, visible: false } : item)),
              );
              window.setTimeout(() => removeToast(toast.id), 220);
            }}
          >
            {toast.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast deve ser usado dentro de ToastProvider.");
  }
  return context;
}
