"use client";

import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { apiFetch } from "@/lib/api";
import { clearToken, getToken, setToken } from "@/lib/auth";

export type AuthUser = {
  id: number;
  email: string;
  full_name: string;
  role: "student" | "faculty";
  created_at: string;
  bio?: string | null;
  institution?: string | null;
  department?: string | null;
  research_interests?: string | null;
  website?: string | null;
  orcid?: string | null;
  linkedin?: string | null;
};

type AuthContextValue = {
  user: AuthUser | null;
  isLoading: boolean;
  error: string | null;
  login: (token: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const token = getToken();
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    try {
      const me = await apiFetch<AuthUser>("/me");
      setUser(me);
      setError(null);
    } catch (err) {
      clearToken();
      setUser(null);
      setError(err instanceof Error ? err.message : "Unable to load session");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = useCallback(
    async (token: string) => {
      setToken(token);
      await refresh();
    },
    [refresh],
  );

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const value = useMemo(
    () => ({ user, isLoading, error, login, logout, refresh }),
    [user, isLoading, error, login, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
