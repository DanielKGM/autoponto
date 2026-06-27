import { createContext, useContext, type ReactNode } from "react";
import type { MeResponse } from "./types";

type SessionContextType = {
  me: MeResponse;
  signOut: () => Promise<void>;
};

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export function SessionProvider({ children, me, signOut }: { children: ReactNode; me: MeResponse; signOut: () => Promise<void> }) {
  return <SessionContext.Provider value={{ me, signOut }}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error("useSession must be used within SessionProvider");
  }
  return context;
}
