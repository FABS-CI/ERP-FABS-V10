/**
 * Page Gestion des Colis
 * Workflow: Commande → Facture → Colisage → Livraison → Paiement
 * Les colis sont liés exclusivement à des factures émises.
 */
import { useState } from "react";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { useQuery, useMutation, useQueryClient } from "react-query";
import {
  Plus, Search, Package, Eye, Edit, Trash2, CheckCircle,
  XCircle, ChevronDown, ChevronRight, FileText, AlertCircle
} from "lucide-react";
import {
  listColis, deleteColis, updateColisStatut,
  createColis, updateColis, getColisByFacture
} from "@/services/colisageService";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog, DialogContent, DialogDescription,
  DialogHeader, DialogTitle, DialogFooter
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";
import axios from "axios";
import { getApiBase } from "../config/api";

// ─── STATUT CONFIG ────────────────────────────────────────────────────────────

const STATUT_CONFIG = {
  en_preparation: { label: "En préparation", variant: "secondary", color: "bg-gray-500" },
  valide:         { label: "Validé",          variant: "default",   color: "bg-green-600" },
  expedie:        { label: "Expédié",         variant: "default",   color: "bg-blue-600" },
  annule:         { label: "Annulé",          variant: "destructive", color: "bg-red-600" },
};

function StatutBadge({ statut }) {
  const cfg = STATUT_CONFIG[statut] || { label: statut, color: "bg-gray-400" };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold text-white ${cfg.color}`}>
      {cfg.label}
    </span>
  );
}

// ─── FORMULAIRE COLIS ─────────────────────────────────────────────────────────

function ColisForm({ factureId, colisExistant, onSuccess, onCancel }) {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [factureData, setFactureData] = useState(null);
  const [factureInput, setFactureInput] = useState(factureId || "");
  const [searchingFacture, setSearchingFacture] = useState(false);
  const [lignes, setLignes] = useState([]);
  const [nombreCartons, setNombreCartons] = useState(colisExistant?.nombre_cartons || 1);
  const [notes, setNotes] = useState(colisExistant?.notes || "");

  // Charger la facture et ses lignes disponibles
  const chargerFacture = async (fid) => {
    if (!fid) return;
    setSearchingFacture(true);
    try {
      const data = await getColisByFacture(fid);
      setFactureData(data);
      // En mode édition, pré-remplir avec les lignes du colis existant
      if (colisExistant) {
        setLignes(
          colisExistant.lignes.map((l) => ({
            ...l,
            qte_input: l.quantite_colisee,
          }))
        );
        setNombreCartons(colisExistant.nombre_cartons || 1);
        setNotes(colisExistant.notes || "");
      } else {
        // Pré-remplir avec les lignes restantes > 0
        const lignesInit = data.lignes
          .filter((l) => l.quantite_restante > 0)
          .map((l) => ({
            ligne_facture_id: l.ligne_id,
            produit_id: l.produit_id,
            designation: l.designation,
            quantite_facturee: l.quantite,
            quantite_colisee: l.quantite_restante,
            quantite_restante: l.quantite_restante,
            qte_input: l.quantite_restante,
          }));
        setLignes(lignesInit);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || "Facture introuvable ou non autorisée");
      setFactureData(null);
      setLignes([]);
    } finally {
      setSearchingFacture(false);
    }
  };

  const handleQteChange = (idx, val) => {
    setLignes((prev) => {
      const updated = [...prev];
      updated[idx] = { ...updated[idx], qte_input: parseInt(val) || 0 };
      return updated;
    });
  };

  const handleSubmit = async () => {
    const fid = factureId || factureInput;
    if (!fid) { toast.error("Sélectionnez une facture"); return; }
    if (!factureData) { toast.error("Chargez d'abord la facture"); return; }

    const lignesValides = lignes.filter((l) => l.qte_input > 0);
    if (!lignesValides.length) { toast.error("Au moins une ligne avec quantité > 0 requise"); return; }

    const nbCartons = parseInt(nombreCartons) || 0;
    if (nbCartons < 1) { toast.error("Le nombre de cartons doit être au moins 1"); return; }

    const payload = {
      facture_id: fid,
      lignes: lignesValides.map((l) => ({
        ligne_facture_id: l.ligne_facture_id,
        produit_id: l.produit_id,
        designation: l.designation,
        quantite_facturee: l.quantite_facturee,
        quantite_colisee: l.qte_input,
      })),
      nombre_cartons: nbCartons,
      notes: notes || null,
    };

    setLoading(true);
    try {
      if (colisExistant) {
        await updateColis(colisExistant.colis_id, {
          lignes: payload.lignes,
          nombre_cartons: payload.nombre_cartons,
          notes: payload.notes,
        });
        toast.success("Colis modifié avec succès");
      } else {
        await createColis(payload);
        toast.success("Colis créé avec succès");
      }
      onSuccess();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Erreur lors de l'enregistrement");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Sélection facture */}
      {!factureId && (
        <div className="space-y-2">
          <Label>Référence ou ID de la facture</Label>
          <div className="flex gap-2">
            <Input
              placeholder="ex: FABS-FC-26-27-0001 ou fac_..."
              value={factureInput}
              onChange={(e) => setFactureInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && chargerFacture(factureInput)}
            />
            <Button
              variant="outline"
              onClick={() => chargerFacture(factureInput)}
              disabled={searchingFacture}
            >
              {searchingFacture ? "..." : "Charger"}
            </Button>
          </div>
        </div>
      )}

      {factureId && !factureData && (
        <div className="text-center py-4">
          <Button onClick={() => chargerFacture(factureId)} variant="outline" disabled={searchingFacture}>
            {searchingFacture ? "Chargement..." : "Charger les lignes de la facture"}
          </Button>
        </div>
      )}

      {/* Infos facture chargée */}
      {factureData && (
        <>
          <div className="rounded-md bg-blue-50 dark:bg-blue-900/20 p-3 text-sm">
            <div className="font-semibold text-blue-800 dark:text-blue-300">
              Facture {factureData.facture_reference}
            </div>
            <div className="text-blue-600 dark:text-blue-400 mt-1">
              Statut: {factureData.facture_statut} · {factureData.nb_colis} colis existant(s)
            </div>
          </div>

          {/* Lignes */}
          <div className="space-y-2">
            <Label>Lignes à coliser</Label>
            {lignes.length === 0 && (
              <div className="flex items-center gap-2 text-amber-600 text-sm p-2 bg-amber-50 dark:bg-amber-900/20 rounded">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                Toutes les quantités de cette facture ont déjà été colisées.
              </div>
            )}
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-gray-500 dark:text-white/50">
                    <th className="text-left py-2 pr-3">Produit</th>
                    <th className="text-center py-2 px-2">Facturé</th>
                    <th className="text-center py-2 px-2">Restant</th>
                    <th className="text-center py-2 px-2 w-24">Qté à coliser</th>
                  </tr>
                </thead>
                <tbody>
                  {lignes.map((ligne, idx) => (
                    <tr key={ligne.ligne_facture_id} className="border-b last:border-0">
                      <td className="py-2 pr-3">
                        <div className="font-medium">{ligne.designation}</div>
                        <div className="text-xs text-gray-400">{ligne.produit_id}</div>
                      </td>
                      <td className="text-center py-2 px-2 text-gray-500 dark:text-white/50">{ligne.quantite_facturee}</td>
                      <td className="text-center py-2 px-2">
                        <span className={ligne.quantite_restante === 0 ? "text-red-500" : "text-green-600 font-medium"}>
                          {ligne.quantite_restante ?? (ligne.quantite_facturee - (factureData.lignes.find(l => l.ligne_id === ligne.ligne_facture_id)?.quantite_colisee || 0))}
                        </span>
                      </td>
                      <td className="py-2 px-2">
                        <Input
                          type="number"
                          min={0}
                          max={ligne.quantite_restante || ligne.quantite_facturee}
                          value={ligne.qte_input}
                          onChange={(e) => handleQteChange(idx, e.target.value)}
                          className="w-20 text-center"
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Nombre de cartons */}
          <div className="space-y-1">
            <Label>Nombre de cartons</Label>
            <Input
              type="number"
              min={1}
              step={1}
              value={nombreCartons}
              onChange={(e) => setNombreCartons(e.target.value)}
              className="w-32"
            />
            {parseInt(nombreCartons) > 0 && (
              <div className="flex flex-wrap gap-1.5 pt-2">
                {Array.from({ length: Math.min(parseInt(nombreCartons), 50) }, (_, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center justify-center px-2 py-1 rounded bg-orange-100 dark:bg-orange-500/20 text-orange-700 dark:text-orange-300 text-xs font-bold font-mono"
                  >
                    {i + 1}/{parseInt(nombreCartons)}
                  </span>
                ))}
              </div>
            )}
            <p className="text-xs text-gray-400 mt-1">
              Chaque carton sera étiqueté automatiquement (ex: 1/{parseInt(nombreCartons) || "N"}, 2/{parseInt(nombreCartons) || "N"}...).
            </p>
          </div>
          <div className="space-y-1">
            <Label>Notes (optionnel)</Label>
            <Textarea
              rows={2}
              placeholder="Instructions, remarques..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>
        </>
      )}

      <div className="flex justify-end gap-2 pt-2">
        <Button variant="outline" onClick={onCancel} disabled={loading}>
          Annuler
        </Button>
        <Button
          onClick={handleSubmit}
          disabled={loading || !factureData || lignes.filter(l => l.qte_input > 0).length === 0}
          className="bg-[#0A2540] hover:bg-[#0A2540]/90"
        >
          {loading ? "Enregistrement..." : colisExistant ? "Modifier le colis" : "Créer le colis"}
        </Button>
      </div>
    </div>
  );
}

// ─── PAGE PRINCIPALE ──────────────────────────────────────────────────────────

const Colis = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [statutFilter, setStatutFilter] = useState("");
  const [selectedColis, setSelectedColis] = useState(null);
  const [showDetail, setShowDetail] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingColis, setEditingColis] = useState(null);
  const [expandedRows, setExpandedRows] = useState({});

  const debouncedSearch = useDebouncedValue(search, 350);

  const { data: colisList = [], isLoading } = useQuery(
    ["colis", debouncedSearch, statutFilter],
    () => listColis({ q: debouncedSearch || undefined, statut: statutFilter || undefined }),
    { enabled: !!user }
  );

  const deleteMutation = useMutation(deleteColis, {
    onSuccess: () => {
      queryClient.invalidateQueries(["colis"]);
      toast.success("Colis supprimé");
    },
    onError: (err) => toast.error(err.response?.data?.detail || "Erreur suppression"),
  });

  const statutMutation = useMutation(
    ({ colisId, statut, motif }) => updateColisStatut(colisId, statut, motif),
    {
      onSuccess: (_, vars) => {
        queryClient.invalidateQueries(["colis"]);
        toast.success(`Colis ${vars.statut === "valide" ? "validé" : vars.statut === "annule" ? "annulé" : "mis à jour"}`);
      },
      onError: (err) => toast.error(err.response?.data?.detail || "Erreur mise à jour"),
    }
  );

  const handleDelete = (colis) => {
    if (window.confirm(`Supprimer le colis ${colis.reference} ?`)) {
      deleteMutation.mutate(colis.colis_id);
    }
  };

  const handleValider = (colis) => {
    if (window.confirm(`Valider le colis ${colis.reference} ?`)) {
      statutMutation.mutate({ colisId: colis.colis_id, statut: "valide" });
    }
  };

  const handleAnnuler = (colis) => {
    const motif = window.prompt(`Motif d'annulation du colis ${colis.reference} ?`);
    if (motif !== null) {
      statutMutation.mutate({ colisId: colis.colis_id, statut: "annule", motif });
    }
  };

  const toggleExpand = (colisId) => {
    setExpandedRows((prev) => ({ ...prev, [colisId]: !prev[colisId] }));
  };

  const canWrite = user && ["super_admin", "admin", "gestionnaire", "preparateur"].includes(user.role);
  const canValidate = user && ["super_admin", "admin", "gestionnaire"].includes(user.role);
  const canDelete = user && ["super_admin", "admin"].includes(user.role);

  if (isLoading) return <DashboardLayout><div className="p-8 text-gray-500 dark:text-white/50">Chargement...</div></DashboardLayout>;

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-[#0A2540] dark:text-white">Gestion des Colis</h1>
            <p className="text-sm text-[#0A2540]/60 dark:text-white/60 mt-1">
              Colisage lié aux factures émises · {colisList.length} colis
            </p>
          </div>
          {canWrite && (
            <Button
              className="bg-[#0A2540] hover:bg-[#0A2540]/90"
              onClick={() => { setEditingColis(null); setShowForm(true); }}
            >
              <Plus className="w-4 h-4 mr-2" />
              Nouveau Colis
            </Button>
          )}
        </div>

        {/* Filtres */}
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Réf. colis, réf. facture, client..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10"
            />
          </div>
          <select
            value={statutFilter}
            onChange={(e) => setStatutFilter(e.target.value)}
            className="px-4 py-2 border rounded-md bg-white dark:bg-[#040f1a] dark:border-gray-700 text-sm"
          >
            <option value="">Tous les statuts</option>
            <option value="en_preparation">En préparation</option>
            <option value="valide">Validé</option>
            <option value="expedie">Expédié</option>
            <option value="annule">Annulé</option>
          </select>
        </div>

        {/* Table */}
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50 dark:bg-[#040f1a]/50">
                    <th className="text-left py-3 px-4 w-8"></th>
                    <th className="text-left py-3 px-4 font-semibold">Référence</th>
                    <th className="text-left py-3 px-4 font-semibold">Facture</th>
                    <th className="text-left py-3 px-4 font-semibold">Client</th>
                    <th className="text-left py-3 px-4 font-semibold">Lignes</th>
                    <th className="text-left py-3 px-4 font-semibold">Cartons</th>
                    <th className="text-left py-3 px-4 font-semibold">Statut</th>
                    <th className="text-left py-3 px-4 font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {colisList.map((colis) => (
                    <>
                      <tr
                        key={colis.colis_id}
                        className="border-b hover:bg-gray-50 dark:hover:bg-[#040f1a]/30"
                      >
                        <td className="py-3 px-4">
                          <button
                            onClick={() => toggleExpand(colis.colis_id)}
                            className="text-gray-400 hover:text-gray-600 dark:text-white/70"
                          >
                            {expandedRows[colis.colis_id]
                              ? <ChevronDown className="w-4 h-4" />
                              : <ChevronRight className="w-4 h-4" />}
                          </button>
                        </td>
                        <td className="py-3 px-4 font-medium font-mono text-sm">
                          {colis.reference}
                        </td>
                        <td className="py-3 px-4">
                          <span className="font-mono text-[#F97316] text-xs">
                            {colis.facture_reference || colis.facture_id}
                          </span>
                          {colis.commande_reference && (
                            <div className="text-xs text-gray-400">Cmd: {colis.commande_reference}</div>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-medium">{colis.client_nom || <span className="text-gray-400 italic">—</span>}</div>
                          {colis.client_ville && <div className="text-xs text-gray-400">{colis.client_ville}</div>}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded font-mono">
                            {colis.lignes?.length || 0}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="inline-flex items-center gap-1 text-xs bg-orange-100 dark:bg-orange-500/20 text-orange-700 dark:text-orange-300 px-2 py-0.5 rounded font-mono font-bold">
                            <Package className="w-3 h-3" />
                            {colis.nombre_cartons ?? 1} carton{(colis.nombre_cartons ?? 1) > 1 ? "s" : ""}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <StatutBadge statut={colis.statut} />
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex gap-1">
                            <Button
                              variant="ghost" size="sm"
                              onClick={() => { setSelectedColis(colis); setShowDetail(true); }}
                              title="Voir détails"
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            {canWrite && colis.statut === "en_preparation" && (
                              <Button
                                variant="ghost" size="sm"
                                onClick={() => { setEditingColis(colis); setShowForm(true); }}
                                title="Modifier"
                              >
                                <Edit className="w-4 h-4 text-blue-500" />
                              </Button>
                            )}
                            {canValidate && colis.statut === "en_preparation" && (
                              <Button
                                variant="ghost" size="sm"
                                onClick={() => handleValider(colis)}
                                title="Valider"
                              >
                                <CheckCircle className="w-4 h-4 text-green-600" />
                              </Button>
                            )}
                            {canValidate && ["en_preparation", "valide"].includes(colis.statut) && (
                              <Button
                                variant="ghost" size="sm"
                                onClick={() => handleAnnuler(colis)}
                                title="Annuler"
                              >
                                <XCircle className="w-4 h-4 text-orange-500" />
                              </Button>
                            )}
                            {canDelete && colis.statut === "en_preparation" && (
                              <Button
                                variant="ghost" size="sm"
                                onClick={() => handleDelete(colis)}
                                title="Supprimer"
                              >
                                <Trash2 className="w-4 h-4 text-red-500" />
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>

                      {/* Lignes détaillées (expandable) */}
                      {expandedRows[colis.colis_id] && (
                        <tr key={`${colis.colis_id}-detail`} className="bg-gray-50 dark:bg-white/5/50 dark:bg-[#040f1a]/20">
                          <td colSpan={8} className="px-8 py-3">
                            <table className="w-full text-xs">
                              <thead>
                                <tr className="text-gray-500 dark:text-white/50 border-b">
                                  <th className="text-left pb-1">Produit</th>
                                  <th className="text-center pb-1">Qté facturée</th>
                                  <th className="text-center pb-1">Qté colisée</th>
                                </tr>
                              </thead>
                              <tbody>
                                {(colis.lignes || []).map((lg, i) => (
                                  <tr key={i} className="border-b last:border-0">
                                    <td className="py-1 pr-4">
                                      <div className="font-medium">{lg.designation}</div>
                                      <div className="text-gray-400">{lg.produit_id}</div>
                                    </td>
                                    <td className="text-center py-1">{lg.quantite_facturee}</td>
                                    <td className="text-center py-1 font-semibold text-[#0A2540] dark:text-white">{lg.quantite_colisee}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                            <div className="mt-3">
                              <div className="text-xs font-medium text-gray-500 dark:text-white/50 mb-1">
                                Cartons ({colis.nombre_cartons ?? 1})
                              </div>
                              <div className="flex flex-wrap gap-1.5">
                                {Array.from({ length: Math.min(colis.nombre_cartons ?? 1, 50) }, (_, i) => (
                                  <span
                                    key={i}
                                    className="inline-flex items-center justify-center px-2 py-1 rounded bg-orange-100 dark:bg-orange-500/20 text-orange-700 dark:text-orange-300 text-xs font-bold font-mono"
                                  >
                                    {i + 1}/{colis.nombre_cartons ?? 1}
                                  </span>
                                ))}
                              </div>
                            </div>
                            {colis.notes && (
                              <div className="mt-2 text-xs text-gray-500 dark:text-white/50">
                                <span className="font-medium">Notes:</span> {colis.notes}
                              </div>
                            )}
                          </td>
                        </tr>
                      )}
                    </>
                  ))}
                </tbody>
              </table>

              {colisList.length === 0 && (
                <div className="text-center py-12 text-gray-400">
                  <Package className="w-10 h-10 mx-auto mb-3 opacity-30" />
                  <p>Aucun colis trouvé</p>
                  {canWrite && (
                    <Button
                      variant="outline" size="sm" className="mt-3"
                      onClick={() => { setEditingColis(null); setShowForm(true); }}
                    >
                      <Plus className="w-4 h-4 mr-1" /> Créer un colis
                    </Button>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Dialog Détail */}
      <Dialog open={showDetail} onOpenChange={setShowDetail}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Colis — {selectedColis?.reference}</DialogTitle>
            <DialogDescription>
              Facture: <span className="font-mono text-[#F97316]">{selectedColis?.facture_reference}</span>
            </DialogDescription>
          </DialogHeader>
          {selectedColis && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div><span className="text-gray-500 dark:text-white/50">Statut:</span>{" "}<StatutBadge statut={selectedColis.statut} /></div>
                <div><span className="text-gray-500 dark:text-white/50">Client:</span> <span className="font-medium">{selectedColis.client_nom || "—"}</span></div>
                <div><span className="text-gray-500 dark:text-white/50">Ville:</span> {selectedColis.client_ville || "—"}</div>
                <div><span className="text-gray-500 dark:text-white/50">Tél:</span> {selectedColis.client_telephone || "—"}</div>
                <div><span className="text-gray-500 dark:text-white/50">Nombre de cartons:</span> <span className="font-bold text-orange-600">{selectedColis.nombre_cartons ?? 1}</span></div>
                <div><span className="text-gray-500 dark:text-white/50">Code-barres:</span> <span className="font-mono">{selectedColis.code_barres}</span></div>
              </div>
              <Separator />
              <div>
                <div className="font-medium text-sm mb-2">Cartons</div>
                <div className="flex flex-wrap gap-1.5 mb-4">
                  {Array.from({ length: Math.min(selectedColis.nombre_cartons ?? 1, 50) }, (_, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center justify-center px-2.5 py-1 rounded bg-orange-100 dark:bg-orange-500/20 text-orange-700 dark:text-orange-300 text-sm font-bold font-mono"
                    >
                      {i + 1}/{selectedColis.nombre_cartons ?? 1}
                    </span>
                  ))}
                </div>
                <div className="font-medium text-sm mb-2">Lignes colisées</div>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-gray-500 dark:text-white/50 text-xs border-b">
                      <th className="text-left pb-1">Produit</th>
                      <th className="text-center pb-1">Facturé</th>
                      <th className="text-center pb-1">Colisé</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(selectedColis.lignes || []).map((lg, i) => (
                      <tr key={i} className="border-b last:border-0">
                        <td className="py-1 pr-3">
                          <div>{lg.designation}</div>
                          <div className="text-xs text-gray-400">{lg.produit_id}</div>
                        </td>
                        <td className="text-center py-1">{lg.quantite_facturee}</td>
                        <td className="text-center py-1 font-semibold">{lg.quantite_colisee}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {selectedColis.notes && (
                <div className="text-sm"><span className="text-gray-500 dark:text-white/50">Notes:</span> {selectedColis.notes}</div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Dialog Création / Édition */}
      <Dialog open={showForm} onOpenChange={(v) => { if (!v) { setShowForm(false); setEditingColis(null); } }}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingColis ? "Modifier le colis" : "Nouveau colis"}</DialogTitle>
            <DialogDescription>
              {editingColis
                ? `Modification de ${editingColis.reference}`
                : "Créer un colis depuis une facture émise"}
            </DialogDescription>
          </DialogHeader>
          <ColisForm
            factureId={editingColis?.facture_id || null}
            colisExistant={editingColis}
            onSuccess={() => {
              setShowForm(false);
              setEditingColis(null);
              queryClient.invalidateQueries(["colis"]);
            }}
            onCancel={() => { setShowForm(false); setEditingColis(null); }}
          />
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
};

export default Colis;
