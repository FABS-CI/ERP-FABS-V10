import axios from "axios";
import API_BASE_URL from "../config/api";
const API = API_BASE_URL;

// ============================================================================
// DASHBOARD RH
// ============================================================================
export async function getRHDashboard() {
  const r = await axios.get(`${API}/rh/dashboard`);
  return r.data;
}

export async function getRHAlertes() {
  const r = await axios.get(`${API}/rh/dashboard/alertes`);
  return r.data;
}

// ============================================================================
// EMPLOYES
// ============================================================================
export async function listEmployes({ q, departement_id, fonction_id, categorie_pro_id, statut, actif, limit = 50, skip = 0 } = {}) {
  const params = { limit, skip };
  if (q) params.q = q;
  if (departement_id) params.departement_id = departement_id;
  if (fonction_id) params.fonction_id = fonction_id;
  if (categorie_pro_id) params.categorie_pro_id = categorie_pro_id;
  if (statut) params.statut = statut;
  if (actif != null) params.actif = actif;
  const r = await axios.get(`${API}/rh/employes`, { params });
  return r.data;
}

export async function getEmploye(id) {
  const r = await axios.get(`${API}/rh/employes/${id}`);
  return r.data;
}

export async function createEmploye(payload) {
  const r = await axios.post(`${API}/rh/employes`, payload);
  return r.data;
}

export async function updateEmploye(id, payload) {
  const r = await axios.patch(`${API}/rh/employes/${id}`, payload);
  return r.data;
}

export async function disableEmploye(id) {
  const r = await axios.delete(`${API}/rh/employes/${id}`);
  return r.data;
}

// ============================================================================
// DEPARTEMENTS
// ============================================================================
export async function listDepartements({ actif } = {}) {
  const params = {};
  if (actif != null) params.actif = actif;
  const r = await axios.get(`${API}/rh/departements`, { params });
  return r.data;
}

export async function createDepartement(payload) {
  const r = await axios.post(`${API}/rh/departements`, payload);
  return r.data;
}

export async function updateDepartement(id, payload) {
  const r = await axios.patch(`${API}/rh/departements/${id}`, payload);
  return r.data;
}

export async function disableDepartement(id) {
  const r = await axios.delete(`${API}/rh/departements/${id}`);
  return r.data;
}

// ============================================================================
// FONCTIONS
// ============================================================================
export async function listFonctions({ actif } = {}) {
  const params = {};
  if (actif != null) params.actif = actif;
  const r = await axios.get(`${API}/rh/fonctions`, { params });
  return r.data;
}

export async function createFonction(payload) {
  const r = await axios.post(`${API}/rh/fonctions`, payload);
  return r.data;
}

export async function updateFonction(id, payload) {
  const r = await axios.patch(`${API}/rh/fonctions/${id}`, payload);
  return r.data;
}

export async function disableFonction(id) {
  const r = await axios.delete(`${API}/rh/fonctions/${id}`);
  return r.data;
}

// ============================================================================
// CATEGORIES PROFESSIONNELLES
// ============================================================================
export async function listCategoriesPro({ actif } = {}) {
  const params = {};
  if (actif != null) params.actif = actif;
  const r = await axios.get(`${API}/rh/categories-pro`, { params });
  return r.data;
}

export async function createCategoriePro(payload) {
  const r = await axios.post(`${API}/rh/categories-pro`, payload);
  return r.data;
}

export async function updateCategoriePro(id, payload) {
  const r = await axios.patch(`${API}/rh/categories-pro/${id}`, payload);
  return r.data;
}

export async function disableCategoriePro(id) {
  const r = await axios.delete(`${API}/rh/categories-pro/${id}`);
  return r.data;
}

// ============================================================================
// CONTRATS
// ============================================================================
export async function listContrats({ employe_id, type_contrat, statut, actif, limit = 50, skip = 0 } = {}) {
  const params = { limit, skip };
  if (employe_id) params.employe_id = employe_id;
  if (type_contrat) params.type_contrat = type_contrat;
  if (statut) params.statut = statut;
  if (actif != null) params.actif = actif;
  const r = await axios.get(`${API}/rh/contrats`, { params });
  return r.data;
}

export async function createContrat(payload) {
  const r = await axios.post(`${API}/rh/contrats`, payload);
  return r.data;
}

export async function updateContrat(id, payload) {
  const r = await axios.patch(`${API}/rh/contrats/${id}`, payload);
  return r.data;
}

export async function disableContrat(id) {
  const r = await axios.delete(`${API}/rh/contrats/${id}`);
  return r.data;
}

// ============================================================================
// CONGES
// ============================================================================
export async function listConges({ employe_id, statut, actif, limit = 50, skip = 0 } = {}) {
  const params = { limit, skip };
  if (employe_id) params.employe_id = employe_id;
  if (statut) params.statut = statut;
  if (actif != null) params.actif = actif;
  const r = await axios.get(`${API}/rh/conges`, { params });
  return r.data;
}

export async function createConge(payload) {
  const r = await axios.post(`${API}/rh/conges`, payload);
  return r.data;
}

export async function approuverCongeSup(id, payload) {
  const r = await axios.post(`${API}/rh/conges/${id}/approuver-sup`, payload);
  return r.data;
}

export async function approuverCongeDirection(id, payload) {
  const r = await axios.post(`${API}/rh/conges/${id}/approuver-direction`, payload);
  return r.data;
}

export async function approuverCongeRH(id, payload) {
  const r = await axios.post(`${API}/rh/conges/${id}/approuver-rh`, payload);
  return r.data;
}

// ============================================================================
// ABSENCES
// ============================================================================
export async function listAbsences({ employe_id, type_absence, actif, limit = 50, skip = 0 } = {}) {
  const params = { limit, skip };
  if (employe_id) params.employe_id = employe_id;
  if (type_absence) params.type_absence = type_absence;
  if (actif != null) params.actif = actif;
  const r = await axios.get(`${API}/rh/absences`, { params });
  return r.data;
}

export async function createAbsence(payload) {
  const r = await axios.post(`${API}/rh/absences`, payload);
  return r.data;
}

// ============================================================================
// MISSIONS
// ============================================================================
export async function listMissions({ employe_id, statut, actif, limit = 50, skip = 0 } = {}) {
  const params = { limit, skip };
  if (employe_id) params.employe_id = employe_id;
  if (statut) params.statut = statut;
  if (actif != null) params.actif = actif;
  const r = await axios.get(`${API}/rh/missions`, { params });
  return r.data;
}

export async function createMission(payload) {
  const r = await axios.post(`${API}/rh/missions`, payload);
  return r.data;
}

export async function cloturerMission(id, payload) {
  const r = await axios.post(`${API}/rh/missions/${id}/cloturer`, payload);
  return r.data;
}

// ============================================================================
// HABILITATIONS ERP
// ============================================================================
export async function listHabilitations({ employe_id, actif } = {}) {
  const params = {};
  if (employe_id) params.employe_id = employe_id;
  if (actif != null) params.actif = actif;
  const r = await axios.get(`${API}/rh/habilitations`, { params });
  return r.data;
}

export async function createHabilitation(payload) {
  const r = await axios.post(`${API}/rh/habilitations`, payload);
  return r.data;
}

// ============================================================================
// EVALUATIONS
// ============================================================================
export async function listEvaluations({ employe_id, type_evaluation, statut, actif, limit = 50, skip = 0 } = {}) {
  const params = { limit, skip };
  if (employe_id) params.employe_id = employe_id;
  if (type_evaluation) params.type_evaluation = type_evaluation;
  if (statut) params.statut = statut;
  if (actif != null) params.actif = actif;
  const r = await axios.get(`${API}/rh/evaluations`, { params });
  return r.data;
}

export async function createEvaluation(payload) {
  const r = await axios.post(`${API}/rh/evaluations`, payload);
  return r.data;
}

// ============================================================================
// DELEGATIONS
// ============================================================================
export async function listDelegations({ actif } = {}) {
  const params = {};
  if (actif != null) params.actif = actif;
  const r = await axios.get(`${API}/rh/delegations`, { params });
  return r.data;
}

export async function createDelegation(payload) {
  const r = await axios.post(`${API}/rh/delegations`, payload);
  return r.data;
}
