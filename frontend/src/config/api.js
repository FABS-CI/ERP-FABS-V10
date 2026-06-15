/**
 * Configuration centrale de l'API
 * Le proxy craco (devServer) redirige /api → http://localhost:8001
 * en interne, donc le browser appelle toujours le port 3000.
 */

export const API_BASE_URL = "/api";

export const getApiBase = (suffix = "") => `/api${suffix}`;

export default API_BASE_URL;
