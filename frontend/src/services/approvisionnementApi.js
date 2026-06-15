import axios from "axios";
import API_BASE_URL from "../config/api";

const API_BASE = API_BASE_URL;

export async function listApprovisionnements(params = {}) {
  const response = await axios.get(`${API_BASE}/approvisionnements`, { params });
  return response.data;
}

export async function getApprovisionnement(id) {
  const response = await axios.get(`${API_BASE}/approvisionnements/${id}`);
  return response.data;
}

export async function createApprovisionnement(data) {
  const response = await axios.post(`${API_BASE}/approvisionnements`, data);
  return response.data;
}

export async function validerApprovisionnement(id) {
  const response = await axios.post(`${API_BASE}/approvisionnements/${id}/valider`);
  return response.data;
}

export async function getLivraisonsFournisseur(fournisseurId, params = {}) {
  const response = await axios.get(`${API_BASE}/fournisseurs/${fournisseurId}/livraisons`, { params });
  return response.data;
}
