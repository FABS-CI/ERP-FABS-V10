import api from "./api";  // ✅ PHASE 3.2: Use centralized api instance (HttpOnly + CSRF)

const API = "/api";

export const CATEGORIES = [
  { value: "maternelle",    label: "Maternelle",     color: "#FFFFFF", bg: "#7C5BC4" },
  { value: "primaire",      label: "Primaire",       color: "#FFFFFF", bg: "#2E7D32" },
  { value: "premier_cycle", label: "Premier cycle",  color: "#FFFFFF", bg: "#0A2540" },
  { value: "second_cycle",  label: "Second cycle",   color: "#FFFFFF", bg: "#FF6200" },
  { value: "litterature",   label: "Littérature",    color: "#FFFFFF", bg: "#C62828" },
  { value: "livre_commun",  label: "Livre commun",   color: "#FFFFFF", bg: "#455A64" },
  { value: "arts",          label: "Arts",           color: "#FFFFFF", bg: "#F57C00" },
];

export const CATEGORIES_MAP = Object.fromEntries(
  CATEGORIES.map((c) => [c.value, c])
);

// ✅ PHASE 3.2: Helper to make request with centralized api instance
// (Handles HttpOnly cookies + CSRF automatically)
async function apiCall(method, url, data = null, params = null) {
  const config = {
    method,
    url: API + url,
    params,
  };
  
  if (data) config.data = data;
  
  const res = await api(config);
  return res.data;
}

export async function listProducts(params = {}) {
  return apiCall('GET', '/produits', null, params);
}

export async function getProduct(id) {
  return apiCall('GET', `/produits/${id}`);
}

export async function createProduct(payload) {
  return apiCall('POST', '/produits', payload);
}

export async function updateProduct(id, payload) {
  return apiCall('PATCH', `/produits/${id}`, payload);
}

export async function disableProduct(id) {
  return apiCall('DELETE', `/produits/${id}`);
}

export async function lookupIsbn(isbn) {
  return apiCall('GET', '/produits/lookup-isbn', null, { isbn });
}

export async function classifierProduit(titre) {
  return apiCall('POST', '/produits/classifier', { titre });
}

export async function getStockAlerts() {
  return apiCall('GET', '/produits/alertes-stock');
}
