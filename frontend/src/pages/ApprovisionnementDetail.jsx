/**
 * Fiche Approvisionnement — Détail + Validation (Sprint 4 V10)
 */
import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft, Inbox, Building2, MapPin, FileText, CheckCircle2, Clock, RefreshCw, ShieldCheck,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";
import { useAuth } from "../hooks/useAuth";
import { can } from "../constants/permissions";
import { getApprovisionnement, validerApprovisionnement } from "../services/approvisionnementApi";

const STATUT_COLORS = {
  brouillon: "bg-gray-400 text-white",
  valide:    "bg-[#10B981] text-white",
  en_cours:  "bg-[#F59E0B] text-white",
  recu:      "bg-[#10B981] text-white",
  annule:    "bg-[#EF4444] text-white",
};

const STATUT_LABELS = {
  brouillon: "Brouillon",
  valide: "Validé",
  en_cours: "En cours",
  recu: "Reçu",
  annule: "Annulé",
};

const formatMoney = (v) =>
  new Intl.NumberFormat("fr-FR").format(Math.round(v || 0)) + " FCFA";

export default function ApprovisionnementDetail() {
  const { approvisionnementId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [appro, setAppro] = useState(null);
  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);

  const canWrite = user && can(user.role, "approvisionnements");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setAppro(await getApprovisionnement(approvisionnementId));
    } catch (e) {
      toast.error("Approvisionnement introuvable");
      navigate("/approvisionnements");
    } finally {
      setLoading(false);
    }
  }, [approvisionnementId, navigate]);

  useEffect(() => { load(); }, [load]);

  const handleValider = async () => {
    if (!window.confirm(
      "Confirmer la validation ?\n\nLe stock du dépôt sera automatiquement incrémenté selon les quantités reçues. Cette action est irréversible."
    )) return;
    setValidating(true);
    try {
      const updated = await validerApprovisionnement(approvisionnementId);
      setAppro(updated);
      toast.success("Approvisionnement validé · Stock mis à jour");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erreur lors de la validation");
    } finally {
      setValidating(false);
    }
  };

  if (loading) {
    return <DashboardLayout><Skeleton className="h-96 w-full" /></DashboardLayout>;
  }
  if (!appro) return null;

  const totalGeneral = appro.lignes.reduce(
    (s, l) => s + (l.quantite || 0) * (l.prix_achat || 0), 0,
  );
  const totalQte = appro.lignes.reduce((s, l) => s + (l.quantite || 0), 0);
  const isDraft = appro.statut === "brouillon";

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="appro-detail">
        <PageHeader
          title={appro.reference || "Approvisionnement"}
          subtitle={`Détail — ${STATUT_LABELS[appro.statut] || appro.statut || "Chargement…"}`}
          pagePath="/approvisionnements"
          actions={
            <div className="flex gap-2">
              <Button variant="outline" onClick={load} size="sm" data-testid="btn-refresh">
                <RefreshCw className="h-4 w-4 mr-2" /> Rafraîchir
              </Button>
              {canWrite && isDraft && (
                <Button
                  onClick={handleValider}
                  disabled={validating}
                  className="bg-green-600 hover:bg-green-700 text-white h-9"
                  data-testid="btn-valider"
                >
                  <ShieldCheck className="h-4 w-4 mr-2" />
                  {validating ? "Validation…" : "Valider et recevoir"}
                </Button>
              )}
            </div>
          }
        />

        {/* Cards Info */}

        {/* Cards Info */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card data-testid="card-fournisseur">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Building2 className="h-5 w-5 text-[#FF6200]" /> Fournisseur
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="font-semibold text-[#0A2540] dark:text-white">{appro.fournisseur_nom || "—"}</p>
              <button
                onClick={() => navigate(`/fournisseurs/${appro.fournisseur_id}`)}
                className="text-xs text-[#FF6200] hover:underline mt-1 font-mono"
                data-testid="link-fournisseur"
              >
                {appro.fournisseur_id}
              </button>
            </CardContent>
          </Card>

          <Card data-testid="card-depot">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <MapPin className="h-5 w-5 text-[#FF6200]" /> Dépôt
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="font-semibold capitalize text-[#0A2540] dark:text-white">{appro.depot}</p>
              <p className="text-xs text-muted-foreground mt-1">{totalQte} unité(s) au total</p>
            </CardContent>
          </Card>

          <Card data-testid="card-total">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <FileText className="h-5 w-5 text-[#FF6200]" /> Total
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-[#0A2540] dark:text-white">{formatMoney(totalGeneral)}</p>
              <p className="text-xs text-muted-foreground mt-1">{appro.lignes.length} ligne(s) produit</p>
            </CardContent>
          </Card>
        </div>

        {/* Notes */}
        {appro.notes && (
          <Card data-testid="card-notes">
            <CardHeader>
              <CardTitle className="text-base">Notes</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm whitespace-pre-wrap">{appro.notes}</p>
            </CardContent>
          </Card>
        )}

        {/* Lignes */}
        <Card>
          <CardHeader>
            <CardTitle>Lignes produits</CardTitle>
            <CardDescription>{appro.lignes.length} produit(s) commandé(s)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm" data-testid="lignes-table">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-2 w-12">#</th>
                    <th className="text-left py-3 px-2">Produit (ID)</th>
                    <th className="text-right py-3 px-2 w-24">Quantité</th>
                    <th className="text-right py-3 px-2 w-40">Prix d&apos;achat unitaire</th>
                    <th className="text-right py-3 px-2 w-40">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {appro.lignes.map((l, idx) => (
                    <tr key={idx} className="border-b" data-testid={`ligne-row-${idx}`}>
                      <td className="py-3 px-2 text-muted-foreground">{idx + 1}</td>
                      <td className="py-3 px-2 font-mono text-xs">{l.produit_id}</td>
                      <td className="py-3 px-2 text-right">{l.quantite}</td>
                      <td className="py-3 px-2 text-right tabular-nums">{formatMoney(l.prix_achat)}</td>
                      <td className="py-3 px-2 text-right font-semibold tabular-nums">
                        {formatMoney((l.quantite || 0) * (l.prix_achat || 0))}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-muted/30">
                  <tr>
                    <td colSpan={2} className="py-3 px-2 font-semibold">{appro.lignes.length} ligne(s)</td>
                    <td className="py-3 px-2 text-right font-semibold">{totalQte}</td>
                    <td className="py-3 px-2 text-right font-semibold">TOTAL HT :</td>
                    <td className="py-3 px-2 text-right text-lg font-bold text-[#0A2540] dark:text-white">
                      {formatMoney(totalGeneral)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Footer audit */}
        {appro.valide_par && (
          <div className="text-xs text-muted-foreground" data-testid="audit-info">
            <Clock className="h-3 w-3 inline mr-1" />
            Validé par utilisateur <code>{appro.valide_par}</code>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
