/**
 * TwoFADisableModal — Confirmation désactivation 2FA
 * Nécessite un code OTP valide (interdit pour super_admin côté backend)
 * ERP FABS-CI V10
 */
import React, { useState, useRef, useEffect } from "react";
import { X, ShieldOff, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { disable2FA } from "../services/twoFAApi";
import { toast } from "sonner";

export default function TwoFADisableModal({ onClose, onDisabled }) {
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef(null);

  useEffect(() => { inputRef.current?.focus(); }, []);

  const handleChange = (e) => {
    const raw = e.target.value.replace(/\D/g, "").slice(0, 6);
    setCode(raw);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (code.length !== 6) return;
    setLoading(true);
    setError("");
    try {
      await disable2FA(code);
      toast.success("2FA désactivé");
      onDisabled?.();
      onClose();
    } catch (err) {
      setError(err?.response?.data?.detail || "Code invalide ou opération refusée");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-white dark:bg-[#0A1929] rounded-2xl shadow-2xl w-full max-w-sm border border-gray-200 dark:border-white/10 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-white/10">
          <div className="flex items-center gap-2.5">
            <ShieldOff className="h-5 w-5 text-red-500" />
            <h2 className="font-semibold text-gray-900 dark:text-white text-base">Désactiver le 2FA</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-white dark:bg-[#0b1e30]/10 transition-colors"
          >
            <X className="h-4 w-4 text-gray-500 dark:text-white/50" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-xl p-4 text-sm text-red-700 dark:text-red-300">
            <strong>Attention :</strong> La désactivation du 2FA réduit la sécurité de votre compte.
            Confirmez avec un code OTP valide.
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Code OTP de confirmation
            </label>
            <Input
              ref={inputRef}
              type="text"
              inputMode="numeric"
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
          </div>

          <div className="flex gap-3">
            <Button type="button" variant="outline" className="flex-1" onClick={onClose} disabled={loading}>
              Annuler
            </Button>
            <Button
              type="submit"
              variant="destructive"
              className="flex-1"
              disabled={loading || code.length !== 6}
            >
              {loading ? <><Loader2 className="h-4 w-4 animate-spin mr-2" /> Désactivation…</> : "Désactiver"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
