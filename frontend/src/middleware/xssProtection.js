/**
 * XSS Protection Middleware
 * Sanitizes and validates user input to prevent XSS attacks
 * Phase 3.5: Frontend Enhanced Security
 */

/**
 * DOMPurify-like sanitization (minimal, browser-native)
 * For production, use: npm install dompurify
 */
class XSSProtection {
  constructor() {
    this.dangerousPatterns = [
      /<script[^>]*>[\s\S]*?<\/script>/gi,
      /javascript:/gi,
      /on\w+\s*=/gi, // Event handlers
      /<iframe[^>]*>/gi,
      /<embed[^>]*>/gi,
      /<object[^>]*>/gi,
    ];
    this.xssAttempts = [];
  }

  /**
   * Sanitize user input
   */
  sanitizeInput(input, context = 'text') {
    if (!input) return input;

    let sanitized = input;

    // Trim whitespace
    if (typeof sanitized === 'string') {
      sanitized = sanitized.trim();
    }

    // Context-specific sanitization
    switch (context) {
      case 'html':
        sanitized = this._sanitizeHTML(sanitized);
        break;
      case 'url':
        sanitized = this._sanitizeURL(sanitized);
        break;
      case 'javascript':
        sanitized = this._sanitizeJavaScript(sanitized);
        break;
      case 'text':
      default:
        sanitized = this._sanitizeText(sanitized);
    }

    return sanitized;
  }

  /**
   * Sanitize text (most permissive)
   */
  _sanitizeText(input) {
    if (typeof input !== 'string') return input;

    let sanitized = input;

    // Remove control characters
    sanitized = sanitized.replace(/[\x00-\x1F\x7F]/g, '');

    // Check for patterns
    this._checkForSuspiciousPatterns(input, 'text');

    return sanitized;
  }

  /**
   * Sanitize HTML (strict)
   */
  _sanitizeHTML(input) {
    if (typeof input !== 'string') return input;

    let sanitized = input;

    // Remove all dangerous patterns
    this.dangerousPatterns.forEach(pattern => {
      if (pattern.test(sanitized)) {
        console.warn('⚠️  Dangerous pattern detected in HTML:', pattern);
        this._logXSSAttempt(input, 'html', pattern);
      }
      sanitized = sanitized.replace(pattern, '');
    });

    // Escape special characters
    sanitized = this._escapeHTML(sanitized);

    return sanitized;
  }

  /**
   * Sanitize URL
   */
  _sanitizeURL(input) {
    if (typeof input !== 'string') return input;

    // Only allow safe protocols
    const safeProtocols = ['http://', 'https://', 'mailto:', 'tel:', '/'];
    const isValid = safeProtocols.some(protocol => input.startsWith(protocol));

    if (!isValid) {
      console.warn('❌ Invalid URL protocol detected:', input);
      this._logXSSAttempt(input, 'url', 'invalid-protocol');
      return '#'; // Fallback
    }

    try {
      const url = new URL(input, window.location.origin);
      return url.toString();
    } catch {
      return '#';
    }
  }

  /**
   * Sanitize JavaScript
   */
  _sanitizeJavaScript(input) {
    if (typeof input !== 'string') return input;

    // Never execute user-provided JavaScript
    // This should be treated as an error condition
    if (input.match(/[\s\S]/)) {
      console.error('❌ Attempted to sanitize JavaScript (should never happen)');
      this._logXSSAttempt(input, 'javascript', 'eval-attempt');
      throw new Error('User input cannot be evaluated as JavaScript');
    }

    return input;
  }

  /**
   * Check for suspicious patterns
   */
  _checkForSuspiciousPatterns(input, context) {
    const suspiciousPatterns = [
      /javascript:/i,
      /<script/i,
      /on\w+\s*=/i,
      /alert\s*\(/i,
      /eval\s*\(/i,
      /expression\s*\(/i,
    ];

    for (const pattern of suspiciousPatterns) {
      if (pattern.test(input)) {
        console.warn(`⚠️  Suspicious pattern detected (${context}):`, pattern);
        this._logXSSAttempt(input, context, pattern.toString());
        return true;
      }
    }

    return false;
  }

  /**
   * Escape HTML special characters
   */
  _escapeHTML(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
    };

    return text.replace(/[&<>"']/g, char => map[char]);
  }

  /**
   * Unescape HTML (use with caution)
   */
  unescapeHTML(text) {
    const textarea = document.createElement('textarea');
    textarea.innerHTML = text;
    return textarea.value;
  }

  /**
   * Validate input length
   */
  validateLength(input, max, context = 'unknown') {
    if (!input) return true;

    const length = typeof input === 'string' ? input.length : JSON.stringify(input).length;

    if (length > max) {
      console.warn(`⚠️  Input exceeds max length (${context}): ${length} > ${max}`);
      this._logXSSAttempt(input, context, `length-exceeded:${length}:${max}`);
      return false;
    }

    return true;
  }

  /**
   * Log XSS attempt
   */
  _logXSSAttempt(input, context, pattern) {
    const attempt = {
      timestamp: new Date().toISOString(),
      context,
      pattern: pattern.toString().substring(0, 100),
      inputLength: input.length,
      sourceUrl: window.location.href,
      userAgent: navigator.userAgent.substring(0, 100),
    };

    this.xssAttempts.push(attempt);

    // Report to backend if critical
    if (this.xssAttempts.length % 5 === 0) {
      this._reportToBackend(attempt);
    }
  }

  /**
   * Report attempt to backend
   */
  async _reportToBackend(attempt) {
    try {
      await fetch('/api/audit/xss-attempt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          event_type: 'XSS_ATTEMPT',
          details: attempt,
          timestamp: new Date().toISOString(),
        }),
      });
    } catch (error) {
      console.error('Error reporting XSS attempt:', error);
    }
  }

  /**
   * Get recorded XSS attempts
   */
  getAttempts() {
    return [...this.xssAttempts];
  }

  /**
   * Clear attempts log
   */
  clearAttempts() {
    this.xssAttempts = [];
  }

  /**
   * Create safe DOM element
   */
  createSafeElement(tagName, content, attributes = {}) {
    const element = document.createElement(tagName);

    // Set text content (safe from XSS)
    if (content && typeof content === 'string') {
      element.textContent = this.sanitizeInput(content, 'text');
    }

    // Set attributes safely
    Object.entries(attributes).forEach(([key, value]) => {
      if (value && typeof value === 'string') {
        const sanitized = this.sanitizeInput(value, 'text');
        element.setAttribute(key, sanitized);
      }
    });

    return element;
  }

  /**
   * Log XSS protection configuration
   */
  logConfiguration() {
    console.group('🔒 XSS Protection Configuration');
    console.log('Dangerous Patterns Count:', this.dangerousPatterns.length);
    console.log('Total Attempts Blocked:', this.xssAttempts.length);
    console.log('Recent Attempts:', this.xssAttempts.slice(-5));
    console.groupEnd();
  }
}

// Export singleton
export default new XSSProtection();
