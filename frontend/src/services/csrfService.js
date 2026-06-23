/**
 * ============================================================================
 * CSRF SERVICE — PHASE 3.2
 * ============================================================================
 * 
 * Handles CSRF token acquisition and management
 * Can be called if CSRF token is needed but not available
 * 
 * Example:
 *   // On initial page load or if CSRF expired
 *   const token = await csrfService.getToken();
 * 
 * ============================================================================
 */

import axios from "axios";
import { csrfStore } from "../hooks/useAuth";

const API = "/api";

/**
 * Fetch CSRF token from backend
 * Backend will set csrf_token_hash cookie automatically
 */
export async function getCSRFToken() {
  try {
    const response = await axios.get(`${API}/auth/csrf`, {
      withCredentials: true,  // Include cookies
    });
    
    const { csrf_token, expires_in } = response.data;
    
    // Store token in memory
    csrfStore.set(csrf_token);
    
    console.debug(`[CSRF] Token obtained, expires in ${expires_in}s`);
    
    return csrf_token;
  } catch (error) {
    console.error("[CSRF] Failed to get token:", error);
    throw error;
  }
}

/**
 * Ensure CSRF token exists, fetch if needed
 * Safe to call multiple times
 */
export async function ensureCSRFToken() {
  if (csrfStore.get()) {
    return csrfStore.get();  // Already have token
  }
  return getCSRFToken();  // Fetch new one
}

/**
 * Reset CSRF token (on logout, session expiry, etc.)
 */
export function clearCSRFToken() {
  csrfStore.clear();
}

export default {
  getToken: getCSRFToken,
  ensureToken: ensureCSRFToken,
  clear: clearCSRFToken,
};
