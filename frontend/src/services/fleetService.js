import axios from "axios";
import { getApiBase } from '../config/api';

const API = getApiBase("/fleet");

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

export const checkVehiculeEligibilite = async (vehiculeId) => {
  const response = await axios.get(`${API}/vehicules/${vehiculeId}/eligibilite`);
  return response.data;
};

// Assurances
export const listAssurances = async (filters = {}) => {
  const response = await axios.get(`${API}/assurances`, { params: filters });
  return response.data;
};

export const createAssurance = async (data) => {
  const response = await axios.post(`${API}/assurances`, data);
  return response.data;
};

export const listAssurancesExpirantes = async (jours = 30) => {
  const response = await axios.get(`${API}/assurances/expirantes`, { params: { jours } });
  return response.data;
};

// Visites Techniques
export const listVisitesTechniques = async (filters = {}) => {
  const response = await axios.get(`${API}/visites-techniques`, { params: filters });
  return response.data;
};

export const createVisiteTechnique = async (data) => {
  const response = await axios.post(`${API}/visites-techniques`, data);
  return response.data;
};

export const listVisitesExpirantes = async (jours = 30) => {
  const response = await axios.get(`${API}/visites-techniques/expirantes`, { params: { jours } });
  return response.data;
};

// Maintenances
export const listMaintenances = async (filters = {}) => {
  const response = await axios.get(`${API}/maintenances`, { params: filters });
  return response.data;
};

export const createMaintenance = async (data) => {
  const response = await axios.post(`${API}/maintenances`, data);
  return response.data;
};

export const updateMaintenanceStatut = async (maintenanceId, statut) => {
  const response = await axios.patch(`${API}/maintenances/${maintenanceId}/statut`, null, {
    params: { statut },
  });
  return response.data;
};

// Affectations
export const listAffectations = async (filters = {}) => {
  const response = await axios.get(`${API}/affectations`, { params: filters });
  return response.data;
};

export const createAffectation = async (data) => {
  const response = await axios.post(`${API}/affectations`, data);
  return response.data;
};

export const retourAffectation = async (affectationId, kilometrageRetour) => {
  const response = await axios.patch(`${API}/affectations/${affectationId}/retour`, null, {
    params: { kilometrage_retour: kilometrageRetour },
  });
  return response.data;
};
