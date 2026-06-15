/**
 * Service FNE — ERP FABS-CI V10 (Sprint 2)
 * Facture Normalisée Électronique — DGI Côte d'Ivoire
 */
import axios from "axios";
import API_BASE_URL from "../config/api";

const API = `${API_BASE_URL}/fne`;

// Dashboard
export const getFNEStats = async () => (await axios.get(`${API}/dashboard/fne-stats`)).data;
export const getBalanceSticker = async () => (await axios.get(`${API}/dashboard/balance-sticker`)).data;

// Factures FNE
export const listFNEInvoices = async (params = {}) => (await axios.get(`${API}/invoices`, { params })).data;
export const getFNEStatus = async (invoiceId) => (await axios.get(`${API}/invoices/${invoiceId}/status`)).data;
export const getFNEQRCode = async (invoiceId) => (await axios.get(`${API}/invoices/${invoiceId}/qr-code`)).data;
export const submitFNEInvoice = async (payload) => (await axios.post(`${API}/invoices/submit`, payload)).data;
export const refundFNEInvoice = async (invoiceId, payload = {}) => (await axios.post(`${API}/invoices/${invoiceId}/refund`, payload)).data;
export const certifierFactureFNE = async (factureId) => (await axios.post(`${API}/factures/${factureId}/certifier-fne`)).data;

// Logs
export const listFNELogs = async (params = {}) => (await axios.get(`${API}/logs`, { params })).data;

// Settings
export const getFNESettings = async () => (await axios.get(`${API}/settings`)).data;
export const pingDGI = async () => (await axios.post(`${API}/settings/ping`)).data;
export const getStickerDetail = async () => (await axios.get(`${API}/dashboard/stickers-detail`)).data;
