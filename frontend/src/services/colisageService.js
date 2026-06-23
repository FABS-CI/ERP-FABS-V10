import api from "./api";  // ✅ PHASE 3.2: Use centralized api instance (HttpOnly + CSRF)
import { getApiBase } from '../config/api';

const API = getApiBase("/colisage");
const API_PATH = "/colisage";  // Relative to /api base

// ─── ORDRES DE COLISAGE ───────────────────────────────────────────────────────

export const listOrdresColisage = async (filters = {}) => {
  const response = await api.get(`/colisage/ordres`, { params: filters });
  return response.data;
};

export const getDashboardColisage = async () => {
  const response = await api.get(`/colisage/ordres/dashboard`);
  return response.data;
};

export const getOrdreColisage = async (ordreId) => {
  const response = await api.get(`/colisage/ordres/${ordreId}`);
  return response.data;
};

export const createOrdreColisage = async (data) => {
  const response = await api.post(`/colisage/ordres`, data);
  return response.data;
};

export const updateOrdreColisageStatut = async (ordreId, statut, notes = null) => {
  const response = await api.patch(`/colisage/ordres/${ordreId}/statut`, { statut, notes });
  return response.data;
};

export const getCartonsSuggeres = async (ordreId) => {
  const response = await api.get(`/colisage/ordres/${ordreId}/cartons-suggeres`);
  return response.data;
};

// ─── CARTONS ─────────────────────────────────────────────────────────────────

export const listCartons = async (filters = {}) => {
  const response = await api.get(`/colisage/cartons`, { params: filters });
  return response.data;
};

export const getCarton = async (cartonId) => {
  const response = await api.get(`/colisage/cartons/${cartonId}`);
  return response.data;
};

export const genererCartonsAuto = async (ordreId, data = {}) => {
  const response = await api.post(`/colisage/cartons/generer-automatique/${ordreId}`, data);
  return response.data;
};

export const validerCarton = async (cartonId, data = {}) => {
  const response = await api.patch(`/colisage/cartons/${cartonId}/valider`, data);
  return response.data;
};

export const deleteCarton = async (cartonId) => {
  const response = await api.delete(`/colisage/cartons/${cartonId}`);
  return response.data;
};

// ─── LIVRAISONS DIRECTES ─────────────────────────────────────────────────────

export const listLivraisons = async (filters = {}) => {
  const response = await api.get(`/colisage/livraisons`, { params: filters });
  return response.data;
};

export const getLivraison = async (livraisonId) => {
  const response = await api.get(`/colisage/livraisons/${livraisonId}`);
  return response.data;
};

export const createLivraison = async (data) => {
  const response = await api.post(`/colisage/livraisons`, data);
  return response.data;
};

export const updateLivraisonStatut = async (livraisonId, statut, notes = null) => {
  const response = await api.patch(`/colisage/livraisons/${livraisonId}/statut`, { statut, notes });
  return response.data;
};

export const chargerCartonLivraison = async (livraisonId, cartonId) => {
  const response = await api.post(`/colisage/livraisons/${livraisonId}/charger-carton`, { carton_id: cartonId });
  return response.data;
};

export const receptionnerLivraison = async (livraisonId, data) => {
  const response = await api.post(`/colisage/livraisons/${livraisonId}/reception`, data);
  return response.data;
};

export const signalerIncidentLivraison = async (livraisonId, data) => {
  const response = await api.post(`/colisage/livraisons/${livraisonId}/incident`, data);
  return response.data;
};

// ─── EXPÉDITIONS (nouvelles — villes distantes) ───────────────────────────────

export const listExpeditionsColisage = async (filters = {}) => {
  const response = await api.get(`/colisage/expeditions`, { params: filters });
  return response.data;
};

export const getExpeditionColisage = async (expeditionId) => {
  const response = await api.get(`/colisage/expeditions/${expeditionId}`);
  return response.data;
};

export const createExpeditionColisage = async (data) => {
  const response = await api.post(`/colisage/expeditions`, data);
  return response.data;
};

export const updateExpeditionColisageStatut = async (expeditionId, statut, notes = null) => {
  const response = await api.patch(`/colisage/expeditions/${expeditionId}/statut`, { statut, notes });
  return response.data;
};

export const receptionnerExpedition = async (expeditionId, data) => {
  const response = await api.post(`/colisage/expeditions/${expeditionId}/reception`, data);
  return response.data;
};

export const recupererExpedition = async (expeditionId, data) => {
  const response = await api.post(`/colisage/expeditions/${expeditionId}/recuperation`, data);
  return response.data;
};

export const signalerIncidentExpedition = async (expeditionId, data) => {
  const response = await api.post(`/colisage/expeditions/${expeditionId}/incident`, data);
  return response.data;
};

// ─── LEGACY COLIS (rétrocompatibilité) ───────────────────────────────────────

export const listColis = async (filters = {}) => {
  const response = await api.get(`/colisage/colis`, { params: filters });
  return response.data;
};

export const getColisByFacture = async (factureId) => {
  const response = await api.get(`/colisage/colis/by-facture/${factureId}`);
  return response.data;
};

export const getColis = async (colisId) => {
  const response = await api.get(`/colisage/colis/${colisId}`);
  return response.data;
};

export const createColis = async (data) => {
  const response = await api.post(`/colisage/colis`, data);
  return response.data;
};

export const updateColis = async (colisId, data) => {
  const response = await axios.put(`/colisage/colis/${colisId}`, data);
  return response.data;
};

export const updateColisStatut = async (colisId, statut, motif = null) => {
  const response = await api.patch(`/colisage/colis/${colisId}/statut`, { statut, motif });
  return response.data;
};

export const deleteColis = async (colisId) => {
  const response = await api.delete(`/colisage/colis/${colisId}`);
  return response.data;
};

export const getStatsColisageFacture = async (factureId) => {
  const response = await api.get(`/colisage/stats/facture/${factureId}`);
  return response.data;
};

export const listMouvements = async (filters = {}) => {
  const response = await api.get(`/colisage/mouvements`, { params: filters });
  return response.data;
};

// ─── ÉTIQUETTES & QR CODE ────────────────────────────────────────────────────

// ✅ PHASE 3.2: URLs without token (browser sends HttpOnly cookie automatically)
export const getCartonQrCodeUrl = (cartonId) =>
  `/api/colisage/cartons/${cartonId}/qrcode`;

export const getCartonEtiquetteUrl = (cartonId) =>
  `/api/colisage/cartons/${cartonId}/etiquette`;

export const getOrdreEtiquettesBulkUrl = (ordreId) =>
  `/api/colisage/ordres/${ordreId}/etiquettes-bulk`;

// téléchargement direct (ouvre dans nouvel onglet ou force download)
// ✅ PHASE 3.2: fetch with credentials to include HttpOnly cookies
export const downloadCartonEtiquette = (cartonId) => {
  const url = getCartonEtiquetteUrl(cartonId);
  fetch(url, { credentials: "include" })
    .then(res => res.blob())
    .then(blob => {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `carton_${cartonId}_etiquette.pdf`;
      a.click();
      URL.revokeObjectURL(a.href);
    })
    .catch(err => console.error("Erreur téléchargement étiquette:", err));
};

export const downloadOrdreEtiquettesBulk = (ordreId) => {
  const url = getOrdreEtiquettesBulkUrl(ordreId);
  fetch(url, { credentials: "include" })
    .then(res => res.blob())
    .then(blob => {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `ordre_${ordreId}_etiquettes.pdf`;
      a.click();
      URL.revokeObjectURL(a.href);
    })
    .catch(err => console.error("Erreur téléchargement étiquettes:", err));
};

// ─── INCIDENTS CONSOLIDÉS ────────────────────────────────────────────────────

export const listIncidents = async (filters = {}) => {
  const response = await api.get(`/colisage/incidents`, { params: filters });
  return response.data;
};

// TICKET-011 : résolution incident
export const updateIncidentResolution = async ({ source, document_id, incident_id, statut_resolution, commentaire }) => {
  const base = source === "expedition"
    ? `/colisage/expeditions/${document_id}/incident/${incident_id}/resolution`
    : `/colisage/livraisons/${document_id}/incident/${incident_id}/resolution`;
  const response = await api.patch(base, { statut_resolution, commentaire });
  return response.data;
};

// Legacy aliases
export const listExpeditions = listExpeditionsColisage;
export const getExpedition = getExpeditionColisage;
export const createExpedition = createExpeditionColisage;
export const updateExpeditionStatut = (id, statut, date = null) =>
  updateExpeditionColisageStatut(id, statut);
