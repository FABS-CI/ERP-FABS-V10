import axios from "axios";

import API_BASE_URL from "../config/api";
const API = API_BASE_URL;

export const TYPE_CLIENTS = [
  { value: "librairie",      label: "Librairie",       color: "#FFFFFF", bg: "#0A2540" },
  { value: "lycee",          label: "Lycée",            color: "#FFFFFF", bg: "#1565C0" },
  { value: "college",        label: "Collège",          color: "#FFFFFF", bg: "#0288D1" },
  { value: "groupe_scolaire",label: "Groupe Scolaire",  color: "#FFFFFF", bg: "#00796B" },
  { value: "epp",            label: "EPP",              color: "#FFFFFF", bg: "#558B2F" },
  { value: "iep",            label: "IEP",              color: "#FFFFFF", bg: "#2E7D32" },
  { value: "catholique",     label: "Catholique",       color: "#FFFFFF", bg: "#6A1B9A" },
  { value: "methodiste",     label: "Méthodiste",       color: "#FFFFFF", bg: "#4A148C" },
  { value: "particulier",    label: "Particulier",      color: "#0A2540", bg: "#E5E7EB" },
  { value: "distributeur",   label: "Distributeur",     color: "#FFFFFF", bg: "#FF6200" },
  { value: "representant",   label: "Représentant",     color: "#FFFFFF", bg: "#7C3AED" },
  { value: "memo",           label: "Mémo / APFC",      color: "#FFFFFF", bg: "#F57F17" },
  { value: "inspecteur",     label: "Inspecteur",       color: "#FFFFFF", bg: "#BF360C" },
  { value: "dren",           label: "DREN",             color: "#FFFFFF", bg: "#880E4F" },
  { value: "up",             label: "UP",               color: "#FFFFFF", bg: "#37474F" },
  { value: "institut",       label: "Institut",         color: "#FFFFFF", bg: "#4E342E" },
  { value: "ecole",          label: "École",            color: "#FFFFFF", bg: "#388E3C" },
  { value: "autre",          label: "Autre",            color: "#0A2540", bg: "#CFD8DC" },
];

export const TYPE_COLOR = Object.fromEntries(
  TYPE_CLIENTS.map((t) => [t.value, t])
);

export async function listClients({ q, type_client, ville, actif, page = 1, page_size = 20 } = {}) {
  const params = { page, page_size };
  if (q) params.q = q;
  if (type_client) params.type_client = type_client;
  if (ville) params.ville = ville;
  if (actif != null) params.actif = actif;
  const r = await axios.get(`${API}/clients`, { params });
  return r.data;
}

export async function getClient(id) {
  const r = await axios.get(`${API}/clients/${id}`);
  return r.data;
}

export async function createClient(payload, { force = false } = {}) {
  const r = await axios.post(`${API}/clients`, payload, { params: { force } });
  return r.data;
}

export async function updateClient(id, payload) {
  const r = await axios.patch(`${API}/clients/${id}`, payload);
  return r.data;
}

export async function disableClient(id) {
  const r = await axios.delete(`${API}/clients/${id}`);
  return r.data;
}

export async function checkDuplicates({ nom, telephone, exclude_id }) {
  const r = await axios.post(`${API}/clients/check-duplicates`, {
    nom,
    telephone: telephone || null,
    exclude_id: exclude_id || null,
  });
  return r.data; // { matches: [...] }
}
