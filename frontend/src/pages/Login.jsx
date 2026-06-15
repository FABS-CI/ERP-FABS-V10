import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { Mail, Lock, Loader2, ArrowRight, Eye, EyeOff } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { COMPANY } from "../constants/company";

function formatApiErrorDetail(detail) {
  if (detail == null) return "Une erreur est survenue. Veuillez réessayer.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail.map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e))).filter(Boolean).join(" ");
  if (detail && typeof detail.msg === "string") return detail.msg;
  return String(detail);
}

export default function Login() {
  const { user, isLoading, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPwd, setShowPwd] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "#0B1220" }}>
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 rounded-full border-2 border-[#F97316] border-t-transparent animate-spin" />
          <p style={{ color: "#94A3B8", fontSize: "14px" }}>Chargement…</p>
        </div>
      </div>
    );
  }
  if (user) return <Navigate to="/dashboard" replace />;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!email || !password) { setError("Email et mot de passe requis"); return; }
    setSubmitting(true);
    try {
      await login(email.trim().toLowerCase(), password);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(formatApiErrorDetail(err.response?.data?.detail) || err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="min-h-screen relative flex items-center justify-center px-4 py-8"
      style={{
        background: "linear-gradient(135deg, #0B1220 0%, #111827 50%, #0B1220 100%)",
        backgroundImage: "url('/assets/login-bg.png')",
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
      data-testid="login-page"
    >
      {/* Overlay */}
      <div
        aria-hidden
        className="absolute inset-0 pointer-events-none"
        style={{ background: "rgba(11,18,32,0.75)" }}
      />

      {/* Déco — cercles lumineux */}
      <div aria-hidden className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full pointer-events-none"
        style={{ background: "radial-gradient(circle, rgba(249,115,22,0.08) 0%, transparent 70%)", filter: "blur(40px)" }} />
      <div aria-hidden className="absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full pointer-events-none"
        style={{ background: "radial-gradient(circle, rgba(59,130,246,0.06) 0%, transparent 70%)", filter: "blur(40px)" }} />

      {/* Carte */}
      <div
        data-testid="login-card"
        className="relative z-10 w-full max-w-md"
        style={{
          background: "rgba(30,41,59,0.9)",
          backdropFilter: "blur(20px)",
          border: "1px solid rgba(255,255,255,0.1)",
          borderRadius: "20px",
          padding: "40px 36px",
          boxShadow: "0 24px 80px rgba(0,0,0,0.5)",
        }}
      >
        {/* Header */}
        <div className="text-center mb-8">
          {/* Logo */}
          <div className="flex items-center justify-center gap-3 mb-5">
            <div
              className="w-12 h-12 rounded-2xl flex items-center justify-center"
              style={{ background: "linear-gradient(135deg,#F97316,#FB923C)", boxShadow: "0 8px 24px rgba(249,115,22,0.35)" }}
            >
              <span style={{ fontSize: "22px", fontWeight: 800, color: "#fff", fontFamily: "Inter, sans-serif" }}>F</span>
            </div>
            <div className="text-left">
              <p style={{ fontSize: "18px", fontWeight: 700, color: "#E2E8F0", lineHeight: 1.2 }}>FABS ERP</p>
              <p style={{ fontSize: "11px", color: "#94A3B8", letterSpacing: "0.06em" }}>v2.0 Enterprise</p>
            </div>
          </div>

          <h1 style={{ fontSize: "22px", fontWeight: 700, color: "#E2E8F0", letterSpacing: "-0.01em" }}>
            Connexion à votre espace
          </h1>
          <p style={{ fontSize: "13px", color: "#94A3B8", marginTop: "6px" }}>
            Renseignez vos identifiants pour continuer
          </p>
          <div style={{ width: "40px", height: "3px", background: "linear-gradient(90deg,#F97316,#FB923C)", borderRadius: "99px", margin: "14px auto 0" }} />
        </div>

        {/* Formulaire */}
        <form className="space-y-4" onSubmit={handleSubmit}>
          {error && (
            <div
              data-testid="login-error"
              style={{
                background: "rgba(239,68,68,0.1)",
                border: "1px solid rgba(239,68,68,0.25)",
                borderRadius: "10px",
                padding: "12px 14px",
                fontSize: "13px",
                color: "#FCA5A5",
              }}
            >
              {error}
            </div>
          )}

          {/* Email */}
          <div>
            <label style={{ fontSize: "13px", fontWeight: 500, color: "#94A3B8", display: "block", marginBottom: "6px" }}>
              Adresse e-mail
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2" style={{ color: "#94A3B8" }} />
              <input
                data-testid="login-email-input"
                type="email"
                placeholder="exemple@etablissement.ci"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
                style={{
                  width: "100%",
                  paddingLeft: "40px",
                  paddingRight: "14px",
                  paddingTop: "11px",
                  paddingBottom: "11px",
                  fontSize: "14px",
                  background: "rgba(255,255,255,0.05)",
                  border: "1px solid rgba(255,255,255,0.12)",
                  borderRadius: "10px",
                  color: "#E2E8F0",
                  outline: "none",
                  transition: "border-color 0.2s, box-shadow 0.2s",
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = "#F97316";
                  e.target.style.boxShadow = "0 0 0 3px rgba(249,115,22,0.12)";
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = "rgba(255,255,255,0.12)";
                  e.target.style.boxShadow = "none";
                }}
              />
            </div>
          </div>

          {/* Mot de passe */}
          <div>
            <label style={{ fontSize: "13px", fontWeight: 500, color: "#94A3B8", display: "block", marginBottom: "6px" }}>
              Mot de passe
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2" style={{ color: "#94A3B8" }} />
              <input
                data-testid="login-password-input"
                type={showPwd ? "text" : "password"}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
                style={{
                  width: "100%",
                  paddingLeft: "40px",
                  paddingRight: "44px",
                  paddingTop: "11px",
                  paddingBottom: "11px",
                  fontSize: "14px",
                  background: "rgba(255,255,255,0.05)",
                  border: "1px solid rgba(255,255,255,0.12)",
                  borderRadius: "10px",
                  color: "#E2E8F0",
                  outline: "none",
                  transition: "border-color 0.2s, box-shadow 0.2s",
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = "#F97316";
                  e.target.style.boxShadow = "0 0 0 3px rgba(249,115,22,0.12)";
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = "rgba(255,255,255,0.12)";
                  e.target.style.boxShadow = "none";
                }}
              />
              <button
                type="button"
                onClick={() => setShowPwd((v) => !v)}
                data-testid="toggle-password"
                className="absolute right-3 top-1/2 -translate-y-1/2 transition-colors"
                style={{ color: "#94A3B8" }}
                onMouseEnter={(e) => e.currentTarget.style.color = "#F97316"}
                onMouseLeave={(e) => e.currentTarget.style.color = "#94A3B8"}
              >
                {showPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Bouton */}
          <button
            data-testid="login-submit-btn"
            type="submit"
            disabled={submitting}
            style={{
              width: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "10px",
              background: submitting ? "rgba(249,115,22,0.6)" : "linear-gradient(90deg,#F97316,#FB923C)",
              color: "#fff",
              fontWeight: 700,
              fontSize: "15px",
              padding: "12px 0",
              borderRadius: "12px",
              border: "none",
              cursor: submitting ? "not-allowed" : "pointer",
              boxShadow: "0 6px 20px rgba(249,115,22,0.35)",
              transition: "all 0.2s",
              marginTop: "8px",
            }}
            onMouseEnter={(e) => { if (!submitting) e.currentTarget.style.filter = "brightness(1.1)"; }}
            onMouseLeave={(e) => e.currentTarget.style.filter = "none"}
          >
            {submitting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Connexion…
              </>
            ) : (
              <>
                Se connecter
                <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>

          <div style={{ paddingTop: "12px", borderTop: "1px solid rgba(255,255,255,0.08)", textAlign: "center" }}>
            <p style={{ fontSize: "11px", color: "rgba(148,163,184,0.6)", letterSpacing: "0.04em" }}>
              {COMPANY.nom} · ERP — {COMPANY.anneeScolaire}
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}
