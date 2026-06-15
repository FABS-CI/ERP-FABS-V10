import axios from "axios";
import { getApiBase } from '../config/api';

const API = getApiBase("/logistics-costs");

// Coûts Missions
export const listCoutsMissions = async (filters = {}) => {
  const response = await axios.get(`${API}/couts`, { params: filters });
  return response.data;
};

export const createCoutMission = async (data) => {
  const response = await axios.post(`${API}/couts`, data);
  return response.data;
};

export const updateCoutMission = async (coutId, data) => {
  const response = await axios.put(`${API}/couts/${coutId}`, data);
  return response.data;
};

// Rentabilité
export const getRentabiliteMission = async (missionId) => {
  const response = await axios.get(`${API}/rentabilite/${missionId}`);
  return response.data;
};

export const listRentabilite = async (filters = {}) => {
  const response = await axios.get(`${API}/rentabilite`, { params: filters });
  return response.data;
};

export const getRentabiliteParVehicule = async (filters = {}) => {
  const response = await axios.get(`${API}/vehicules/rentabilite`, { params: filters });
  return response.data;
};

// Rapports
export const getRapportCouts = async (dateDebut, dateFin) => {
  const response = await axios.get(`${API}/rapport`, {
    params: { date_debut: dateDebut, date_fin: dateFin },
  });
  return response.data;
};
