/**
 * useNotifications — Hook React pour le moteur central de notifications ERP
 * Sprint 1 V10 — Notifications internes temps réel
 *
 * - Charge la liste initiale via REST
 * - Maintient un compteur de notifications non lues
 * - Ouvre une connexion WebSocket (auth par cookie httpOnly)
 * - Affiche un toast à la réception d'une nouvelle notification
 * - Joue un son à chaque nouvelle notification (Web Audio API)
 * - Reconnexion automatique avec backoff exponentiel
 */
import { useEffect, useRef, useState, useCallback } from "react";
import { toast } from "sonner";
import {
  listNotifications,
  countUnread,
  markAsRead as apiMarkAsRead,
  markAllAsRead as apiMarkAllAsRead,
} from "../services/notificationsService";
import { useAuth } from "./useAuth";

// ─── Son de notification via Web Audio API ────────────────────────────────────
function playNotificationSound(type = "info") {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();

    // Paramètres selon le type
    const configs = {
      success:  [{ f: 880, t: 0,    d: 0.12 }, { f: 1100, t: 0.13, d: 0.18 }],
      warning:  [{ f: 660, t: 0,    d: 0.15 }, { f: 550,  t: 0.17, d: 0.15 }],
      error:    [{ f: 440, t: 0,    d: 0.12 }, { f: 330,  t: 0.13, d: 0.2  }, { f: 220, t: 0.35, d: 0.25 }],
      info:     [{ f: 880, t: 0,    d: 0.15 }],
    };

    const notes = configs[type] || configs.info;
    const now = ctx.currentTime;

    notes.forEach(({ f, t, d }) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.type = "sine";
      osc.frequency.setValueAtTime(f, now + t);
      gain.gain.setValueAtTime(0.25, now + t);
      gain.gain.exponentialRampToValueAtTime(0.001, now + t + d);
      osc.start(now + t);
      osc.stop(now + t + d + 0.02);
    });

    // Fermer le contexte après le dernier son
    const lastNote = notes[notes.length - 1];
    setTimeout(() => ctx.close(), (lastNote.t + lastNote.d + 0.1) * 1000);
  } catch (e) {
    // Web Audio non disponible (headless, etc.) — silencieux
  }
}
// ─────────────────────────────────────────────────────────────────────────────

function buildWsUrl() {
  const apiBase = process.env.REACT_APP_BACKEND_URL || "";
  // apiBase = https://<host>  → ws scheme correspondant
  try {
    const u = new URL(apiBase);
    const scheme = u.protocol === "https:" ? "wss:" : "ws:";
    return `${scheme}//${u.host}/api/notifications/ws`;
  } catch {
    const scheme = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${scheme}//${window.location.host}/api/notifications/ws`;
  }
}

const MAX_BACKOFF_MS = 30_000;

export function useNotifications() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const closedManuallyRef = useRef(false);

  // --- REST helpers --------------------------------------------------------
  const refreshList = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    try {
      const data = await listNotifications({ limit: 20 });
      setItems(Array.isArray(data) ? data : []);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [user]);

  const refreshCount = useCallback(async () => {
    if (!user) return;
    try {
      const data = await countUnread();
      setCount(data?.count || 0);
    } catch {
      // ignore
    }
  }, [user]);

  const markAsRead = useCallback(async (notificationId) => {
    try {
      await apiMarkAsRead(notificationId);
      setItems((prev) =>
        prev.map((n) =>
          n.notification_id === notificationId ? { ...n, lue: true } : n
        )
      );
      setCount((c) => Math.max(0, c - 1));
    } catch {
      // ignore
    }
  }, []);

  const markAllAsRead = useCallback(async () => {
    try {
      await apiMarkAllAsRead();
      setItems((prev) => prev.map((n) => ({ ...n, lue: true })));
      setCount(0);
      toast.success("Toutes les notifications ont été marquées comme lues");
    } catch {
      toast.error("Erreur lors du marquage des notifications");
    }
  }, []);

  // --- WebSocket -----------------------------------------------------------
  const connectWs = useCallback(() => {
    if (!user) return;
    if (wsRef.current && wsRef.current.readyState <= 1) return;

    const url = buildWsUrl();
    let ws;
    try {
      ws = new WebSocket(url);
    } catch (e) {
      console.error("[notifications] WS construction error", e);
      return;
    }
    wsRef.current = ws;

    ws.onopen = () => {
      reconnectAttemptsRef.current = 0;
      setConnected(true);
      // Heartbeat toutes les 30s pour garder la connexion vivante
      ws._pingInterval = setInterval(() => {
        try {
          ws.send(JSON.stringify({ event: "ping" }));
        } catch {
          /* noop */
        }
      }, 30_000);
    };

    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        if (data.event === "notification:new") {
          setItems((prev) => [data, ...prev].slice(0, 50));
          setCount((c) => c + 1);
          // 🔔 Son de notification
          playNotificationSound(data.type || "info");
          // Toast utilisateur
          const variantFn =
            data.type === "error"
              ? toast.error
              : data.type === "warning"
              ? toast.warning
              : data.type === "success"
              ? toast.success
              : toast;
          variantFn(data.titre, {
            description: data.message,
            duration: 6000,
            action: data.lien
              ? { label: "Voir", onClick: () => window.location.assign(data.lien) }
              : undefined,
          });
        } else if (data.event === "notification:count") {
          setCount(data.count || 0);
        }
      } catch {
        /* ignore */
      }
    };

    ws.onerror = () => {
      // l'erreur sera suivie d'un onclose
    };

    ws.onclose = () => {
      setConnected(false);
      if (ws._pingInterval) clearInterval(ws._pingInterval);
      if (closedManuallyRef.current) return;
      const attempt = reconnectAttemptsRef.current + 1;
      reconnectAttemptsRef.current = attempt;
      const delay = Math.min(1000 * 2 ** attempt, MAX_BACKOFF_MS);
      setTimeout(() => {
        if (!closedManuallyRef.current) connectWs();
      }, delay);
    };
  }, [user]);

  useEffect(() => {
    closedManuallyRef.current = false;
    if (user) {
      refreshCount();
      refreshList();
      connectWs();
    }
    return () => {
      closedManuallyRef.current = true;
      if (wsRef.current) {
        try {
          if (wsRef.current._pingInterval) clearInterval(wsRef.current._pingInterval);
          wsRef.current.close();
        } catch {
          /* ignore */
        }
        wsRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.user_id]);

  return {
    items,
    count,
    loading,
    connected,
    refreshList,
    refreshCount,
    markAsRead,
    markAllAsRead,
  };
}
