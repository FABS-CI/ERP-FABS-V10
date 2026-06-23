/**
 * Security Event Logger Service
 * Logs security-related events and sends to backend audit trail
 * Phase 3.5: Frontend Enhanced Security
 */

class SecurityEventLogger {
  constructor() {
    this.events = [];
    this.failedLoginAttempts = 0;
    this.lastLoginAttemptTime = null;
    this.rateLimitWindow = 60 * 1000; // 60 seconds
    this.maxFailedAttemptsPerWindow = 5;
    this.suspiciousBehaviors = [];
  }

  /**
   * Log authentication event
   */
  logAuthEvent(event_type, details = {}) {
    const event = {
      timestamp: new Date().toISOString(),
      event_type, // LOGIN_SUCCESS, LOGIN_FAILED, LOGOUT, etc.
      details,
      userAgent: navigator.userAgent.substring(0, 200),
      sourceUrl: window.location.href,
      timestamp: Date.now(),
    };

    this.events.push(event);
    console.log(`📝 Auth Event: ${event_type}`, details);

    // Send to backend immediately for critical events
    if (this._isCriticalEvent(event_type)) {
      this._sendToBackend(event);
    }
  }

  /**
   * Log failed login attempt
   */
  logFailedLogin(username, reason = 'unknown') {
    // Check rate limit
    const now = Date.now();
    if (this.lastLoginAttemptTime && now - this.lastLoginAttemptTime > this.rateLimitWindow) {
      // Reset counter if outside window
      this.failedLoginAttempts = 0;
    }

    this.failedLoginAttempts++;
    this.lastLoginAttemptTime = now;

    const event = {
      timestamp: new Date().toISOString(),
      event_type: 'LOGIN_FAILED',
      username: this._hashString(username), // Hash email
      reason,
      attempt_number: this.failedLoginAttempts,
      isRateLimited: this.failedLoginAttempts >= this.maxFailedAttemptsPerWindow,
    };

    this.events.push(event);

    console.warn(`⚠️  Login failed (attempt ${this.failedLoginAttempts}):`, reason);

    // Log suspicious behavior if rate limited
    if (this.failedLoginAttempts >= this.maxFailedAttemptsPerWindow) {
      this.logSuspiciousBehavior('multiple-failed-logins', {
        username: this._hashString(username),
        attempts: this.failedLoginAttempts,
        window: this.rateLimitWindow,
      });

      // Alert backend
      this._sendToBackend({
        ...event,
        alert_level: 'HIGH',
      });
    }
  }

  /**
   * Log successful login
   */
  logSuccessfulLogin(username) {
    // Reset failed attempts
    this.failedLoginAttempts = 0;

    const event = {
      timestamp: new Date().toISOString(),
      event_type: 'LOGIN_SUCCESS',
      username: this._hashString(username),
    };

    this.events.push(event);
    console.log('✅ Login successful');

    this._sendToBackend(event);
  }

  /**
   * Log logout
   */
  logLogout(reason = 'user-initiated') {
    const event = {
      timestamp: new Date().toISOString(),
      event_type: 'LOGOUT',
      reason,
    };

    this.events.push(event);
    console.log('👋 User logged out');

    this._sendToBackend(event);
  }

  /**
   * Log permission denied event
   */
  logPermissionDenied(resource, action) {
    const event = {
      timestamp: new Date().toISOString(),
      event_type: 'PERMISSION_DENIED',
      resource,
      action,
    };

    this.events.push(event);
    console.warn(`⚠️  Permission denied: ${action} on ${resource}`);

    this._sendToBackend(event);
  }

  /**
   * Log suspicious behavior
   */
  logSuspiciousBehavior(behavior_type, details = {}) {
    const event = {
      timestamp: new Date().toISOString(),
      behavior_type,
      details,
      sourceUrl: window.location.href,
      userAgent: navigator.userAgent.substring(0, 200),
    };

    this.suspiciousBehaviors.push(event);

    console.error(`❌ Suspicious behavior detected: ${behavior_type}`, details);

    // Always report suspicious behaviors
    this._sendToBackend({
      event_type: 'SUSPICIOUS_BEHAVIOR',
      ...event,
      alert_level: 'HIGH',
    });
  }

  /**
   * Log data access event
   */
  logDataAccess(resource_type, action, resource_id) {
    const event = {
      timestamp: new Date().toISOString(),
      event_type: 'DATA_ACCESS',
      resource_type,
      action,
      resource_id,
    };

    this.events.push(event);
    console.log(`📖 Data access: ${action} ${resource_type}/${resource_id}`);

    // Send batch reports
    if (this.events.length % 10 === 0) {
      this._sendBatchToBackend();
    }
  }

  /**
   * Determine if event is critical
   */
  _isCriticalEvent(event_type) {
    const criticalEvents = [
      'LOGIN_SUCCESS',
      'LOGIN_FAILED',
      'LOGOUT',
      'PERMISSION_DENIED',
      'SUSPICIOUS_BEHAVIOR',
    ];

    return criticalEvents.includes(event_type);
  }

  /**
   * Hash string (simple, for privacy)
   */
  _hashString(str) {
    if (!str) return '';
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return `hash_${Math.abs(hash).toString(16)}`;
  }

  /**
   * Send event to backend
   */
  async _sendToBackend(event) {
    try {
      const response = await fetch('/api/audit/security-event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          ...event,
          client_timestamp: new Date().toISOString(),
        }),
      });

      if (!response.ok) {
        console.warn('Failed to log security event to backend');
      }
    } catch (error) {
      console.error('Error sending security event to backend:', error);
    }
  }

  /**
   * Send batch of events to backend
   */
  async _sendBatchToBackend() {
    try {
      const eventBatch = this.events.splice(0, 10);

      const response = await fetch('/api/audit/security-events-batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          events: eventBatch,
          batch_size: eventBatch.length,
          client_timestamp: new Date().toISOString(),
        }),
      });

      if (!response.ok) {
        console.warn('Failed to log batch events to backend');
        // Return events to queue if failed
        this.events.unshift(...eventBatch);
      }
    } catch (error) {
      console.error('Error sending batch events:', error);
    }
  }

  /**
   * Get recent events
   */
  getRecentEvents(limit = 10) {
    return this.events.slice(-limit);
  }

  /**
   * Get all events
   */
  getAllEvents() {
    return [...this.events];
  }

  /**
   * Get suspicious behaviors
   */
  getSuspiciousBehaviors() {
    return [...this.suspiciousBehaviors];
  }

  /**
   * Clear events
   */
  clearEvents() {
    this.events = [];
    this.suspiciousBehaviors = [];
  }

  /**
   * Get event statistics
   */
  getStatistics() {
    const stats = {
      totalEvents: this.events.length,
      loginAttempts: this.events.filter(e => e.event_type === 'LOGIN_FAILED').length,
      suspiciousBehaviors: this.suspiciousBehaviors.length,
      dataAccessEvents: this.events.filter(e => e.event_type === 'DATA_ACCESS').length,
    };

    return stats;
  }

  /**
   * Log configuration
   */
  logConfiguration() {
    console.group('📝 Security Event Logger Configuration');
    console.log('Rate Limit Window:', this.rateLimitWindow, 'ms');
    console.log('Max Failed Attempts:', this.maxFailedAttemptsPerWindow);
    console.log('Total Events:', this.events.length);
    console.log('Suspicious Behaviors:', this.suspiciousBehaviors.length);
    console.log('Statistics:', this.getStatistics());
    console.groupEnd();
  }
}

// Export singleton
export default new SecurityEventLogger();
