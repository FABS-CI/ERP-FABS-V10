import axios from "axios";
import { getApiBase } from '../config/api';

const API = getApiBase("/bi-analytics");

// KPI Ventes
export const getKPIVentes = async (dateDebut, dateFin) => {
  const response = await axios.get(`${API}/kpi/ventes`, {
    params: { date_debut: dateDebut, date_fin: dateFin },
  });
  return response.data;
};

// KPI Logistique
export const getKPILogistique = async (dateDebut, dateFin) => {
  const response = await axios.get(`${API}/kpi/logistique`, {
    params: { date_debut: dateDebut, date_fin: dateFin },
  });
  return response.data;
};

// KPI Finance
export const getKPIFinance = async (dateDebut, dateFin) => {
  const response = await axios.get(`${API}/kpi/finance`, {
    params: { date_debut: dateDebut, date_fin: dateFin },
  });
  return response.data;
};

// Dashboard Global
export const getDashboardGlobal = async (jours = 30) => {
  const response = await axios.get(`${API}/dashboard`, { params: { jours } });
  return response.data;
};

// Forecasting
export const forecastVentes = async (mois = 3) => {
  const response = await axios.get(`${API}/forecast/ventes`, { params: { mois } });
  return response.data;
};

export const forecastDepenses = async (mois = 3) => {
  const response = await axios.get(`${API}/forecast/depenses`, { params: { mois } });
  return response.data;
};

// Analyses Avancées
export const analyseRentabiliteClient = async (dateDebut, dateFin) => {
  const response = await axios.get(`${API}/analyse/rentabilite-client`, {
    params: { date_debut: dateDebut, date_fin: dateFin },
  });
  return response.data;
};

export const analyseRentabiliteVehicule = async (dateDebut, dateFin) => {
  const response = await axios.get(`${API}/analyse/rentabilite-vehicule`, {
    params: { date_debut: dateDebut, date_fin: dateFin },
  });
  return response.data;
};
