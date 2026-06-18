/**
 * Instance axios centralisée — utilisée par les modules logistique et stock.
 * Reprend le même pattern que les autres services (pas d'intercepteur global, le token
 * est géré par le proxy craco ou les cookies httpOnly).
 */
import axios from "axios";
import { API_BASE_URL } from "../config/api";

const api = axios.create({
  baseURL: API_BASE_URL,
});

export default api;
