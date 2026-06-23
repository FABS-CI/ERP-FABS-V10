/**
 * Security Headers Service
 * Manages Content Security Policy, SRI validation, and security headers
 * Phase 3.5: Frontend Enhanced Security
 */

const DEFAULT_CSP = {
  'default-src': ["'self'"],
  'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"], // Remove unsafe-* in prod
  'style-src': ["'self'", "'unsafe-inline'", 'https://fonts.googleapis.com'],
  'img-src': ["'self'", 'data:', 'blob:', 'https:'],
  'font-src': ["'self'", 'data:', 'https://fonts.gstatic.com'],
  'connect-src': ["'self'", 'https://localhost:8443', 'https://localhost:3000'],
  'frame-ancestors': ["'none'"],
  'base-uri': ["'self'"],
  'form-action': ["'self'"],
  'object-src': ["'none'"],
  'upgrade-insecure-requests': [],
};

const ENVIRONMENT_CSP = {
  development: {
    'connect-src': ["'self'", 'https://localhost:8443', 'http://localhost:8002', 'ws://localhost:*', 'wss://localhost:*'],
    'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
  },
  production: {
    'connect-src': ["'self'", 'https://api.fabsci.com'],
    'script-src': ["'self'"],
    'style-src': ["'self'", 'https://fonts.googleapis.com'],
    'upgrade-insecure-requests': [],
  },
};

class SecurityHeadersService {
  constructor() {
    this.environment = process.env.NODE_ENV || 'development';
    this.cspPolicy = this._buildCSP();
    this.cspViolations = [];
    this.sri_hashes = new Map();
    this._initCSPReporting();
  }

  /**
   * Build final CSP policy from defaults + environment overrides
   */
  _buildCSP() {
    const policy = { ...DEFAULT_CSP };
    const envOverrides = ENVIRONMENT_CSP[this.environment] || {};
    
    Object.keys(envOverrides).forEach(directive => {
      if (envOverrides[directive].length > 0) {
        policy[directive] = envOverrides[directive];
      }
    });
    
    return policy;
  }

  /**
   * Get CSP string for meta tag or header
   */
  getCSPString() {
    return Object.entries(this.cspPolicy)
      .map(([directive, sources]) => {
        if (sources.length === 0) return directive;
        return `${directive} ${sources.join(' ')}`;
      })
      .join('; ');
  }

  /**
   * Inject CSP meta tag into document head
   */
  injectCSPMetaTag() {
    if (typeof document === 'undefined') return;

    // Check if already injected
    const existing = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
    if (existing) return;

    const meta = document.createElement('meta');
    meta.httpEquiv = 'Content-Security-Policy';
    meta.content = this.getCSPString();
    document.head.appendChild(meta);

    console.log('🔒 CSP meta tag injected');
  }

  /**
   * Listen for CSP violations
   */
  _initCSPReporting() {
    if (typeof document === 'undefined') return;

    document.addEventListener('securitypolicyviolation', (event) => {
      const violation = {
        timestamp: new Date().toISOString(),
        violatedDirective: event.violatedDirective,
        blockedURI: event.blockedURI,
        sourceFile: event.sourceFile,
        lineNumber: event.lineNumber,
        columnNumber: event.columnNumber,
        originalPolicy: event.originalPolicy,
        disposition: event.disposition, // 'enforce' or 'report'
      };

      this.cspViolations.push(violation);

      console.warn('⚠️  CSP Violation:', violation);

      // Log to backend if critical
      if (this._isCriticalViolation(violation)) {
        this._reportViolationToBackend(violation);
      }
    });
  }

  /**
   * Determine if violation is critical
   */
  _isCriticalViolation(violation) {
    const criticalDirectives = ['script-src', 'object-src', 'base-uri'];
    return criticalDirectives.includes(violation.violatedDirective);
  }

  /**
   * Report violation to backend audit trail
   */
  async _reportViolationToBackend(violation) {
    try {
      const response = await fetch('/api/audit/security-violation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          event_type: 'CSP_VIOLATION',
          details: violation,
          user_agent: navigator.userAgent,
          url: window.location.href,
        }),
      });

      if (!response.ok) {
        console.error('Failed to report CSP violation to backend');
      }
    } catch (error) {
      console.error('Error reporting CSP violation:', error);
    }
  }

  /**
   * Get CSP violations recorded so far
   */
  getViolations() {
    return [...this.cspViolations];
  }

  /**
   * Clear violations log
   */
  clearViolations() {
    this.cspViolations = [];
  }

  /**
   * Register SRI hash for external resource
   */
  registerSRIHash(url, algorithm = 'sha384', hash) {
    this.sri_hashes.set(url, { algorithm, hash });
  }

  /**
   * Get SRI integrity attribute
   */
  getSRIAttribute(url) {
    const sri = this.sri_hashes.get(url);
    if (!sri) return null;
    return `${sri.algorithm}-${sri.hash}`;
  }

  /**
   * Validate external resource integrity
   */
  validateResourceIntegrity(url, resourceElement) {
    const expected = this.sri_hashes.get(url);
    if (!expected) {
      console.warn(`⚠️  No SRI hash registered for: ${url}`);
      return true; // Allow if not registered
    }

    const actual = resourceElement.integrity || '';
    const expectedAttr = `${expected.algorithm}-${expected.hash}`;

    if (actual !== expectedAttr) {
      console.error(`❌ SRI mismatch for ${url}`);
      this._reportIntegrityFailure(url, expected, actual);
      return false;
    }

    return true;
  }

  /**
   * Report integrity failure
   */
  async _reportIntegrityFailure(url, expected, actual) {
    try {
      await fetch('/api/audit/integrity-failure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          event_type: 'SRI_FAILURE',
          url,
          expected,
          actual,
          timestamp: new Date().toISOString(),
        }),
      });
    } catch (error) {
      console.error('Error reporting integrity failure:', error);
    }
  }

  /**
   * Add directive to CSP (runtime)
   */
  addDirective(directive, sources = []) {
    if (!this.cspPolicy[directive]) {
      this.cspPolicy[directive] = [];
    }
    this.cspPolicy[directive] = [...new Set([...this.cspPolicy[directive], ...sources])];
  }

  /**
   * Remove directive from CSP (runtime)
   */
  removeDirective(directive) {
    delete this.cspPolicy[directive];
  }

  /**
   * Get CSP policy object
   */
  getPolicy() {
    return { ...this.cspPolicy };
  }

  /**
   * Get environment
   */
  getEnvironment() {
    return this.environment;
  }
}

// Export singleton
export default new SecurityHeadersService();
