/**
 * IdleWarningModal — Modal d'avertissement avant déconnexion automatique
 */
import React from "react";

export default function IdleWarningModal({ secondsLeft, onStay, onLogout }) {
  const minutes = Math.floor(secondsLeft / 60);
  const secs    = secondsLeft % 60;
  const timeStr = minutes > 0
    ? `${minutes}:${String(secs).padStart(2, "0")}`
    : `${secs}s`;

  return (
    <div style={overlay}>
      <div style={modal}>
        {/* Icône */}
        <div style={iconWrap}>
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none"
               stroke="#f59e0b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        </div>

        <h2 style={title}>Session sur le point d'expirer</h2>
        <p style={subtitle}>
          Vous allez être déconnecté automatiquement dans
        </p>

        <div style={countdown}>{timeStr}</div>

        <p style={hint}>
          En raison d'inactivité. Cliquez sur <strong>Rester connecté</strong> pour continuer.
        </p>

        <div style={btnRow}>
          <button style={btnSecondary} onClick={onLogout}>
            Se déconnecter
          </button>
          <button style={btnPrimary} onClick={onStay}>
            Rester connecté
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Styles inline ────────────────────────────────────────────────────────────

const overlay = {
  position: "fixed", inset: 0,
  background: "rgba(0,0,0,0.55)",
  display: "flex", alignItems: "center", justifyContent: "center",
  zIndex: 9999,
  backdropFilter: "blur(3px)",
};

const modal = {
  background: "#fff",
  borderRadius: 16,
  padding: "40px 36px 32px",
  maxWidth: 420, width: "90%",
  textAlign: "center",
  boxShadow: "0 20px 60px rgba(0,0,0,0.2)",
};

const iconWrap = {
  marginBottom: 16,
};

const title = {
  fontSize: 20, fontWeight: 700,
  color: "#1e293b", margin: "0 0 8px",
};

const subtitle = {
  fontSize: 14, color: "#64748b", margin: "0 0 16px",
};

const countdown = {
  fontSize: 48, fontWeight: 800,
  color: "#ef4444",
  letterSpacing: "-1px",
  margin: "0 0 16px",
  fontVariantNumeric: "tabular-nums",
};

const hint = {
  fontSize: 13, color: "#94a3b8", margin: "0 0 28px",
};

const btnRow = {
  display: "flex", gap: 12, justifyContent: "center",
};

const btnPrimary = {
  padding: "10px 24px",
  background: "#2563eb", color: "#fff",
  border: "none", borderRadius: 8,
  fontSize: 14, fontWeight: 600,
  cursor: "pointer",
};

const btnSecondary = {
  padding: "10px 24px",
  background: "#f1f5f9", color: "#64748b",
  border: "none", borderRadius: 8,
  fontSize: 14, fontWeight: 600,
  cursor: "pointer",
};
