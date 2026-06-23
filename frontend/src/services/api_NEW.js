/**
 * ============================================================================
 * API SERVICE v2 — PHASE 3.2: HTTONLY COOKIES + CSRF
 * ============================================================================
 * 
 * CHANGES FROM v1:
 * ✅ Removed localStorage token injection (now in HttpOnly cookie)
 * ✅ Removed Authorization header injection (browser sends cookies)
 * ✅ Added CSRF token injection for POST/PUT/DELETE
 * ✅ Added 401 error handling (session expiry)
 * ✅ Simpler, safer, more standard
 * 
 * HOW IT WORKS:
 * 1. Browser automatically sends HttpOnly cookies on every request
 * 2. Backend validates session_token cookie (no header reading needed)
 * 3. For POST/PUT/DELETE, frontend adds X-CSRF-Token header
 * 4. Backend CSRFValidationMiddleware checks token
 * 5. On 401, axios interceptor triggers redirect
 * 
 * ============================================================================
 */

import axios from "axios";
import { API_BASE_URL } from "../config/api";
import { csrfStore } from "../hooks/useAuth";

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,  // ✅ Include cookies in requests
});

/**
 * ✅ Request Interceptor: Add CSRF token to state-changing operations
 */
api.interceptors.request.use((config) => {
  // Only add CSRF token to POST, PUT, DELETE, PATCH
  if (["post", "put", "delete", "patch"].includes(config.method?.toLowerCase())) {
    const csrfToken = csrfStore.get();
    if (csrfToken) {
      config.headers["X-CSRF-Token"] = csrfToken;
      // console.debug(`[API] Adding CSRF token to ${config.method.toUpperCase()} ${config.url}`);
    } else {
      // No CSRF token available — this might be first request
      // POST /api/auth/csrf can be called to get one
      console.warn(`[API] No CSRF token for ${config.method.toUpperCase()} ${config.url}`);
    }
  }
  
  return config;
});

/**
 * ✅ Response Interceptor: Handle session expiry & token rotation
 */
api.interceptors.response.use(
  (response) => {
    // ✅ Handle CSRF token rotation (optional)
    const newCsrfToken = response.headers["x-csrf-token"];
    if (newCsrfToken) {
      csrfStore.set(newCsrfToken);
    }
    
    return response;
  },
  (error) => {
    // ✅ Handle 401 (session expired)
    if (error.response?.status === 401) {
      csrfStore.clear();
      
      // Trigger auth expiry event
      window.dispatchEvent(new CustomEvent("auth:expired"));
      
      // Redirect after a delay (let components react first)
      setTimeout(() => {
        if (window.location.pathname !== "/login") {
          window.location.href = "/login?reason=session_expired";
        }
      }, 500);
    }
    
    return Promise.reject(error);
  }
);

export default api;

/**
 * ============================================================================
 * USAGE EXAMPLES
 * ============================================================================
 * 
 * BEFORE (v1 — localStorage JWT):
 * ```javascript
 * import api from "../services/api";
 * 
 * // axios was reading localStorage.getItem('fabs_token') on every request
 * const response = await api.get("/clients");
 * const response = await api.post("/clients", { nom_client: "Acme" });
 * ```
 * 
 * AFTER (v2 — HttpOnly cookies + CSRF):
 * ```javascript
 * import api from "../services/api";
 * 
 * // Browser auto-sends cookies, axios auto-adds CSRF token to POST
 * const response = await api.get("/clients");
 * const response = await api.post("/clients", { nom_client: "Acme" }); // CSRF added
 * ```
 * 
 * NO CODE CHANGES NEEDED IN CONSUMING COMPONENTS!
 * All API calls work the same, just more secure.
 * 
 * ============================================================================
 */
