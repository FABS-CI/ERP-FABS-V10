/**
 * API Service for Paiements Module - Sprint 8
 */
import axios from 'axios';

import API_BASE_URL from "../config/api";
const API = API_BASE_URL;

// TICKET-004 : ajout skip/limit pour pagination + retour {items, total}
export const getPaiements = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.mode_paiement) params.append('mode_paiement', filters.mode_paiement);
  if (filters.client_id) params.append('client_id', filters.client_id);
  if (filters.date_debut) params.append('date_debut', filters.date_debut);
  if (filters.date_fin) params.append('date_fin', filters.date_fin);
  if (filters.q) params.append('q', filters.q);
  if (filters.skip !== undefined) params.append('skip', filters.skip);
  if (filters.limit !== undefined) params.append('limit', filters.limit);

  const response = await axios.get(`${API}/paiements?${params.toString()}`);
  // Le backend retourne { items: [...], total: N }
  return response.data;
};

export const getPaiement = async (paiementId) => {
  const response = await axios.get(`${API}/paiements/${paiementId}`);
  return response.data;
};

export const createPaiement = async (data) => {
  const response = await axios.post(`${API}/paiements`, data);
  return response.data;
};

export const getPaiementsByFacture = async (factureId) => {
  const response = await axios.get(`${API}/paiements/facture/${factureId}`);
  return response.data;
};

export const sendPaiementWhatsApp = async (paiementId, payload = {}) => {
  const response = await axios.post(`${API}/paiements/${paiementId}/envoyer-whatsapp`, payload);
  return response.data;
};

export const sendPaiementEmail = async (paiementId, payload = {}) => {
  const response = await axios.post(`${API}/paiements/${paiementId}/envoyer-email`, payload);
  return response.data;
};

// ✅ TICKET-002 : génération PDF reçu paiement
export const getPaiementPDF = async (paiementId) => {
  const response = await axios.get(`${API}/paiements/${paiementId}/pdf`, {
    responseType: 'blob',
  });
  return response.data; // Blob
};
