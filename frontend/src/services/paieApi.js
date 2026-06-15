import axios from "axios";
import API_BASE_URL from "../config/api";

const API = `${API_BASE_URL}/paie`;

export const calculerPaie = async (payload) => (await axios.post(`${API}/calculer`, payload)).data;
export const creerBulletin = async (payload) => (await axios.post(`${API}/bulletins`, payload)).data;
export const listerBulletins = async (params = {}) => (await axios.get(`${API}/bulletins`, { params })).data;
export const getBulletin = async (id) => (await axios.get(`${API}/bulletins/${id}`)).data;
export const getBareme = async () => (await axios.get(`${API}/bareme`)).data;
