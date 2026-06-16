import axios from "axios";
import { getApiBase } from '../config/api';

const API = getApiBase("/colisage");

// ─── COLIS ───────────────────────────────────────────────────────────────────

export const listColis = async (filters = {}) => {
  const response = await axios.get(`${API}/colis`, { params: filters });
  return response.data;
};

export const getColisByFacture = async (factureId) => {
  const response = await axios.get(`${API}/colis/by-facture/${factureId}`);
  return response.data;
};

export const getColis = async (colisId) => {
  const response = await axios.get(`${API}/colis/${colisId}`);
  return response.data;
};

export const createColis = async (data) => {
  const response = await axios.post(`${API}/colis`, data);
  return response.data;
};

export const updateColis = async (colisId, data) => {
  const response = await axios.put(`${API}/colis/${colisId}`, data);
  return response.data;
};

export const updateColisStatut = async (colisId, statut, motif = null) => {
  const response = await axios.patch(`${API}/colis/${colisId}/statut`, { statut, motif });
  return response.data;
};

export const deleteColis = async (colisId) => {
  const response = await axios.delete(`${API}/colis/${colisId}`);
  return response.data;
};

// ─── STATS ───────────────────────────────────────────────────────────────────

export const getStatsColisageFacture = async (factureId) => {
  const response = await axios.get(`${API}/stats/facture/${factureId}`);
  return response.data;
};

// ─── EXPÉDITIONS (legacy — module séparé) ────────────────────────────────────

export const listExpeditions = async (filters = {}) => {
  const response = await axios.get(`${API}/expeditions`, { params: filters });
  return response.data;
};

export const getExpedition = async (expeditionId) => {
  const response = await axios.get(`${API}/expeditions/${expeditionId}`);
  return response.data;
};

export const createExpedition = async (data) => {
  const response = await axios.post(`${API}/expeditions`, data);
  return response.data;
};

export const updateExpeditionStatut = async (expeditionId, statut, dateLivraisonReelle = null) => {
  const response = await axios.patch(`${API}/expeditions/${expeditionId}/statut`, null, {
    params: { statut, date_livraison_reelle: dateLivraisonReelle },
  });
  return response.data;
};

// ─── MOUVEMENTS ──────────────────────────────────────────────────────────────

export const listMouvements = async (filters = {}) => {
  const response = await axios.get(`${API}/mouvements`, { params: filters });
  return response.data;
};
