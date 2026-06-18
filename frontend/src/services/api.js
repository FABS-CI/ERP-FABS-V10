/**
 * Instance axios centralisée — utilisée par les modules logistique et stock.
 * Injecte automatiquement le token JWT depuis localStorage.
 */
import axios from "axios";
import { API_BASE_URL } from "../config/api";
import { tokenStore } from "../hooks/useAuth";

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = tokenStore.get();
  if (token) {
    config.headers["Authorization"] = `Bearer ${token}`;
  }
  return config;
});

export default api;
