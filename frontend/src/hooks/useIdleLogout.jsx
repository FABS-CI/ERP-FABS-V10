/**
 * useIdleLogout — Déconnexion automatique après inactivité
 * Timeout : 15 minutes
 * Avertissement : 2 minutes avant la déconnexion
 */
import { useEffect, useRef, useCallback, useState } from "react";

const IDLE_TIMEOUT_MS  = 15 * 60 * 1000; // 15 minutes
const WARN_BEFORE_MS   =  2 * 60 * 1000; //  2 minutes avant

const ACTIVITY_EVENTS = [
  "mousemove", "mousedown", "keydown",
  "touchstart", "scroll", "click", "focus"
];

export function useIdleLogout(logout, isAuthenticated) {
  const idleTimer   = useRef(null);
  const warnTimer   = useRef(null);
  const [showWarning, setShowWarning] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(0);
  const countdownRef = useRef(null);

  const clearTimers = useCallback(() => {
    clearTimeout(idleTimer.current);
    clearTimeout(warnTimer.current);
    clearInterval(countdownRef.current);
  }, []);

  const doLogout = useCallback(() => {
    clearTimers();
    setShowWarning(false);
    logout();
  }, [logout, clearTimers]);

  const startWarningCountdown = useCallback(() => {
    setShowWarning(true);
    setSecondsLeft(Math.floor(WARN_BEFORE_MS / 1000));
    countdownRef.current = setInterval(() => {
      setSecondsLeft(s => {
        if (s <= 1) {
          clearInterval(countdownRef.current);
          return 0;
        }
        return s - 1;
      });
    }, 1000);
  }, []);

  const resetTimers = useCallback(() => {
    if (!isAuthenticated) return;
    clearTimers();
    setShowWarning(false);

    // Avertissement 2 min avant expiration
    warnTimer.current = setTimeout(() => {
      startWarningCountdown();
    }, IDLE_TIMEOUT_MS - WARN_BEFORE_MS);

    // Déconnexion après 15 min
    idleTimer.current = setTimeout(() => {
      doLogout();
    }, IDLE_TIMEOUT_MS);
  }, [isAuthenticated, clearTimers, startWarningCountdown, doLogout]);

  // Rester connecté (bouton dans modal)
  const stayConnected = useCallback(() => {
    resetTimers();
  }, [resetTimers]);

  useEffect(() => {
    if (!isAuthenticated) {
      clearTimers();
      return;
    }

    resetTimers();

    const handleActivity = () => resetTimers();
    ACTIVITY_EVENTS.forEach(evt =>
      window.addEventListener(evt, handleActivity, { passive: true })
    );

    return () => {
      clearTimers();
      ACTIVITY_EVENTS.forEach(evt =>
        window.removeEventListener(evt, handleActivity)
      );
    };
  }, [isAuthenticated, resetTimers, clearTimers]);

  return { showWarning, secondsLeft, stayConnected, doLogout };
}
