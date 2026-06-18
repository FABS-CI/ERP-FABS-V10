/**
 * TwoFASetupModal — Modal de configuration 2FA TOTP
 * Étapes : 1) Afficher QR → 2) Saisir code → 3) Succès
 * ERP FABS-CI V10
 */
import React, { useState, useEffect, useRef } from "react";
import { X, Shield, Copy, CheckCircle2, AlertCircle, Loader2, RefreshCw } from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { setup2FA, activate2FA, disable2FA } from "../services/twoFAApi";
import { toast } from "sonner";

// ─── Overlay ──────────────────────────────────────────────────────────────────
function Overlay({ children, onClose }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      {children}
    </div>
  );
}

// ─── Étape 1 : afficher QR + secret ──────────────────────────────────────────
function StepQR({ qrBase64, secret, onNext, onClose }) {
  const [copied, setCopied] = useState(false);

  const copySecret = () => {
    navigator.clipboard.writeText(secret).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="space-y-5">
      {/* Instructions */}
      <div className="bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800 rounded-xl p-4 text-sm text-blue-800 dark:text-blue-200 space-y-1">
        <p className="font-semibold">Comment configurer :</p>
        <ol className="list-decimal list-inside space-y-1 text-blue-700 dark:text-blue-300">
          <li>Ouvrez <strong>Google Authenticator</strong> ou <strong>Authy</strong></li>
          <li>Appuyez sur <strong>"+"</strong> puis <strong>"Scanner un QR code"</strong></li>
          <li>Scannez le code ci-dessous</li>
        </ol>
      </div>

      {/* QR Code */}
      <div className="flex justify-center">
        <div className="border-2 border-[#FF6200]/30 rounded-2xl p-3 bg-white dark:bg-[#0b1e30] shadow-lg">
          <img
            src={`data:image/png;base64,${qrBase64}`}
            alt="QR Code 2FA"
            className="w-48 h-48 block"
          />
        </div>
      </div>

      {/* Secret manuel */}
      <div className="space-y-1.5">
        <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
          Ou saisissez manuellement la clé secrète :
        </p>
        <div className="flex gap-2">
          <code className="flex-1 bg-gray-100 dark:bg-white dark:bg-[#0b1e30]/10 rounded-lg px-3 py-2 text-sm font-mono text-center tracking-widest select-all">
            {secret}
          </code>
          <Button
            size="sm"
            variant="outline"
            onClick={copySecret}
            className="shrink-0"
            title="Copier le secret"
          >
            {copied ? <CheckCircle2 className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3 pt-1">
        <Button variant="outline" className="flex-1" onClick={onClose}>Annuler</Button>
        <Button
          className="flex-1 bg-[#FF6200] hover:bg-[#E55900] text-white"
          onClick={onNext}
        >
          J'ai scanné → Continuer
        </Button>
      </div>
    </div>
  );
}

// ─── Étape 2 : saisir le code OTP ────────────────────────────────────────────
function StepVerify({ onActivate, onBack, loading, error }) {
  const [code, setCode] = useState("");
  const inputRef = useRef(null);

  useEffect(() => { inputRef.current?.focus(); }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (code.replace(/\s/g, "").length === 6) onActivate(code.replace(/\s/g, ""));
  };

  // Format auto : espace après 3 chiffres
  const handleChange = (e) => {
    const raw = e.target.value.replace(/\D/g, "").slice(0, 6);
    setCode(raw);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="text-center space-y-2">
        <div className="w-14 h-14 rounded-2xl bg-[#FF6200]/10 flex items-center justify-center mx-auto">
          <Shield className="h-7 w-7 text-[#FF6200]" />
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-300">
          Entrez le code à 6 chiffres affiché dans votre application
        </p>
      </div>

      <div className="space-y-2">
        <Input
          ref={inputRef}
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          maxLength={6}
          placeholder="000000"
          value={code}
          onChange={handleChange}
          className="text-center text-2xl tracking-[0.4em] font-mono h-14"
          disabled={loading}
          autoComplete="one-time-code"
        />
        {error && (
          <p className="flex items-center gap-1.5 text-sm text-red-500">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {error}
          </p>
        )}
        <p className="text-xs text-gray-400 text-center">Le code se renouvelle toutes les 30 secondes</p>
      </div>

      <div className="flex gap-3">
        <Button type="button" variant="outline" className="flex-1" onClick={onBack} disabled={loading}>
          Retour
        </Button>
        <Button
          type="submit"
          className="flex-1 bg-[#FF6200] hover:bg-[#E55900] text-white"
          disabled={loading || code.length !== 6}
        >
          {loading ? <><Loader2 className="h-4 w-4 animate-spin mr-2" /> Vérification…</> : "Activer le 2FA"}
        </Button>
      </div>
    </form>
  );
}

// ─── Étape 3 : succès ────────────────────────────────────────────────────────
function StepSuccess({ onClose }) {
  return (
    <div className="space-y-5 text-center">
      <div className="w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mx-auto">
        <CheckCircle2 className="h-9 w-9 text-green-500" />
      </div>
      <div className="space-y-1">
        <h3 className="font-semibold text-lg text-gray-900 dark:text-white">2FA activé !</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Votre compte est maintenant protégé par une double authentification.
          À chaque connexion, vous devrez saisir le code de votre application.
        </p>
      </div>
      <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-xl p-3 text-xs text-amber-700 dark:text-amber-300 text-left">
        <strong>Important :</strong> Conservez votre application d'authentification.
        Si vous perdez l'accès, contactez l'administrateur système.
      </div>
      <Button className="w-full bg-[#FF6200] hover:bg-[#E55900] text-white" onClick={onClose}>
        Fermer
      </Button>
    </div>
  );
}

// ─── Modal principal ──────────────────────────────────────────────────────────
export default function TwoFASetupModal({ onClose, onActivated }) {
  const [step, setStep] = useState("loading"); // loading | qr | verify | success | error
  const [qrData, setQrData] = useState(null);
  const [activating, setActivating] = useState(false);
  const [activateError, setActivateError] = useState("");
  const [initError, setInitError] = useState("");

  useEffect(() => { initSetup(); }, []);

  const initSetup = async () => {
    setStep("loading");
    setInitError("");
    try {
      const data = await setup2FA();
      setQrData(data);
      setStep("qr");
    } catch (err) {
      const msg = err?.response?.data?.detail || "Erreur lors de l'initialisation du 2FA";
      setInitError(msg);
      setStep("error");
    }
  };

  const handleActivate = async (code) => {
    setActivating(true);
    setActivateError("");
    try {
      await activate2FA(code);
      setStep("success");
      onActivated?.();
      toast.success("2FA activé avec succès");
    } catch (err) {
      const msg = err?.response?.data?.detail || "Code invalide";
      setActivateError(msg);
    } finally {
      setActivating(false);
    }
  };

  const titles = {
    loading: "Configuration du 2FA",
    qr: "Étape 1 — Scanner le QR code",
    verify: "Étape 2 — Vérifier le code",
    success: "2FA activé",
    error: "Erreur d'initialisation",
  };

  return (
    <Overlay onClose={step !== "loading" ? onClose : undefined}>
      <div className="bg-white dark:bg-[#0A1929] rounded-2xl shadow-2xl w-full max-w-md border border-gray-200 dark:border-white/10 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-white/10">
          <div className="flex items-center gap-2.5">
            <Shield className="h-5 w-5 text-[#FF6200]" />
            <h2 className="font-semibold text-gray-900 dark:text-white text-base">
              {titles[step] || "2FA"}
            </h2>
          </div>
          {step !== "loading" && (
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-white dark:bg-[#0b1e30]/10 transition-colors"
              aria-label="Fermer"
            >
              <X className="h-4 w-4 text-gray-500 dark:text-white/50" />
            </button>
          )}
        </div>

        {/* Body */}
        <div className="p-6">
          {step === "loading" && (
            <div className="flex flex-col items-center gap-3 py-8">
              <Loader2 className="h-8 w-8 animate-spin text-[#FF6200]" />
              <p className="text-sm text-gray-500 dark:text-white/50">Génération du QR code…</p>
            </div>
          )}

          {step === "error" && (
            <div className="space-y-4">
              <div className="flex items-start gap-3 p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-xl">
                <AlertCircle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
                <p className="text-sm text-red-700 dark:text-red-300">{initError}</p>
              </div>
              <div className="flex gap-3">
                <Button variant="outline" className="flex-1" onClick={onClose}>Annuler</Button>
                <Button
                  className="flex-1 bg-[#FF6200] hover:bg-[#E55900] text-white"
                  onClick={initSetup}
                >
                  <RefreshCw className="h-4 w-4 mr-2" /> Réessayer
                </Button>
              </div>
            </div>
          )}

          {step === "qr" && qrData && (
            <StepQR
              qrBase64={qrData.qr_code_base64}
              secret={qrData.secret}
              onNext={() => setStep("verify")}
              onClose={onClose}
            />
          )}

          {step === "verify" && (
            <StepVerify
              onActivate={handleActivate}
              onBack={() => setStep("qr")}
              loading={activating}
              error={activateError}
            />
          )}

          {step === "success" && <StepSuccess onClose={onClose} />}
        </div>
      </div>
    </Overlay>
  );
}
