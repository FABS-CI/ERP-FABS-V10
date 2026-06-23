/**
 * Page FNE — Détail d'une facture FNE (Sprint 2 V10)
 */
import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, RefreshCw, ShieldCheck, AlertTriangle, Copy } from "lucide-react";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";
import { getFNEStatus, getFNEQRCode, refundFNEInvoice } from "../services/fneApi";

const STATUT_COLORS = {
  pending:   "bg-[#F59E0B] text-white",
  submitted: "bg-[#0A2540] text-white",
  accepted:  "bg-[#10B981] text-white",
  certified: "bg-[#10B981] text-white",
  rejected:  "bg-[#EF4444] text-white",
  error:     "bg-[#EF4444] text-white",
  failed:    "bg-[#EF4444] text-white",
};

export default function FNEInvoiceDetail() {
  const { invoiceId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [meta, setMeta] = useState(null);
  const [qr, setQr] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [m, q] = await Promise.all([
        getFNEStatus(invoiceId).catch(() => null),
        getFNEQRCode(invoiceId).catch(() => null),
      ]);
      setMeta(m);
      setQr(q);
    } finally {
      setLoading(false);
    }
  }, [invoiceId]);

  useEffect(() => { refresh(); }, [refresh]);

  const handleRefund = async () => {
    if (!window.confirm("Confirmer la demande d'avoir/remboursement FNE ?")) return;
    try {
      await refundFNEInvoice(invoiceId);
      toast.success("Demande d'avoir envoyée à la DGI");
      refresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erreur lors de la demande d'avoir");
    }
  };

  const copyToClipboard = (txt) => {
    navigator.clipboard.writeText(txt);
    toast.success("Copié dans le presse-papier");
  };

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="fne-invoice-detail">
        <div className="flex items-center justify-between">
          <Button variant="ghost" onClick={() => navigate("/fne")} data-testid="btn-back">
            <ArrowLeft className="h-4 w-4 mr-2" /> Retour FNE
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={refresh} data-testid="btn-refresh-detail">
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} /> Rafraîchir
            </Button>
            {meta?.status === "accepted" && (
              <Button variant="destructive" onClick={handleRefund} data-testid="btn-refund">
                <AlertTriangle className="h-4 w-4 mr-2" /> Émettre un avoir
              </Button>
            )}
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="h-6 w-6 text-[#FF6200]" />
              Facture FNE — <span className="font-mono">{invoiceId}</span>
            </CardTitle>
            <CardDescription>
              Détail certification DGI · {meta?.status && <Badge className={`ml-2 ${STATUT_COLORS[meta.status] || "bg-gray-400"}`}>{meta.status}</Badge>}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}
              </div>
            ) : !meta ? (
              <p className="text-sm text-muted-foreground">Facture FNE introuvable.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <dl className="space-y-3">
                  <DataRow label="Invoice ID" value={meta.invoice_id} mono onCopy={() => copyToClipboard(meta.invoice_id)} />
                  <DataRow label="FNE ID (DGI)" value={meta.fne_id || "—"} mono onCopy={meta.fne_id ? () => copyToClipboard(meta.fne_id) : null} />
                  <DataRow label="Statut" value={meta.status} />
                  <DataRow label="Créée le" value={meta.created_at?.slice(0, 19).replace("T", " ")} />
                  <DataRow label="Soumise le" value={meta.submitted_at?.slice(0, 19).replace("T", " ") || "—"} />
                  <DataRow label="Validée le" value={meta.validated_at?.slice(0, 19).replace("T", " ") || "—"} />
                  <DataRow label="Mis à jour" value={meta.updated_at?.slice(0, 19).replace("T", " ") || "—"} />
                </dl>

                <div className="flex flex-col items-center justify-center bg-[#F9FAFB] dark:bg-white dark:bg-[#0b1e30]/5 rounded-lg p-6 border">
                  <p className="text-xs uppercase tracking-wide text-muted-foreground mb-3">QR Code DGI</p>
                  {qr?.qr_code ? (
                    <img
                      src={qr.qr_code.startsWith("data:") ? qr.qr_code : `data:image/png;base64,${qr.qr_code}`}
                      alt="QR Code FNE"
                      className="w-48 h-48 bg-white dark:bg-[#0b1e30] rounded-md p-2"
                      data-testid="fne-qr-code"
                    />
                  ) : (
                    <div className="w-48 h-48 bg-white dark:bg-[#0b1e30]/50 rounded-md border-2 border-dashed border-gray-300 dark:border-white/10 flex items-center justify-center text-center text-sm text-muted-foreground">
                      QR code disponible après certification
                    </div>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}

function DataRow({ label, value, mono, onCopy }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b py-2">
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className={`text-sm font-medium text-[#0A2540] dark:text-white ${mono ? "font-mono" : ""} flex items-center gap-2`}>
        {value}
        {onCopy && (
          <button onClick={onCopy} className="text-muted-foreground hover:text-[#FF6200]" data-testid={`copy-${label}`}>
            <Copy className="h-3.5 w-3.5" />
          </button>
        )}
      </dd>
    </div>
  );
}
