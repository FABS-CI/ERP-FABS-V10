/**
 * CORS Validator Service
 * Validates CORS headers and enforces origin whitelist
 * Phase 3.5: Frontend Enhanced Security
 */

class CORSValidator {
  constructor() {
    this.allowedOrigins = this._buildAllowedOrigins();
    this.corsViolations = [];
    this.corsSuccesses = [];
  }

  /**
   * Build allowed origins from environment
   */
  _buildAllowedOrigins() {
    const baseOrigins = [
      window.location.origin, // Current origin
    ];

    // Add development origins
    if (process.env.NODE_ENV === 'development') {
      baseOrigins.push('http://localhost:3000');
      baseOrigins.push('http://localhost:8002');
      baseOrigins.push('https://localhost:8443');
      baseOrigins.push('http://127.0.0.1:3000');
      baseOrigins.push('https://127.0.0.1:8443');
    }

    // Add production origins
    if (process.env.NODE_ENV === 'production') {
      const prodOrigins = (process.env.REACT_APP_ALLOWED_ORIGINS || '').split(',');
      baseOrigins.push(...prodOrigins.map(o => o.trim()).filter(Boolean));
    }

    return new Set(baseOrigins);
  }

  /**
   * Add allowed origin
   */
  addAllowedOrigin(origin) {
    // Validate origin format
    if (!this._isValidOrigin(origin)) {
      console.warn(`❌ Invalid origin format: ${origin}`);
      return false;
    }
    this.allowedOrigins.add(origin);
    return true;
  }

  /**
   * Remove allowed origin
   */
  removeAllowedOrigin(origin) {
    return this.allowedOrigins.delete(origin);
  }

  /**
   * Get all allowed origins
   */
  getAllowedOrigins() {
    return Array.from(this.allowedOrigins);
  }

  /**
   * Validate origin format
   */
  _isValidOrigin(origin) {
    try {
      const url = new URL(origin);
      return ['http:', 'https:'].includes(url.protocol);
    } catch {
      return false;
    }
  }

  /**
   * Validate CORS headers in response
   */
  validateCORSResponse(response) {
    const origin = window.location.origin;
    const allowedOrigin = response.headers.get('access-control-allow-origin');
    const allowedMethods = response.headers.get('access-control-allow-methods');
    const allowedHeaders = response.headers.get('access-control-allow-headers');
    const credentials = response.headers.get('access-control-allow-credentials');

    const validation = {
      timestamp: new Date().toISOString(),
      url: response.url,
      origin,
      headers: {
        allowedOrigin,
        allowedMethods,
        allowedHeaders,
        credentials,
      },
      isValid: true,
      issues: [],
    };

    // Check if response has CORS headers
    if (!allowedOrigin && !allowedMethods) {
      validation.issues.push('No CORS headers found in response');
    }

    // Validate allowed origin
    if (allowedOrigin && allowedOrigin !== '*') {
      if (!this.allowedOrigins.has(allowedOrigin)) {
        validation.isValid = false;
        validation.issues.push(`Unknown origin: ${allowedOrigin}`);
      }
    }

    // Warn about wildcard origin
    if (allowedOrigin === '*') {
      validation.issues.push('CORS allows wildcard origin (*)');
    }

    // Check credentials flag
    if (credentials === 'true' && allowedOrigin === '*') {
      validation.isValid = false;
      validation.issues.push('Cannot use credentials with wildcard CORS');
    }

    if (!validation.isValid) {
      this.corsViolations.push(validation);
      console.error('❌ CORS validation failed:', validation);
      this._reportCORSViolation(validation);
    } else {
      this.corsSuccesses.push(validation);
    }

    return validation;
  }

  /**
   * Validate fetch request origin
   */
  validateFetchOrigin(url) {
    try {
      const requestUrl = new URL(url, window.location.origin);
      const requestOrigin = requestUrl.origin;

      // Same-origin requests are always allowed
      if (requestOrigin === window.location.origin) {
        return { allowed: true, reason: 'same-origin' };
      }

      // Check if in whitelist
      if (this.allowedOrigins.has(requestOrigin)) {
        return { allowed: true, reason: 'whitelisted' };
      }

      return { 
        allowed: false, 
        reason: 'unknown-origin',
        origin: requestOrigin,
      };
    } catch (error) {
      return { allowed: false, reason: 'invalid-url', error };
    }
  }

  /**
   * Report CORS violation to backend
   */
  async _reportCORSViolation(validation) {
    try {
      await fetch('/api/audit/cors-violation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          event_type: 'CORS_VIOLATION',
          details: validation,
          timestamp: new Date().toISOString(),
        }),
      });
    } catch (error) {
      console.error('Error reporting CORS violation:', error);
    }
  }

  /**
   * Get CORS violations
   */
  getViolations() {
    return [...this.corsViolations];
  }

  /**
   * Get CORS successes
   */
  getSuccesses() {
    return [...this.corsSuccesses];
  }

  /**
   * Clear logs
   */
  clearLogs() {
    this.corsViolations = [];
    this.corsSuccesses = [];
  }

  /**
   * Log CORS configuration
   */
  logCORSConfiguration() {
    console.group('🔒 CORS Configuration');
    console.log('Current Origin:', window.location.origin);
    console.log('Allowed Origins:', this.getAllowedOrigins());
    console.log('Violations:', this.corsViolations.length);
    console.log('Successes:', this.corsSuccesses.length);
    console.groupEnd();
  }
}

// Export singleton
export default new CORSValidator();
