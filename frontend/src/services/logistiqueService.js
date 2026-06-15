import axios from "axios";
import { getApiBase } from '../config/api';

const API = getApiBase("/logistique");

// Missions Logistiques
export const listMissions = async (filters = {}) => {
  const response = await axios.get(`${API}/missions`, { params: filters });
  return response.data;
};

export const getMission = async (missionId) => {
  const response = await axios.get(`${API}/missions/${missionId}`);
  return response.data;
};

export const createMission = async (data) => {
  const response = await axios.post(`${API}/missions`, data);
  return response.data;
};

export const updateMissionStatut = async (missionId, statut) => {
  const response = await axios.patch(`${API}/missions/${missionId}/statut`, null, {
    params: { statut },
  });
  return response.data;
};

// Véhicules
export const listVehicules = async (filters = {}) => {
  const response = await axios.get(`${API}/vehicules`, { params: filters });
  return response.data;
};

export const createVehicule = async (data) => {
  const response = await axios.post(`${API}/vehicules`, data);
  return response.data;
};

export const updateVehiculeStatut = async (vehiculeId, statut) => {
  const response = await axios.patch(`${API}/vehicules/${vehiculeId}/statut`, null, {
    params: { statut },
  });
  return response.data;
};

// Suivi Livraisons
export const listSuivi = async (filters = {}) => {
  const response = await axios.get(`${API}/suivi`, { params: filters });
  return response.data;
};

export const getSuiviExpedition = async (expeditionId) => {
  const response = await axios.get(`${API}/suivi/${expeditionId}`);
  return response.data;
};

export const createOrUpdateSuivi = async (expeditionId, data) => {
  const response = await axios.post(`${API}/suivi/${expeditionId}`, data);
  return response.data;
};
