/**
 * Page Détail Paiement — Sprint 8
 */
import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Receipt } from "lucide-react";
import { toast } from "sonner";

import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Separator } from "../components/ui/separator";
import { Skeleton } from "../components/ui/skeleton";
import DocumentActionBar from "../components/document/DocumentActionBar";

import { getPaiement, sendPaiementWhatsApp, sendPaiementEmail, getPaiementPDF } from "../services/paiementsApi";

const MODES = {
  especes: { label: "Espèces", color: "bg-green-600" },
  cheque: { label: "Chèque", color: "bg-blue-600" },
  virement: { label: "Virement", color: "bg-purple-600" },
  mobile_money: { label: "Mobile Money", color: "bg-orange-500" },
};

const fmt = (n) => new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 }).format(n || 0) + " FCFA";

export default function PaiementDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [paiement, setPaiement] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPaiement(id)
      .then(setPaiement)
      .catch(() => { toast.error("Paiement introuvable"); navigate("/paiements"); })
      .finally(() => setLoading(false));
  }, [id, navigate]);

  const handleSendWhatsApp = async (payload) => {
    const data = await sendPaiementWhatsApp(id, payload);
    if (data.whatsapp_url) window.open(data.whatsapp_url, "_blank");
  };

  const handleSendEmail = async (payload) => {
    await sendPaiementEmail(id, payload);
  };

  // ✅ TICKET-002 : handlers PDF
  const handleGeneratePDF = useCallback(async () => {
    const blob = await getPaiementPDF(id);
    return blob; // DocumentActionBar attend un Blob
  }, [id]);

  const handleDownloadPDF = useCallback(async () => {
    const blob = await getPaiementPDF(id);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `recu-${paiement?.reference ?? id}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [id, paiement?.reference]);

  const handlePrintPDF = useCallback(async () => {
    const blob = await getPaiementPDF(id);
    const url = URL.createObjectURL(blob);
    const win = window.open(url, "_blank");
    if (win) win.addEventListener("load", () => win.print());
  }, [id]);

  if (loading) {
    return (
      <DashboardLayout>
        <Skeleton className="h-12 w-64 mb-4" /><Skeleton className="h-64 w-full" />
      </DashboardLayout>
    );
  }
  if (!paiement) return null;

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="paiement-detail">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => navigate("/paiements")} data-testid="btn-retour">
              <ArrowLeft className="h-4 w-4 mr-2" /> Retour
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-[#0A2540] dark:text-white">{paiement.reference}</h1>
              <div className="flex items-center gap-2 mt-2">
                <Badge className={`${MODES[paiement.mode_paiement]?.color} text-white`}>
                  {MODES[paiement.mode_paiement]?.label}
                </Badge>
                <span className="text-sm text-gray-500 dark:text-white/50">{paiement.date_paiement}</span>
              </div>
            </div>
          </div>
          {/* ✅ TICKET-002 : onGeneratePDF / onDownload / onPrint branchés */}
          <DocumentActionBar
            documentType="Reçu de Paiement"
            documentId={paiement.paiement_id}
            documentReference={paiement.reference}
            clientWhatsApp={paiement.client_numero_whatsapp}
            clientEmail={paiement.client_email}
            clientNom={paiement.client_nom}
            montant={paiement.montant_total ? `${Number(paiement.montant_total).toLocaleString('fr-FR')} FCFA` : ''}
            onSendWhatsApp={handleSendWhatsApp}
            onSendEmail={handleSendEmail}
            onGeneratePDF={handleGeneratePDF}
            onDownload={handleDownloadPDF}
            onPrint={handlePrintPDF}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader><CardTitle>Informations client</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-1">
                  <div><span className="text-gray-500 dark:text-white/50">Client :</span> <span className="font-medium">{paiement.client_nom}</span></div>
                  {paiement.banque && <div><span className="text-gray-500 dark:text-white/50">Banque :</span> {paiement.banque}</div>}
                  {paiement.numero_cheque && <div><span className="text-gray-500 dark:text-white/50">N° chèque :</span> {paiement.numero_cheque}</div>}
                  {paiement.reference_virement && <div><span className="text-gray-500 dark:text-white/50">Réf virement :</span> {paiement.reference_virement}</div>}
                  {paiement.operateur && <div><span className="text-gray-500 dark:text-white/50">Opérateur :</span> {paiement.operateur}</div>}
                  {paiement.numero_transaction && <div><span className="text-gray-500 dark:text-white/50">N° transaction :</span> {paiement.numero_transaction}</div>}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle className="flex items-center gap-2"><Receipt className="h-5 w-5" /> Factures affectées</CardTitle></CardHeader>
              <CardContent>
                {paiement.factures?.length === 0 ? (
                  <p className="text-gray-500 dark:text-white/50 text-sm">Aucune affectation — montant entièrement non affecté.</p>
                ) : (
                  <div className="space-y-2">
                    {paiement.factures.map((f) => (
                      <div key={f.facture_id} className="flex justify-between items-center border-b pb-2">
                        <span className="font-mono text-sm">{f.facture_reference}</span>
                        <span className="font-semibold text-green-600">{fmt(f.montant_affecte)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {paiement.notes && (
              <Card>
                <CardHeader><CardTitle>Notes</CardTitle></CardHeader>
                <CardContent><p className="whitespace-pre-wrap">{paiement.notes}</p></CardContent>
              </Card>
            )}
          </div>

          <div>
            <Card>
              <CardHeader><CardTitle>Résumé</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between"><span>Montant total</span><span className="font-bold text-[#FF6200]">{fmt(paiement.montant_total)}</span></div>
                <Separator />
                <div className="flex justify-between"><span>Affecté</span><span className="text-green-600 font-semibold">{fmt(paiement.montant_affecte)}</span></div>
                <div className="flex justify-between"><span>Non affecté</span><span className="text-orange-600 font-semibold">{fmt(paiement.montant_non_affecte)}</span></div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
