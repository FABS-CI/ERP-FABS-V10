import axios from "axios";
import { getApiBase } from '../config/api';

const API = getApiBase("/notifications");

// ============================================================================
// WEBSOCKET REAL-TIME NOTIFICATIONS
// ============================================================================

class NotificationWebSocketManager {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000;
    this.listeners = new Set();
    this.connected = false;
  }

  /**
   * Connect to WebSocket for real-time notifications
   * Callbacks: onMessage(payload), onConnect(), onDisconnect()
   */
  connect(onMessage, onConnect = null, onDisconnect = null) {
    const token = localStorage.getItem("session_token") || sessionStorage.getItem("session_token");
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsHost = window.location.host;
    const wsUrl = `${wsProtocol}//${wsHost}/api/notifications/ws${token ? `?token=${token}` : ""}`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log("[NotifWS] Connected");
        this.connected = true;
        this.reconnectAttempts = 0;
        if (onConnect) onConnect();
      };

      this.ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          console.log("[NotifWS] Message:", payload);

          // Play sound on new notification
          if (payload.event === "notification:new") {
            this.playNotificationSound();
          }

          if (onMessage) onMessage(payload);
          this.notifyListeners(payload);
        } catch (err) {
          console.error("[NotifWS] Parse error:", err);
        }
      };

      this.ws.onerror = (error) => {
        console.error("[NotifWS] Error:", error);
      };

      this.ws.onclose = () => {
        console.log("[NotifWS] Disconnected");
        this.connected = false;
        if (onDisconnect) onDisconnect();
        this.attemptReconnect(onMessage, onConnect, onDisconnect);
      };
    } catch (err) {
      console.error("[NotifWS] Connection error:", err);
    }
  }

  attemptReconnect(onMessage, onConnect, onDisconnect) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`[NotifWS] Reconnecting (attempt ${this.reconnectAttempts})...`);
      setTimeout(() => {
        this.connect(onMessage, onConnect, onDisconnect);
      }, this.reconnectDelay);
    } else {
      console.error("[NotifWS] Max reconnect attempts reached");
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.connected = false;
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  ping() {
    this.send({ event: "ping" });
  }

  playNotificationSound() {
    try {
      const audio = new Audio("/sounds/notification.mp3");
      audio.volume = 0.5; // 50% volume
      audio.play().catch((err) => {
        console.warn("[NotifWS] Could not play sound:", err);
      });
    } catch (err) {
      console.warn("[NotifWS] Sound error:", err);
    }
  }

  subscribe(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  notifyListeners(payload) {
    this.listeners.forEach((cb) => cb(payload));
  }
}

// Global instance
export const notificationWsManager = new NotificationWebSocketManager();

// Notifications
export const listNotifications = async (filters = {}) => {
  const response = await axios.get(`${API}`, { params: filters });
  return response.data;
};

export const listUnreadNotifications = async () => {
  const response = await axios.get(`${API}/non-lues`);
  return response.data;
};

export const countUnread = async () => {
  const response = await axios.get(`${API}/count`);
  return response.data;
};

export const markAsRead = async (notificationId) => {
  const response = await axios.patch(`${API}/${notificationId}/lire`);
  return response.data;
};

export const markAllAsRead = async () => {
  const response = await axios.patch(`${API}/tout-lire`);
  return response.data;
};

export const deleteNotification = async (notificationId) => {
  const response = await axios.delete(`${API}/${notificationId}`);
  return response.data;
};

// Préférences
export const getPreferences = async () => {
  const response = await axios.get(`${API}/preferences`);
  return response.data;
};

export const updatePreferences = async (data) => {
  const response = await axios.put(`${API}/preferences`, data);
  return response.data;
};

// Email Templates (Admin)
export const listEmailTemplates = async () => {
  const response = await axios.get(`${API}/templates`);
  return response.data;
};

export const createEmailTemplate = async (data) => {
  const response = await axios.post(`${API}/templates`, data);
  return response.data;
};

export const updateEmailTemplate = async (templateId, data) => {
  const response = await axios.put(`${API}/templates/${templateId}`, data);
  return response.data;
};

export const deleteEmailTemplate = async (templateId) => {
  const response = await axios.delete(`${API}/templates/${templateId}`);
  return response.data;
};

// Email Logs (Admin)
export const listEmailLogs = async (filters = {}) => {
  const response = await axios.get(`${API}/logs`, { params: filters });
  return response.data;
};

// Test
export const sendTestNotification = async () => {
  const response = await axios.post(`${API}/test`);
  return response.data;
};
