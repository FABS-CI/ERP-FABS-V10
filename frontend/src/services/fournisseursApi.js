import axios from "axios";
import API_BASE_URL from "../config/api";

const API_BASE = API_BASE_URL;

export async function listFournisseurs(params = {}) {
  const response = await axios.get(`${API_BASE}/fournisseurs`, { params });
  return response.data;
}

export async function getFournisseur(id) {
  const response = await axios.get(`${API_BASE}/fournisseurs/${id}`);
  return response.data;
}

export async function createFournisseur(data) {
  const response = await axios.post(`${API_BASE}/fournisseurs`, data);
  return response.data;
}

export async function updateFournisseur(id, data) {
  const response = await axios.put(`${API_BASE}/fournisseurs/${id}`, data);
  return response.data;
}

export async function deleteFournisseur(id) {
  const response = await axios.delete(`${API_BASE}/fournisseurs/${id}`);
  return response.data;
}
