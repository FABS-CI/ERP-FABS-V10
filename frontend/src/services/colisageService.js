import axios from "axios";
import { getApiBase } from '../config/api';

const API = getApiBase("/colisage");

// ─── ORDRES DE COLISAGE ───────────────────────────────────────────────────────

export const listOrdresColisage = async (filters = {}) => {
  const response = await axios.get(`${API}/ordres`, { params: filters });
  return response.data;
};

export const getDashboardColisage = async () => {
  const response = await axios.get(`${API}/ordres/dashboard`);
  return response.data;
};

export const getOrdreColisage = async (ordreId) => {
  const response = await axios.get(`${API}/ordres/${ordreId}`);
  return response.data;
};

export const createOrdreColisage = async (data) => {
  const response = await axios.post(`${API}/ordres`, data);
  return response.data;
};

export const updateOrdreColisageStatut = async (ordreId, statut, notes = null) => {
  const response = await axios.patch(`${API}/ordres/${ordreId}/statut`, { statut, notes });
  return response.data;
};

export const getCartonsSuggeres = async (ordreId) => {
  const response = await axios.get(`${API}/ordres/${ordreId}/cartons-suggeres`);
  return response.data;
};

// ─── CARTONS ─────────────────────────────────────────────────────────────────

export const listCartons = async (filters = {}) => {
  const response = await axios.get(`${API}/cartons`, { params: filters });
  return response.data;
};

export const getCarton = async (cartonId) => {
  const response = await axios.get(`${API}/cartons/${cartonId}`);
  return response.data;
};

export const genererCartonsAuto = async (ordreId, data = {}) => {
  const response = await axios.post(`${API}/cartons/generer-automatique/${ordreId}`, data);
  return response.data;
};

export const validerCarton = async (cartonId, data = {}) => {
  const response = await axios.patch(`${API}/cartons/${cartonId}/valider`, data);
  return response.data;
};

export const deleteCarton = async (cartonId) => {
  const response = await axios.delete(`${API}/cartons/${cartonId}`);
  return response.data;
};

// ─── LIVRAISONS DIRECTES ─────────────────────────────────────────────────────

export const listLivraisons = async (filters = {}) => {
  const response = await axios.get(`${API}/livraisons`, { params: filters });
  return response.data;
};

export const getLivraison = async (livraisonId) => {
  const response = await axios.get(`${API}/livraisons/${livraisonId}`);
  return response.data;
};

export const createLivraison = async (data) => {
  const response = await axios.post(`${API}/livraisons`, data);
  return response.data;
};

export const updateLivraisonStatut = async (livraisonId, statut, notes = null) => {
  const response = await axios.patch(`${API}/livraisons/${livraisonId}/statut`, { statut, notes });
  return response.data;
};

export const chargerCartonLivraison = async (livraisonId, cartonId) => {
  const response = await axios.post(`${API}/livraisons/${livraisonId}/charger-carton`, { carton_id: cartonId });
  return response.data;
};

export const receptionnerLivraison = async (livraisonId, data) => {
  const response = await axios.post(`${API}/livraisons/${livraisonId}/reception`, data);
  return response.data;
};

export const signalerIncidentLivraison = async (livraisonId, data) => {
  const response = await axios.post(`${API}/livraisons/${livraisonId}/incident`, data);
  return response.data;
};

// ─── EXPÉDITIONS (nouvelles — villes distantes) ───────────────────────────────

export const listExpeditionsColisage = async (filters = {}) => {
  const response = await axios.get(`${API}/expeditions`, { params: filters });
  return response.data;
};

export const getExpeditionColisage = async (expeditionId) => {
  const response = await axios.get(`${API}/expeditions/${expeditionId}`);
  return response.data;
};

export const createExpeditionColisage = async (data) => {
  const response = await axios.post(`${API}/expeditions`, data);
  return response.data;
};

export const updateExpeditionColisageStatut = async (expeditionId, statut, notes = null) => {
  const response = await axios.patch(`${API}/expeditions/${expeditionId}/statut`, { statut, notes });
  return response.data;
};

export const receptionnerExpedition = async (expeditionId, data) => {
  const response = await axios.post(`${API}/expeditions/${expeditionId}/reception`, data);
  return response.data;
};

export const recupererExpedition = async (expeditionId, data) => {
  const response = await axios.post(`${API}/expeditions/${expeditionId}/recuperation`, data);
  return response.data;
};

export const signalerIncidentExpedition = async (expeditionId, data) => {
  const response = await axios.post(`${API}/expeditions/${expeditionId}/incident`, data);
  return response.data;
};

// ─── LEGACY COLIS (rétrocompatibilité) ───────────────────────────────────────

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

export const getStatsColisageFacture = async (factureId) => {
  const response = await axios.get(`${API}/stats/facture/${factureId}`);
  return response.data;
};

export const listMouvements = async (filters = {}) => {
  const response = await axios.get(`${API}/mouvements`, { params: filters });
  return response.data;
};

// ─── ÉTIQUETTES & QR CODE ────────────────────────────────────────────────────

const _getToken = () => localStorage.getItem("fabs_token") || "";

export const getCartonQrCodeUrl = (cartonId) =>
  `${API}/cartons/${cartonId}/qrcode?token=${_getToken()}`;

export const getCartonEtiquetteUrl = (cartonId) =>
  `${API}/cartons/${cartonId}/etiquette?token=${_getToken()}`;

export const getOrdreEtiquettesBulkUrl = (ordreId) =>
  `${API}/ordres/${ordreId}/etiquettes-bulk?token=${_getToken()}`;

// téléchargement direct (ouvre dans nouvel onglet ou force download)
export const downloadCartonEtiquette = (cartonId) => {
  window.open(getCartonEtiquetteUrl(cartonId), "_blank");
};

export const downloadOrdreEtiquettesBulk = (ordreId) => {
  window.open(getOrdreEtiquettesBulkUrl(ordreId), "_blank");
};

// ─── INCIDENTS CONSOLIDÉS ────────────────────────────────────────────────────

export const listIncidents = async (filters = {}) => {
  const response = await axios.get(`${API}/incidents`, { params: filters });
  return response.data;
};

// TICKET-011 : résolution incident
export const updateIncidentResolution = async ({ source, document_id, incident_id, statut_resolution, commentaire }) => {
  const base = source === "expedition"
    ? `${API}/expeditions/${document_id}/incident/${incident_id}/resolution`
    : `${API}/livraisons/${document_id}/incident/${incident_id}/resolution`;
  const response = await axios.patch(base, { statut_resolution, commentaire });
  return response.data;
};

// Legacy aliases
export const listExpeditions = listExpeditionsColisage;
export const getExpedition = getExpeditionColisage;
export const createExpedition = createExpeditionColisage;
export const updateExpeditionStatut = (id, statut, date = null) =>
  updateExpeditionColisageStatut(id, statut);
