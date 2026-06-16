/**
 * API Service for Proformas — ERP FABS-CI
 * Utilise les cookies httpOnly (JWT) gérés automatiquement par axios.
 */
import axios from "axios";
import API_BASE_URL from "../config/api";

const API = API_BASE_URL;

export async function listProformas(params = {}) {
  const r = await axios.get(`${API}/proformas`, { params });
  return r.data;
}

export async function getProforma(proformaId) {
  const r = await axios.get(`${API}/proformas/${proformaId}`);
  return r.data;
}

export async function createProforma(payload) {
  const r = await axios.post(`${API}/proformas`, payload);
  return r.data;
}

export async function updateProforma(proformaId, payload) {
  const r = await axios.patch(`${API}/proformas/${proformaId}`, payload);
  return r.data;
}

export async function deleteProforma(proformaId) {
  const r = await axios.delete(`${API}/proformas/${proformaId}`);
  return r.data;
}

export async function generateProformaPDF(proformaId) {
  const r = await axios.post(
    `${API}/proformas/${proformaId}/generer-pdf`,
    {},
    { responseType: "blob" }
  );
  return r.data;
}

export async function sendProformaWhatsApp(proformaId, payload = {}) {
  const r = await axios.post(`${API}/proformas/${proformaId}/envoyer-whatsapp`, payload || {});
  return r.data;
}

export async function sendProformaEmail(proformaId, payload = {}) {
  const r = await axios.post(`${API}/proformas/${proformaId}/envoyer-email`, payload || {});
  return r.data;
}

export async function convertProformaToInvoice(proformaId) {
  const r = await axios.post(`${API}/proformas/${proformaId}/convertir-facture`, {});
  return r.data;
}

export async function getProformasDashboardStats() {
  const r = await axios.get(`${API}/proformas/stats/dashboard`);
  return r.data;
}
