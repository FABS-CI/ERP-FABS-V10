/**
 * Service API — 2FA TOTP (ERP FABS-CI V10)
 * Endpoints : /auth/2fa/{status,setup,activate,verify,disable}
 */
import axios from "axios";
import API_BASE_URL from "../config/api";

const BASE = `${API_BASE_URL}/auth/2fa`;

/** Statut 2FA de l'utilisateur connecté */
export const get2FAStatus = async () => {
  const { data } = await axios.get(`${BASE}/status`);
  return data; // { enabled, required, role }
};

/** Initier le setup — retourne secret + QR code base64 */
export const setup2FA = async () => {
  const { data } = await axios.post(`${BASE}/setup`);
  return data; // { secret, qr_code_base64, otpauth_url, message }
};

/** Activer le 2FA après scan (valider le premier code) */
export const activate2FA = async (code) => {
  const { data } = await axios.post(`${BASE}/activate`, { code });
  return data; // { valid, message }
};

/** Vérifier un code TOTP (utilisé post-login) */
export const verify2FA = async (code) => {
  const { data } = await axios.post(`${BASE}/verify`, { code });
  return data; // { valid, message }
};

/** Désactiver le 2FA (code de confirmation requis, interdit super_admin) */
export const disable2FA = async (code) => {
  const { data } = await axios.post(`${BASE}/disable`, { code });
  return data; // { valid, message }
};
