/**
 * Page Fiche Fournisseur — Détail + Historique livraisons (Sprint 3 V10)
 */
import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft, Building2, Phone, Mail, MapPin, User, Edit, Trash2, Truck, RefreshCw,
} from "lucide-react";
import { toast } from "sonner";
import axios from "axios";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";
import API_BASE_URL from "../config/api";
import { useAuth } from "../hooks/useAuth";
import { can } from "../constants/permissions";
import { getFournisseur, deleteFournisseur } from "../services/fournisseursApi";

export default function FournisseurDetail() {
  const { fournisseurId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [fournisseur, setFournisseur] = useState(null);
  const [livraisons, setLivraisons] = useState([]);
  const [tab, setTab] = useState("infos");

  const canWrite = user && can(user.role, "fournisseurs");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [f, livRes] = await Promise.all([
        getFournisseur(fournisseurId),
        axios.get(`${API_BASE_URL}/fournisseurs/${fournisseurId}/livraisons`).catch(() => ({ data: { items: [] } })),
      ]);
      setFournisseur(f);
      const data = livRes.data;
      setLivraisons(Array.isArray(data) ? data : data?.items || []);
    } catch (e) {
      toast.error("Fournisseur introuvable");
      navigate("/fournisseurs");
    } finally {
      setLoading(false);
    }
  }, [fournisseurId, navigate]);

  useEffect(() => { load(); }, [load]);

  const handleDelete = async () => {
    if (!window.confirm(`Supprimer définitivement le fournisseur "${fournisseur?.nom}" ?`)) return;
    try {
      await deleteFournisseur(fournisseurId);
      toast.success("Fournisseur supprimé");
      navigate("/fournisseurs");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erreur lors de la suppression");
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <Skeleton className="h-96 w-full" />
      </DashboardLayout>
    );
  }

  if (!fournisseur) return null;

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="fournisseur-detail">
        {/* Header */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <Button variant="ghost" onClick={() => navigate("/fournisseurs")} data-testid="btn-back">
            <ArrowLeft className="h-4 w-4 mr-2" /> Retour Fournisseurs
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={load} data-testid="btn-refresh">
              <RefreshCw className="h-4 w-4 mr-2" /> Rafraîchir
            </Button>
            {canWrite && (
              <>
                <Button
                  variant="outline"
                  onClick={() => navigate(`/fournisseurs?edit=${fournisseurId}`)}
                  data-testid="btn-edit"
                >
                  <Edit className="h-4 w-4 mr-2" /> Modifier
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleDelete}
                  className="bg-[#EF4444] hover:bg-[#EF4444]/90"
                  data-testid="btn-delete"
                >
                  <Trash2 className="h-4 w-4 mr-2" /> Supprimer
                </Button>
              </>
            )}
          </div>
        </div>

        {/* Titre */}
        <div className="flex items-start gap-4">
          <div className="w-14 h-14 rounded-xl bg-blue-600 flex items-center justify-center shrink-0">
            <Building2 className="h-7 w-7 text-white" />
          </div>
          <div className="flex-1">
            <h1 className="text-2xl md:text-3xl font-bold text-[#0A2540] dark:text-white">{fournisseur.nom}</h1>
            <div className="flex items-center gap-3 mt-1 text-sm text-muted-foreground">
              <span className="font-mono">{fournisseur.reference}</span>
              <Badge className={fournisseur.actif ? "bg-[#10B981] text-white" : "bg-gray-400 text-white"}>
                {fournisseur.actif ? "Actif" : "Inactif"}
              </Badge>
              <span>Créé le {fournisseur.created_at?.slice(0, 10)}</span>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={tab} onValueChange={setTab}>
          <TabsList>
            <TabsTrigger value="infos" data-testid="tab-infos">Informations</TabsTrigger>
            <TabsTrigger value="livraisons" data-testid="tab-livraisons">
              Livraisons ({livraisons.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="infos" className="space-y-4 mt-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card data-testid="card-contact">
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <User className="h-5 w-5 text-[#FF6200]" /> Contact
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <InfoRow icon={User} label="Personne" value={fournisseur.contact || "—"} />
                  <InfoRow icon={Phone} label="Téléphone" value={
                    fournisseur.telephone ? (
                      <a href={`tel:${fournisseur.telephone}`} className="text-[#FF6200] hover:underline">
                        {fournisseur.telephone}
                      </a>
                    ) : "—"
                  } />
                  <InfoRow icon={Mail} label="Email" value={
                    fournisseur.email ? (
                      <a href={`mailto:${fournisseur.email}`} className="text-[#FF6200] hover:underline break-all">
                        {fournisseur.email}
                      </a>
                    ) : "—"
                  } />
                </CardContent>
              </Card>

              <Card data-testid="card-adresse">
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <MapPin className="h-5 w-5 text-[#FF6200]" /> Adresse
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm whitespace-pre-wrap text-[#0A2540] dark:text-white">
                    {fournisseur.adresse || <span className="text-muted-foreground">Non renseignée</span>}
                  </p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="livraisons" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Truck className="h-5 w-5 text-[#FF6200]" /> Historique des livraisons
                </CardTitle>
                <CardDescription>
                  Toutes les livraisons reçues de ce fournisseur
                </CardDescription>
              </CardHeader>
              <CardContent>
                {livraisons.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground" data-testid="livraisons-empty">
                    <Truck className="h-12 w-12 mx-auto mb-3 opacity-30" />
                    <p>Aucune livraison enregistrée pour ce fournisseur.</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm" data-testid="livraisons-table">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-3 px-2">Référence</th>
                          <th className="text-left py-3 px-2">Date</th>
                          <th className="text-left py-3 px-2">Statut</th>
                          <th className="text-right py-3 px-2">Montant</th>
                        </tr>
                      </thead>
                      <tbody>
                        {livraisons.map((l, idx) => (
                          <tr key={l.livraison_id || idx} className="border-b hover:bg-muted/50">
                            <td className="py-3 px-2 font-mono text-xs">{l.reference || l.livraison_id || "—"}</td>
                            <td className="py-3 px-2">{l.date_livraison?.slice(0, 10) || "—"}</td>
                            <td className="py-3 px-2">
                              <Badge className="bg-[#0A2540] text-white">{l.statut || "—"}</Badge>
                            </td>
                            <td className="py-3 px-2 text-right font-semibold tabular-nums">
                              {l.montant ? new Intl.NumberFormat("fr-FR").format(l.montant) + " FCFA" : "—"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}

function InfoRow({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center justify-between gap-3 py-2 border-b last:border-0">
      <span className="text-muted-foreground flex items-center gap-2">
        <Icon className="h-4 w-4" />
        {label}
      </span>
      <span className="text-right text-[#0A2540] dark:text-white max-w-[60%]">{value}</span>
    </div>
  );
}
