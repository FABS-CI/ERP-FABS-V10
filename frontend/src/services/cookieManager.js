/**
 * Secure Cookie Manager
 * Handles secure cookie operations with HttpOnly, Secure, SameSite flags
 * Phase 3.5: Frontend Enhanced Security
 */

class CookieManager {
  constructor() {
    this.SECURE_COOKIE_OPTIONS = {
      httpOnly: true, // Can only be set by backend
      secure: process.env.NODE_ENV === 'production', // HTTPS only in prod
      sameSite: 'Strict', // CSRF protection
      maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
    };
    this.TOKEN_REFRESH_THRESHOLD = 24 * 60 * 60 * 1000; // Refresh 1 day before expiry
    this.cookieData = new Map(); // Client-side cache (non-sensitive)
    this._initTokenRefreshInterval();
  }

  /**
   * Set secure cookie (backend should do this, but validate here)
   */
  setSecureCookie(name, value, options = {}) {
    const finalOptions = { ...this.SECURE_COOKIE_OPTIONS, ...options };
    
    // Validate cookie value (prevent injection)
    if (this._isSuspiciousCookieValue(value)) {
      console.error(`❌ Suspicious cookie value detected for ${name}`);
      throw new Error('Invalid cookie value');
    }

    // Build cookie string
    const cookieParts = [`${name}=${encodeURIComponent(value)}`];
    
    if (finalOptions.maxAge) {
      cookieParts.push(`Max-Age=${finalOptions.maxAge}`);
    }
    if (finalOptions.secure) {
      cookieParts.push('Secure');
    }
    if (finalOptions.sameSite) {
      cookieParts.push(`SameSite=${finalOptions.sameSite}`);
    }
    if (finalOptions.path) {
      cookieParts.push(`Path=${finalOptions.path}`);
    }

    // Note: HttpOnly cannot be set from JavaScript - must come from backend
    const warningMsg = finalOptions.httpOnly ? 
      '⚠️  HttpOnly flag must be set by backend' : '';

    document.cookie = cookieParts.join('; ');
    console.log(`🍪 Cookie set: ${name} ${warningMsg}`);

    // Cache non-sensitive metadata
    this.cookieData.set(name, {
      setAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + (finalOptions.maxAge || 0)).toISOString(),
      isHttpOnly: finalOptions.httpOnly,
      isSecure: finalOptions.secure,
      sameSite: finalOptions.sameSite,
    });
  }

  /**
   * Get cookie value (will be empty for HttpOnly cookies)
   */
  getCookie(name) {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(`${name}=`)) {
        const value = cookie.substring(name.length + 1);
        return decodeURIComponent(value);
      }
    }
    return null;
  }

  /**
   * Get all cookie names (metadata only)
   */
  getAllCookieNames() {
    return Array.from(this.cookieData.keys());
  }

  /**
   * Remove cookie
   */
  removeCookie(name) {
    document.cookie = `${name}=; Max-Age=0; Path=/; SameSite=Strict`;
    this.cookieData.delete(name);
    console.log(`🗑️  Cookie removed: ${name}`);
  }

  /**
   * Clear all cookies
   */
  clearAllCookies() {
    this.cookieData.forEach((_, name) => {
      this.removeCookie(name);
    });
  }

  /**
   * Detect suspicious cookie values
   */
  _isSuspiciousCookieValue(value) {
    // Check for injection patterns
    const suspiciousPatterns = [
      /javascript:/i,
      /<script/i,
      /on\w+\s*=/i, // Event handlers
      /[\x00-\x1F]/, // Control characters
    ];

    return suspiciousPatterns.some(pattern => pattern.test(value));
  }

  /**
   * Get cookie metadata
   */
  getCookieMetadata(name) {
    return this.cookieData.get(name) || null;
  }

  /**
   * Check if cookie is HttpOnly (from metadata)
   */
  isHttpOnly(name) {
    const metadata = this.getCookieMetadata(name);
    return metadata?.isHttpOnly || false;
  }

  /**
   * Check if cookie is Secure
   */
  isSecure(name) {
    const metadata = this.getCookieMetadata(name);
    return metadata?.isSecure || false;
  }

  /**
   * Get cookie expiry
   */
  getCookieExpiry(name) {
    const metadata = this.getCookieMetadata(name);
    return metadata?.expiresAt ? new Date(metadata.expiresAt) : null;
  }

  /**
   * Check if cookie is about to expire
   */
  isAboutToExpire(name) {
    const expiry = this.getCookieExpiry(name);
    if (!expiry) return false;

    const timeLeft = expiry.getTime() - Date.now();
    return timeLeft < this.TOKEN_REFRESH_THRESHOLD;
  }

  /**
   * Initialize automatic token refresh
   */
  _initTokenRefreshInterval() {
    if (typeof window === 'undefined') return;

    // Check every 5 minutes if tokens need refresh
    setInterval(() => {
      this._checkAndRefreshTokens();
    }, 5 * 60 * 1000);
  }

  /**
   * Check and refresh tokens if needed
   */
  async _checkAndRefreshTokens() {
    const tokenName = 'auth_token';
    
    if (this.isAboutToExpire(tokenName)) {
      console.log('🔄 Token about to expire, requesting refresh...');
      try {
        await this._requestTokenRefresh();
      } catch (error) {
        console.error('Failed to refresh token:', error);
        // Force re-authentication
        window.location.href = '/login';
      }
    }
  }

  /**
   * Request token refresh from backend
   */
  async _requestTokenRefresh() {
    const response = await fetch('/api/auth/refresh-token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', // Include cookies
    });

    if (!response.ok) {
      throw new Error(`Token refresh failed: ${response.status}`);
    }

    console.log('✅ Token refreshed successfully');
    return response.json();
  }

  /**
   * Validate cookie security (debug)
   */
  validateCookieSecurity(name) {
    const metadata = this.getCookieMetadata(name);
    if (!metadata) {
      return { valid: false, reason: 'Cookie not found' };
    }

    const issues = [];

    if (!metadata.isHttpOnly) {
      issues.push('Not marked as HttpOnly');
    }
    if (process.env.NODE_ENV === 'production' && !metadata.isSecure) {
      issues.push('Not marked as Secure in production');
    }
    if (metadata.sameSite !== 'Strict') {
      issues.push(`SameSite is ${metadata.sameSite}, should be Strict`);
    }

    return {
      valid: issues.length === 0,
      issues,
      metadata,
    };
  }

  /**
   * Log cookie configuration
   */
  logCookieConfiguration() {
    console.group('🍪 Cookie Configuration');
    console.log('Environment:', process.env.NODE_ENV);
    console.log('Secure Flag:', this.SECURE_COOKIE_OPTIONS.secure);
    console.log('SameSite:', this.SECURE_COOKIE_OPTIONS.sameSite);
    console.log('Max Age:', this.SECURE_COOKIE_OPTIONS.maxAge);
    
    console.group('Cookies');
    this.cookieData.forEach((metadata, name) => {
      console.log(`${name}:`, metadata);
    });
    console.groupEnd();
    
    console.groupEnd();
  }
}

// Export singleton
export default new CookieManager();
