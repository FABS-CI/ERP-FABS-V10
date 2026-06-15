import axios from "axios";
import { getApiBase } from '../config/api';

const API = getApiBase("/colisage");

// Colis
export const listColis = async (filters = {}) => {
  const response = await axios.get(`${API}/colis`, { params: filters });
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

export const deleteColis = async (colisId) => {
  const response = await axios.delete(`${API}/colis/${colisId}`);
  return response.data;
};

export const updateColisStatut = async (colisId, statut) => {
  const response = await axios.patch(`${API}/colis/${colisId}/statut`, null, {
    params: { statut },
  });
  return response.data;
};

// Expéditions
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

// Mouvements
export const listMouvements = async (filters = {}) => {
  const response = await axios.get(`${API}/mouvements`, { params: filters });
  return response.data;
};
