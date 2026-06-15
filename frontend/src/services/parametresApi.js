/**
 * API Service for Paramètres - Sprint 13
 */
import axios from 'axios';

import API_BASE_URL from "../config/api";
const API = API_BASE_URL;

export const getParametres = async () => {
  const response = await axios.get(`${API}/parametres`);
  return response.data;
};

export const getParametre = async (cle) => {
  const response = await axios.get(`${API}/parametres/${cle}`);
  return response.data;
};

export const updateParametre = async (cle, valeur) => {
  const response = await axios.patch(`${API}/parametres/${cle}`, { valeur });
  return response.data;
};

// ── Document Settings / Logo ─────────────────────────────────────────────────

export const getDocumentSettings = async () => {
  const response = await axios.get(`${API}/document-settings/settings`);
  return response.data;
};

export const uploadLogo = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await axios.post(`${API}/document-settings/logo/upload`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};

export const deleteLogo = async () => {
  const response = await axios.delete(`${API}/document-settings/logo`);
  return response.data;
};
