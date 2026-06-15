import { useEffect, useState, useCallback, useContext, createContext } from "react";
import axios from "axios";

const API = "/api";

// Token stocké en localStorage
export const tokenStore = {
  get: () => localStorage.getItem("fabs_token"),
  set: (t) => t ? localStorage.setItem("fabs_token", t) : localStorage.removeItem("fabs_token"),
  clear: () => localStorage.removeItem("fabs_token"),
};

// Intercepteur axios global : injecte le token dans chaque requête
axios.interceptors.request.use((config) => {
  const token = tokenStore.get();
  if (token) {
    config.headers["Authorization"] = `Bearer ${token}`;
  }
  return config;
});

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    const token = tokenStore.get();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const r = await axios.get(`${API}/auth/me`);
      setUser(r.data);
    } catch {
      tokenStore.clear();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = useCallback(async (email, password) => {
    const r = await axios.post(`${API}/auth/login`, { email, password });
    tokenStore.set(r.data.access_token);
    setUser(r.data.user);
    return r.data.user;
  }, []);

  const logout = useCallback(async () => {
    try {
      await axios.post(`${API}/auth/logout`, {});
    } catch (_) { /* ignore */ }
    tokenStore.clear();
    setUser(null);
    window.location.href = "/login";
  }, []);

  return (
    <AuthCtx.Provider value={{ user, isLoading, role: user?.role, setUser, refresh: checkAuth, login, logout }}>
      {children}
    </AuthCtx.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthCtx);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
