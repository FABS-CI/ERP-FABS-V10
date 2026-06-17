/**
 * Service FNE — ERP FABS-CI V10
 * Facture Normalisée Électronique — DGI Côte d'Ivoire
 *
 * Couverture complète de tous les endpoints /fne/* du backend.
 */
import axios from "axios";
import API_BASE_URL from "../config/api";

const API = `${API_BASE_URL}/fne`;

// ─── Dashboard ───────────────────────────────────────────────────────────────
/** Statistiques globales FNE (total, certifiés, en attente…) */
export const getFNEStats = async () => (await axios.get(`${API}/dashboard/fne-stats`)).data;

/** Solde de timbres fiscaux restants chez la DGI */
export const getBalanceSticker = async () => (await axios.get(`${API}/dashboard/balance-sticker`)).data;

/** Détail stickers / répartition mensuelle */
export const getStickerDetail = async () => (await axios.get(`${API}/dashboard/stickers-detail`)).data;

// ─── Factures FNE ────────────────────────────────────────────────────────────
/** Liste paginée des factures FNE */
export const listFNEInvoices = async (params = {}) =>
  (await axios.get(`${API}/invoices`, { params })).data;

/** Statut FNE d'une facture (pending / submitted / accepted / rejected) */
export const getFNEStatus = async (invoiceId) =>
  (await axios.get(`${API}/invoices/${invoiceId}/status`)).data;

/** QR Code base64 d'une facture certifiée */
export const getFNEQRCode = async (invoiceId) =>
  (await axios.get(`${API}/invoices/${invoiceId}/qr-code`)).data;

/**
 * Soumet une facture directement à l'API DGI.
 * @param {Object} payload - FNEInvoice (reference, invoiceType, paymentMethod, template, items…)
 */
export const submitFNEInvoice = async (payload) =>
  (await axios.post(`${API}/invoices/submit`, payload)).data;

/**
 * Crée un avoir (refund) pour une facture déjà certifiée.
 * @param {string} invoiceId - ID DGI de la facture d'origine
 * @param {Array}  items     - [{id, quantity}]
 */
export const refundFNEInvoice = async (invoiceId, items = []) =>
  (await axios.post(`${API}/invoices/${invoiceId}/refund`, items)).data;

/**
 * Lance la certification FNE d'une facture existante dans l'ERP.
 * @param {string} factureId - facture_id interne ERP
 */
export const certifierFactureFNE = async (factureId) =>
  (await axios.post(`${API}/factures/${factureId}/certifier-fne`)).data;

// ─── Logs d'audit ────────────────────────────────────────────────────────────
/** Journal d'audit FNE (toutes soumissions DGI) */
export const listFNELogs = async (params = {}) =>
  (await axios.get(`${API}/logs`, { params })).data;

// ─── Paramètres ──────────────────────────────────────────────────────────────
/** Lit la configuration FNE courante (API KEY masquée) */
export const getFNESettings = async () => (await axios.get(`${API}/settings`)).data;

/**
 * Met à jour la configuration FNE (super_admin uniquement).
 * @param {Object} payload - FNESettingsUpdate (dgi_api_key, company_ncc, etc.)
 */
export const updateFNESettings = async (payload) =>
  (await axios.put(`${API}/settings`, payload)).data;

/** Teste la connectivité à l'URL DGI configurée */
export const pingDGI = async () => (await axios.post(`${API}/settings/ping`)).data;

// ─── Tests API DGI (onglet Tests) ────────────────────────────────────────────
/**
 * Test de signature facture — envoie une facture de test à l'API DGI.
 * Utile pour valider l'API KEY avant la mise en production.
 * @param {Object} overrides - Surcharges optionnelles (template, paymentMethod…)
 */
export const testSignInvoice = async (overrides = {}) => {
  const testPayload = {
    invoiceType: "sale",
    paymentMethod: "cash",
    template: "B2C",
    clientCompanyName: "Client Test FNE",
    clientPhone: "+2250700000000",
    clientEmail: "test@editionsfabsci.com",
    clientSellerName: "Vendeur Test",
    items: [
      {
        reference: "TEST-001",
        description: "Article test FNE",
        quantity: 1,
        amount: 1000,
        discount: 0,
        measurementUnit: "pcs",
        taxes: ["TVA"],
        customTaxes: [],
      },
    ],
    customTaxes: [],
    discount: 0,
    ...overrides,
  };
  return (await axios.post(`${API}/invoices/submit`, testPayload)).data;
};

/**
 * Test de certification B2B — facture avec NCC client.
 * @param {string} clientNcc - NCC du client (ex: "1234567X")
 */
export const testSignB2B = async (clientNcc = "1234567X") =>
  testSignInvoice({
    template: "B2B",
    clientNcc,
    clientCompanyName: "Entreprise Test B2B",
    paymentMethod: "transfer",
  });

/**
 * Test de certification B2G — facture gouvernementale.
 */
export const testSignB2G = async () =>
  testSignInvoice({
    template: "B2G",
    clientCompanyName: "Ministère Test",
    paymentMethod: "transfer",
  });

/**
 * Test d'avoir — créé un avoir sur une facture existante.
 * @param {string} invoiceId - ID DGI de la facture (ex: depuis testSignInvoice)
 * @param {Array}  items     - [{id, quantity}]
 */
export const testRefundInvoice = async (invoiceId, items) =>
  refundFNEInvoice(invoiceId, items);

/**
 * Test balance sticker — vérifie le solde de timbres chez la DGI.
 */
export const testBalanceSticker = async () => getBalanceSticker();
