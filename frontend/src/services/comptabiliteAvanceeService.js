import axios from "axios";
import { getApiBase } from '../config/api';

const API = getApiBase("/comptabilite-avancee");

// Plan Comptable
export const listPlanComptable = async (filters = {}) => {
  const response = await axios.get(`${API}/plan-comptable`, { params: filters });
  return response.data;
};

export const createCompteComptable = async (data) => {
  const response = await axios.post(`${API}/plan-comptable`, data);
  return response.data;
};

// Journaux Comptables
export const listJournaux = async () => {
  const response = await axios.get(`${API}/journaux`);
  return response.data;
};

export const createJournal = async (data) => {
  const response = await axios.post(`${API}/journaux`, data);
  return response.data;
};

// Écritures Comptables
export const listEcritures = async (filters = {}) => {
  const response = await axios.get(`${API}/ecritures`, { params: filters });
  return response.data;
};

export const createEcriture = async (data) => {
  const response = await axios.post(`${API}/ecritures`, data);
  return response.data;
};

export const generateEcritureFacture = async (factureId) => {
  const response = await axios.post(`${API}/ecritures/auto/facture/${factureId}`);
  return response.data;
};

export const generateEcriturePaiement = async (paiementId) => {
  const response = await axios.post(`${API}/ecritures/auto/paiement/${paiementId}`);
  return response.data;
};

// Rapprochement Bancaire
export const listRapprochements = async (filters = {}) => {
  const response = await axios.get(`${API}/rapprochements`, { params: filters });
  return response.data;
};

export const createRapprochement = async (data) => {
  const response = await axios.post(`${API}/rapprochements`, data);
  return response.data;
};
