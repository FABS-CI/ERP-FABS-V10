import { useState, useRef, useEffect } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { Mail, Lock, Loader2, ArrowRight, Eye, EyeOff, Shield, AlertCircle, ShieldAlert } from "lucide-react";
import { useAuth, csrfStore } from "../hooks/useAuth";
import { COMPANY } from "../constants/company";
import { verify2FA } from "../services/twoFAApi";

function formatApiErrorDetail(detail) {
  if (detail == null) return "Une erreur est survenue. Veuillez réessayer.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail.map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e))).filter(Boolean).join(" ");
  if (detail && typeof detail.msg === "string") return detail.msg;
  return String(detail);
}

// ─── Étape OTP inline ────────────────────────────────────────────────────────
function StepOTP({ onVerify, loading, error, onBack }) {
  const [code, setCode] = useState("");
  const inputRef = useRef(null);
  useEffect(() => { inputRef.current?.focus(); }, []);

  const handleChange = (e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6));

  return (
    <div className="space-y-5">
      <div className="text-center space-y-2">
        <div
          style={{
            width: 56, height: 56, borderRadius: 16,
            background: "rgba(249,115,22,0.15)",
            display: "flex", alignItems: "center", justifyContent: "center",
            margin: "0 auto",
          }}
        >
          <Shield style={{ width: 28, height: 28, color: "#F97316" }} />
        </div>
        <h2 style={{ fontSize: 18, fontWeight: 700, color: "#E2E8F0" }}>Vérification 2FA</h2>
        <p style={{ fontSize: 13, color: "#94A3B8" }}>
          Entrez le code à 6 chiffres de votre application d'authentification
        </p>
      </div>

      {error && (
        <div style={{
          background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.25)",
          borderRadius: 10, padding: "12px 14px", fontSize: 13, color: "#FCA5A5",
          display: "flex", alignItems: "center", gap: 8
        }}>
          <AlertCircle style={{ width: 16, height: 16, flexShrink: 0 }} />
          {error}
        </div>
      )}

      <div>
        <input
          ref={inputRef}
          type="text"
          inputMode="numeric"
          maxLength={6}
          placeholder="000000"
          value={code}
          onChange={handleChange}
          autoComplete="one-time-code"
          style={{
            width: "100%",
            textAlign: "center",
            fontSize: 28,
            letterSpacing: "0.3em",
            fontFamily: "monospace",
            fontWeight: 700,
            paddingTop: 14,
            paddingBottom: 14,
            background: "rgba(255,255,255,0.05)",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: 12,
            color: "#E2E8F0",
            outline: "none",
          }}
          onFocus={(e) => {
            e.target.style.borderColor = "#F97316";
            e.target.style.boxShadow = "0 0 0 3px rgba(249,115,22,0.12)";
          }}
          onBlur={(e) => {
            e.target.style.borderColor = "rgba(255,255,255,0.12)";
            e.target.style.boxShadow = "none";
          }}
          onKeyDown={(e) => { if (e.key === "Enter" && code.length === 6) onVerify(code); }}
        />
        <p style={{ fontSize: 11, color: "#64748B", textAlign: "center", marginTop: 6 }}>
          Le code se renouvelle toutes les 30 secondes
        </p>
      </div>

      <button
        type="button"
        disabled={loading || code.length !== 6}
        onClick={() => onVerify(code)}
        style={{
          width: "100%",
          display: "flex", alignItems: "center", justifyContent: "center", gap: 10,
          background: (loading || code.length !== 6)
            ? "rgba(249,115,22,0.4)"
            : "linear-gradient(90deg,#F97316,#FB923C)",
          color: "#fff", fontWeight: 700, fontSize: 15,
          padding: "12px 0", borderRadius: 12, border: "none",
          cursor: (loading || code.length !== 6) ? "not-allowed" : "pointer",
          boxShadow: "0 6px 20px rgba(249,115,22,0.3)",
          transition: "all 0.2s",
        }}
      >
        {loading ? <><Loader2 style={{ width: 20, height: 20 }} className="animate-spin" /> Vérification…</> : <>Confirmer <ArrowRight style={{ width: 20, height: 20 }} /></>}
      </button>

      <button
        type="button"
        onClick={onBack}
        style={{
          width: "100%", background: "none", border: "none",
          color: "#64748B", fontSize: 13, cursor: "pointer",
          textDecoration: "underline", padding: "4px 0",
        }}
      >
        ← Retour à la connexion
      </button>
    </div>
  );
}

// ─── Étape Setup requis ───────────────────────────────────────────────────────
function StepSetupRequired({ onGoSetup, onBack }) {
  return (
    <div className="space-y-5 text-center">
      <div style={{
        width: 56, height: 56, borderRadius: 16,
        background: "rgba(245,158,11,0.15)",
        display: "flex", alignItems: "center", justifyContent: "center",
        margin: "0 auto",
      }}>
        <ShieldAlert style={{ width: 28, height: 28, color: "#F59E0B" }} />
      </div>
      <div>
        <h2 style={{ fontSize: 18, fontWeight: 700, color: "#E2E8F0" }}>Configuration 2FA requise</h2>
        <p style={{ fontSize: 13, color: "#94A3B8", marginTop: 6 }}>
          Votre rôle impose la double authentification. Configurez-la maintenant pour accéder à l'application.
        </p>
      </div>
      <div style={{
        background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.2)",
        borderRadius: 10, padding: "12px 14px", fontSize: 13, color: "#FCD34D", textAlign: "left"
      }}>
        Vous serez redirigé vers les <strong>Paramètres</strong> pour scanner un QR code avec Google Authenticator ou Authy.
      </div>
      <button
        type="button"
        onClick={onGoSetup}
        style={{
          width: "100%",
          display: "flex", alignItems: "center", justifyContent: "center", gap: 10,
          background: "linear-gradient(90deg,#F97316,#FB923C)",
          color: "#fff", fontWeight: 700, fontSize: 15,
          padding: "12px 0", borderRadius: 12, border: "none", cursor: "pointer",
          boxShadow: "0 6px 20px rgba(249,115,22,0.3)",
        }}
      >
        <Shield style={{ width: 20, height: 20 }} />
        Configurer le 2FA
      </button>
      <button
        type="button"
        onClick={onBack}
        style={{
          width: "100%", background: "none", border: "none",
          color: "#64748B", fontSize: 13, cursor: "pointer",
          textDecoration: "underline", padding: "4px 0",
        }}
      >
        ← Retour à la connexion
      </button>
    </div>
  );
}

// ─── Composant principal ──────────────────────────────────────────────────────
export default function Login() {
  const { user, isLoading, login, setUser } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPwd, setShowPwd] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Gestion des étapes 2FA
  const [step, setStep] = useState("login"); // login | otp | setup_required
  const [otpLoading, setOtpLoading] = useState(false);
  const [otpError, setOtpError] = useState("");
  const [pendingUserData, setPendingUserData] = useState(null); // données user pré-auth

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
      const data = await login(email.trim().toLowerCase(), password);
      if (data?.twofa_pending) {
        // Token pré-auth stocké, on demande le code OTP
        setPendingUserData(data.user);
        setStep("otp");
      } else if (data?.twofa_setup_required) {
        // 2FA obligatoire mais pas configuré → on laisse l'utilisateur aller le configurer
        setPendingUserData(data.user);
        // Finaliser la session temporairement (token complet retourné dans ce cas)
        setUser(data.user);
        setStep("setup_required");
      } else {
        // Prefetch des chunks critiques en background avant navigation
        Promise.allSettled([
          import("./Dashboard"),
          import("./Clients"),
          import("./Commandes"),
          import("./Factures"),
        ]);
        navigate("/dashboard", { replace: true });
      }
    } catch (err) {
      setError(formatApiErrorDetail(err.response?.data?.detail) || err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleOTPVerify = async (code) => {
    setOtpLoading(true);
    setOtpError("");
    try {
      const result = await verify2FA(code);
      // ✅ CSRF token is auto-extracted by useAuth hook
      // Browser automatically stores session_token in HttpOnly cookie
      // Finaliser la session
      setUser(pendingUserData);
      Promise.allSettled([import("./Dashboard"), import("./Clients"), import("./Commandes"), import("./Factures")]);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setOtpError(err?.response?.data?.detail || "Code invalide. Vérifiez votre application.");
    } finally {
      setOtpLoading(false);
    }
  };

  const handleGoSetup = () => {
    navigate("/parametres", { replace: true });
  };

  const handleBack = () => {
    // ✅ Clear CSRF token when returning to login
    csrfStore.clear();
    setPendingUserData(null);
    setOtpError("");
    setError("");
    setStep("login");
  };

  return (
    <div
      className="login-page-root min-h-screen relative flex"
      style={{
        backgroundImage: "url('/assets/login-bg.png')",
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
        backgroundColor: "#0d1b2a",
      }}
      data-testid="login-page"
    >
      {/* Styles responsive (mobile / tablette / desktop) */}
      <style>{`
        .login-page-shell {
          flex: 1 1 100%;
          justify-content: center;
          padding-left: 22%;
        }
        .login-card-box {
          padding: 48px 40px;
        }
        /* Tablette */
        @media (max-width: 1024px) {
          .login-page-shell { padding-left: 8%; justify-content: center; }
        }
        /* Mobile : on GARDE le branding + l'image des livres visibles en haut,
           la carte vient en dessous. Fond visible (pas assombri uniformément). */
        @media (max-width: 768px) {
          .login-page-root {
            background-position: center top;
            background-size: cover;
            display: block !important;
          }
          .login-mobile-branding {
            display: flex !important;
          }
          .login-page-shell {
            padding-left: 0 !important;
            padding-right: 0 !important;
            flex-direction: column !important;
            justify-content: flex-start !important;
            align-items: center !important;
          }
          .login-card-box {
            padding: 30px 22px;
            max-width: 100%;
          }
          /* Overlay léger juste pour la lisibilité globale, image toujours visible */
          .login-overlay-mobile {
            background: linear-gradient(180deg, rgba(13,27,42,0.30) 0%, rgba(13,27,42,0.55) 100%) !important;
          }
        }
        /* Le branding mobile est masqué sur desktop (l'image de fond suffit) */
        .login-mobile-branding { display: none; }
        @media (max-width: 380px) {
          .login-card-box { padding: 26px 16px; }
        }
      `}</style>

      {/* Overlay sombre pour lisibilité de la carte */}
      <div
        aria-hidden
        className="login-overlay-mobile absolute inset-0 pointer-events-none"
        style={{
          background: "linear-gradient(90deg, rgba(13,27,42,0.0) 0%, rgba(13,27,42,0.25) 40%, rgba(13,27,42,0.55) 60%, rgba(13,27,42,0.0) 100%)",
        }}
      />

      {/* ── Carte login décalée vers la droite (à côté du livre) ── */}
      <div
        className="login-page-shell relative z-10 flex items-center px-4 sm:px-6 py-8 sm:py-10 w-full"
      >
        {/* Glow effect */}
        <div aria-hidden style={{
          position: "absolute", top: "30%", right: "-10%",
          width: 300, height: 300, borderRadius: "50%",
          background: "radial-gradient(circle, rgba(249,115,22,0.06) 0%, transparent 70%)",
          filter: "blur(50px)", pointerEvents: "none",
        }} />

      {/* ── Branding mobile (logo + nom + slogan), visible uniquement < 768px ── */}
      <div
        className="login-mobile-branding relative z-10 w-full max-w-sm flex-col items-center text-center"
        style={{ marginBottom: 22, gap: 8 }}
      >
        <div
          style={{
            width: 64, height: 64, borderRadius: 18,
            background: "linear-gradient(135deg,#F97316,#FB923C)",
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 10px 30px rgba(249,115,22,0.45)",
          }}
        >
          <span style={{ fontSize: 32, fontWeight: 800, color: "#fff", fontFamily: "Inter, sans-serif" }}>F</span>
        </div>
        <h2 style={{ fontSize: 22, fontWeight: 800, color: "#fff", letterSpacing: "0.04em", textShadow: "0 2px 12px rgba(0,0,0,0.7)", marginTop: 4 }}>
          ÉDITIONS FABS-CI
        </h2>
        <p style={{ fontSize: 13, color: "#E2E8F0", textShadow: "0 1px 8px rgba(0,0,0,0.7)" }}>
          Plateforme de gestion complète de l'entreprise
        </p>
        <p style={{ fontSize: 12, fontStyle: "italic", color: "#FBBF24", textShadow: "0 1px 8px rgba(0,0,0,0.7)" }}>
          {COMPANY.slogan}
        </p>
      </div>

      {/* Carte login */}
      <div
        data-testid="login-card"
        className="login-card-box relative z-10 w-full max-w-sm"
        style={{
          background: "rgba(20,32,50,0.85)",
          backdropFilter: "blur(10px)",
          border: "1px solid rgba(249,115,22,0.15)",
          borderRadius: "16px",
          boxShadow: "0 25px 50px rgba(0,0,0,0.6)",
        }}
      >
        {/* Header — toujours visible */}
        <div className="text-center mb-8">
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

          {step === "login" && (
            <>
              <h1 style={{ fontSize: "22px", fontWeight: 700, color: "#E2E8F0", letterSpacing: "-0.01em" }}>
                Connexion à votre espace
              </h1>
              <p style={{ fontSize: "13px", color: "#94A3B8", marginTop: "6px" }}>
                Renseignez vos identifiants pour continuer
              </p>
            </>
          )}
          <div style={{ width: "40px", height: "3px", background: "linear-gradient(90deg,#F97316,#FB923C)", borderRadius: "99px", margin: "14px auto 0" }} />
        </div>

        {/* ── Étape login ── */}
        {step === "login" && (
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
                  display: "flex", alignItems: "center", gap: 8,
                }}
              >
                <AlertCircle style={{ width: 16, height: 16, flexShrink: 0 }} />
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
                    width: "100%", paddingLeft: "40px", paddingRight: "14px",
                    paddingTop: "11px", paddingBottom: "11px", fontSize: "14px",
                    background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.12)",
                    borderRadius: "10px", color: "#E2E8F0", outline: "none", transition: "border-color 0.2s, box-shadow 0.2s",
                  }}
                  onFocus={(e) => { e.target.style.borderColor = "#F97316"; e.target.style.boxShadow = "0 0 0 3px rgba(249,115,22,0.12)"; }}
                  onBlur={(e) => { e.target.style.borderColor = "rgba(255,255,255,0.12)"; e.target.style.boxShadow = "none"; }}
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
                    width: "100%", paddingLeft: "40px", paddingRight: "44px",
                    paddingTop: "11px", paddingBottom: "11px", fontSize: "14px",
                    background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.12)",
                    borderRadius: "10px", color: "#E2E8F0", outline: "none", transition: "border-color 0.2s, box-shadow 0.2s",
                  }}
                  onFocus={(e) => { e.target.style.borderColor = "#F97316"; e.target.style.boxShadow = "0 0 0 3px rgba(249,115,22,0.12)"; }}
                  onBlur={(e) => { e.target.style.borderColor = "rgba(255,255,255,0.12)"; e.target.style.boxShadow = "none"; }}
                />
                <button
                  type="button"
                  onClick={() => setShowPwd((v) => !v)}
                  data-testid="toggle-password"
                  className="absolute right-3 top-1/2 -translate-y-1/2 transition-colors"
                  style={{ color: "#94A3B8", background: "none", border: "none", cursor: "pointer", padding: 0 }}
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
                width: "100%", display: "flex", alignItems: "center", justifyContent: "center", gap: "10px",
                background: submitting ? "rgba(249,115,22,0.6)" : "linear-gradient(90deg,#F97316,#FB923C)",
                color: "#fff", fontWeight: 700, fontSize: "15px", padding: "12px 0",
                borderRadius: "12px", border: "none",
                cursor: submitting ? "not-allowed" : "pointer",
                boxShadow: "0 6px 20px rgba(249,115,22,0.35)", transition: "all 0.2s", marginTop: "8px",
              }}
              onMouseEnter={(e) => { if (!submitting) e.currentTarget.style.filter = "brightness(1.1)"; }}
              onMouseLeave={(e) => e.currentTarget.style.filter = "none"}
            >
              {submitting ? (<><Loader2 className="w-5 h-5 animate-spin" /> Connexion…</>) : (<>Se connecter<ArrowRight className="w-5 h-5" /></>)}
            </button>

            <div style={{ paddingTop: "12px", borderTop: "1px solid rgba(255,255,255,0.08)", textAlign: "center" }}>
              <p style={{ fontSize: "11px", color: "rgba(148,163,184,0.6)", letterSpacing: "0.04em" }}>
                {COMPANY.nom} · ERP — {COMPANY.anneeScolaire}
              </p>
            </div>
          </form>
        )}

        {/* ── Étape OTP ── */}
        {step === "otp" && (
          <StepOTP
            onVerify={handleOTPVerify}
            loading={otpLoading}
            error={otpError}
            onBack={handleBack}
          />
        )}

        {/* ── Étape setup requis ── */}
        {step === "setup_required" && (
          <StepSetupRequired
            onGoSetup={handleGoSetup}
            onBack={handleBack}
          />
        )}
      </div>
      {/* fin carte */}
      </div>
      {/* fin colonne droite */}
    </div>
  );
}
