/**
 * API Service for Commandes Module
 * Sprint 6
 */
import axios from 'axios';

import API_BASE_URL from "../config/api";
const API = API_BASE_URL;

// Get all commandes with optional filters
const _buildCommandesParams = (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.statut && filters.statut !== 'all') params.append('statut', filters.statut);
  if (filters.client_id && filters.client_id !== 'all') params.append('client_id', filters.client_id);
  if (filters.date_debut) params.append('date_debut', filters.date_debut);
  if (filters.date_fin) params.append('date_fin', filters.date_fin);
  if (filters.q) params.append('q', filters.q);
  if (filters.skip !== undefined) params.append('skip', filters.skip);
  if (filters.limit) params.append('limit', filters.limit);
  return params;
};

// Retourne un tableau (rétrocompatible)
export const getCommandes = async (filters = {}) => {
  const response = await axios.get(`${API}/commandes?${_buildCommandesParams(filters).toString()}`);
  const data = response.data;
  return Array.isArray(data) ? data : (data?.items ?? data);
};

// Retourne l'objet paginé complet { items, total, page, limit, has_next }
export const getCommandesPaginated = async (filters = {}) => {
  const response = await axios.get(`${API}/commandes?${_buildCommandesParams(filters).toString()}`);
  const data = response.data;
  if (data?.items !== undefined) return data;
  return { items: Array.isArray(data) ? data : [], total: 0, page: 1, limit: filters.limit || 50, has_next: false };
};

// Get single commande with lignes
export const getCommande = async (commandeId) => {
  const response = await axios.get(`${API}/commandes/${commandeId}`);
  return response.data;
};

// Create new commande
export const createCommande = async (data, submit = false) => {
  const response = await axios.post(`${API}/commandes?submit=${submit}`, data);
  return response.data;
};

// Update commande (brouillon only)
export const updateCommande = async (commandeId, data) => {
  const response = await axios.patch(`${API}/commandes/${commandeId}`, data);
  return response.data;
};

// Validate commande
export const validerCommande = async (commandeId) => {
  const response = await axios.post(`${API}/commandes/${commandeId}/valider`);
  return response.data;
};

// Prepare commande
export const preparerCommande = async (commandeId) => {
  const response = await axios.post(`${API}/commandes/${commandeId}/preparer`);
  return response.data;
};

// Deliver commande
export const livrerCommande = async (commandeId) => {
  const response = await axios.post(`${API}/commandes/${commandeId}/livrer`);
  return response.data;
};

// Cancel commande
export const annulerCommande = async (commandeId, motif) => {
  const response = await axios.post(`${API}/commandes/${commandeId}/annuler`, { motif });
  return response.data;
};

// Generate commande PDF
export const generateCommandePDF = async (commandeId) => {
  const response = await axios.get(`${API}/commandes/${commandeId}/pdf`, {
    responseType: 'blob',
  });
  return response.data;
};

// Send commande via WhatsApp
export const sendCommandeWhatsApp = async (commandeId, payload = {}) => {
  const response = await axios.post(`${API}/commandes/${commandeId}/envoyer-whatsapp`, payload || {});
  return response.data;
};

// Send commande via Email
export const sendCommandeEmail = async (commandeId, payload = {}) => {
  const response = await axios.post(`${API}/commandes/${commandeId}/envoyer-email`, payload || {});
  return response.data;
};

// Delete commande (super_admin uniquement — cascade complète)
export const deleteCommande = async (commandeId) => {
  await axios.delete(`${API}/commandes/${commandeId}`);
};

// Check doublon en temps réel
export const checkDoublon = async (payload) => {
  const response = await axios.post(`${API}/commandes/check-doublon`, payload);
  return response.data;
};

// Logger la décision utilisateur face à un doublon
export const logDoublonDecision = async (logId, decision) => {
  const response = await axios.patch(`${API}/commandes/check-doublon/${logId}`, { decision });
  return response.data;
};
