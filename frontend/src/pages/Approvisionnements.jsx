/**
 * Page Approvisionnements — Liste + Nouveau (Sprint 4 V10)
 * Gestion des bons de commande fournisseurs / réceptions
 */
import React, { useState, useEffect, useCallback, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  Plus, Search, Inbox, Trash2, Eye, FileText, Package, Calendar, CheckCircle2, Clock,
} from "lucide-react";
import { toast } from "sonner";
import axios from "axios";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "../components/ui/dialog";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";
import API_BASE_URL from "../config/api";
import { useAuth } from "../hooks/useAuth";
import { can } from "../constants/permissions";
import { listApprovisionnements, createApprovisionnement } from "../services/approvisionnementApi";
import { listFournisseurs } from "../services/fournisseursApi";

const STATUT_COLORS = {
  brouillon: { label: "Brouillon",  color: "bg-gray-400 text-white",      icon: FileText },
  valide:    { label: "Validé",     color: "bg-[#10B981] text-white",     icon: CheckCircle2 },
  en_cours:  { label: "En cours",   color: "bg-[#F59E0B] text-white",     icon: Clock },
  recu:      { label: "Reçu",       color: "bg-[#10B981] text-white",     icon: CheckCircle2 },
  annule:    { label: "Annulé",     color: "bg-[#EF4444] text-white",     icon: Trash2 },
};

const formatMoney = (v) =>
  new Intl.NumberFormat("fr-FR").format(Math.round(v || 0)) + " FCFA";

const EMPTY_LIGNE = { produit_id: "", quantite: 1, prix_achat: 0 };
const EMPTY_FORM = { fournisseur_id: "", depot: "principal", notes: "", lignes: [{ ...EMPTY_LIGNE }] };

export default function Approvisionnements() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterStatut, setFilterStatut] = useState("all");

  // Modale création
  const [showModal, setShowModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [fournisseurs, setFournisseurs] = useState([]);
  const [produits, setProduits] = useState([]);

  const canWrite = user && can(user.role, "approvisionnements");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listApprovisionnements({ limit: 200 });
      setItems(Array.isArray(data) ? data : data?.items || []);
    } catch (e) {
      console.error(e);
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openCreate = async () => {
    setForm({ ...EMPTY_FORM, lignes: [{ ...EMPTY_LIGNE }] });
    try {
      const [f, p] = await Promise.all([
        listFournisseurs({ limit: 200 }),
        axios.get(`${API_BASE_URL}/produits?limit=500`).then((r) => r.data),
      ]);
      setFournisseurs(Array.isArray(f) ? f : f?.items || []);
      const prods = Array.isArray(p) ? p : p?.items || [];
      setProduits(prods.map((x) => ({
        product_id: x.product_id || x.produit_id,
        titre: x.titre || x.nom || x.reference,
      })));
    } catch (e) {
      console.error(e);
      toast.error("Erreur chargement fournisseurs / produits");
    }
    setShowModal(true);
  };

  const updateLigne = (idx, field, value) => {
    setForm((prev) => {
      const lignes = [...prev.lignes];
      lignes[idx] = { ...lignes[idx], [field]: value };
      return { ...prev, lignes };
    });
  };

  const addLigne = () => setForm((p) => ({ ...p, lignes: [...p.lignes, { ...EMPTY_LIGNE }] }));
  const removeLigne = (idx) => setForm((p) => ({ ...p, lignes: p.lignes.filter((_, i) => i !== idx) }));

  const totals = useMemo(() => {
    const total = form.lignes.reduce((s, l) => s + (Number(l.quantite) || 0) * (Number(l.prix_achat) || 0), 0);
    const lines = form.lignes.length;
    const qte = form.lignes.reduce((s, l) => s + (Number(l.quantite) || 0), 0);
    return { total, lines, qte };
  }, [form.lignes]);

  const handleSave = async () => {
    if (!form.fournisseur_id) return toast.error("Veuillez sélectionner un fournisseur");
    if (form.lignes.some((l) => !l.produit_id || !l.quantite || l.prix_achat == null))
      return toast.error("Chaque ligne doit avoir produit, quantité et prix d'achat");

    setSaving(true);
    try {
      const created = await createApprovisionnement({
        fournisseur_id: form.fournisseur_id,
        depot: form.depot,
        lignes: form.lignes.map((l) => ({
          produit_id: l.produit_id,
          quantite: Number(l.quantite),
          prix_achat: Number(l.prix_achat),
        })),
        notes: form.notes || undefined,
      });
      toast.success(`Approvisionnement ${created.reference} créé`);
      setShowModal(false);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erreur lors de la création");
    } finally {
      setSaving(false);
    }
  };

  const filtered = items.filter((a) => {
    if (filterStatut !== "all" && a.statut !== filterStatut) return false;
    if (!search) return true;
    const s = search.toLowerCase();
    return [a.reference, a.fournisseur_nom, a.fournisseur_id, a.notes]
      .some((v) => (v || "").toLowerCase().includes(s));
  });

  const totalGeneral = items.reduce(
    (s, a) => s + a.lignes.reduce((ls, l) => ls + (l.quantite || 0) * (l.prix_achat || 0), 0),
    0,
  );
  const inDraft = items.filter((a) => a.statut === "brouillon").length;
  const validated = items.filter((a) => a.statut === "valide" || a.statut === "recu").length;

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="approvisionnements-page">
        <PageHeader
          title="Approvisionnements"
          subtitle="Bons d'achat fournisseurs — réceptions et mise à jour stock"
          pagePath="/approvisionnements"
          actions={
            canWrite && (
              <Button
                className="bg-blue-600 hover:bg-blue-700 text-white h-9"
                onClick={openCreate}
                data-testid="btn-create"
              >
                <Plus className="h-4 w-4 mr-2" /> Nouvel approvisionnement
              </Button>
            )
          }
        />

        {/* KPI */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <KPICard label="Total" value={items.length} color="text-[#0A2540]" testId="kpi-total" />
          <KPICard label="Brouillons" value={inDraft} color="text-[#F59E0B]" testId="kpi-draft" />
          <KPICard label="Validés / Reçus" value={validated} color="text-[#10B981]" testId="kpi-validated" />
          <KPICard label="Montant total" value={formatMoney(totalGeneral)} color="text-[#FF6200]" testId="kpi-amount" small />
        </div>

        {/* Filtres */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  data-testid="appro-search"
                  type="search"
                  placeholder="Rechercher par référence, fournisseur, notes…"
                  className="pl-9"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <Select value={filterStatut} onValueChange={setFilterStatut}>
                <SelectTrigger className="w-full md:w-[200px]" data-testid="appro-statut-filter">
                  <SelectValue placeholder="Statut" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tous les statuts</SelectItem>
                  {Object.entries(STATUT_COLORS).map(([k, v]) => (
                    <SelectItem key={k} value={k}>{v.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Liste */}
        <Card>
          <CardHeader>
            <CardTitle>Liste des approvisionnements</CardTitle>
            <CardDescription>{filtered.length} ligne(s)</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-40 w-full" />
            ) : filtered.length === 0 ? (
              <div className="text-center py-16 text-muted-foreground" data-testid="appro-empty">
                <Inbox className="h-12 w-12 mx-auto mb-3 opacity-30" />
                <p>{search || filterStatut !== "all" ? "Aucun approvisionnement ne correspond." : "Aucun approvisionnement enregistré."}</p>
                {!search && filterStatut === "all" && canWrite && (
                  <Button onClick={openCreate} className="mt-4 bg-[#FF6200] hover:bg-[#FF6200]/90 text-white" data-testid="btn-empty-create">
                    <Plus className="h-4 w-4 mr-2" /> Créer le premier
                  </Button>
                )}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm" data-testid="appro-table">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-2 w-32">Référence</th>
                      <th className="text-left py-3 px-2">Fournisseur</th>
                      <th className="text-left py-3 px-2">Dépôt</th>
                      <th className="text-center py-3 px-2">Lignes</th>
                      <th className="text-center py-3 px-2">Statut</th>
                      <th className="text-right py-3 px-2">Montant</th>
                      <th className="text-left py-3 px-2">Créé le</th>
                      <th className="text-right py-3 px-2 w-16"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((a) => {
                      const conf = STATUT_COLORS[a.statut] || { label: a.statut, color: "bg-gray-400 text-white", icon: FileText };
                      const Icon = conf.icon;
                      const montant = a.lignes.reduce((s, l) => s + (l.quantite || 0) * (l.prix_achat || 0), 0);
                      return (
                        <tr
                          key={a.approvisionnement_id}
                          className="border-b hover:bg-muted/50 cursor-pointer"
                          onClick={() => navigate(`/approvisionnements/${a.approvisionnement_id}`)}
                          data-testid={`appro-row-${a.approvisionnement_id}`}
                        >
                          <td className="py-3 px-2 font-mono text-xs">{a.reference}</td>
                          <td className="py-3 px-2 font-medium">{a.fournisseur_nom || a.fournisseur_id}</td>
                          <td className="py-3 px-2 capitalize">{a.depot}</td>
                          <td className="py-3 px-2 text-center">{a.lignes?.length || 0}</td>
                          <td className="py-3 px-2 text-center">
                            <Badge className={`${conf.color} inline-flex items-center gap-1`}>
                              <Icon className="h-3 w-3" /> {conf.label}
                            </Badge>
                          </td>
                          <td className="py-3 px-2 text-right font-semibold tabular-nums">{formatMoney(montant)}</td>
                          <td className="py-3 px-2 text-xs text-muted-foreground">{a.created_at?.slice(0, 10)}</td>
                          <td className="py-3 px-2 text-right">
                            <Eye className="h-4 w-4 inline text-muted-foreground" />
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Modale création */}
        <Dialog open={showModal} onOpenChange={setShowModal}>
          <DialogContent className="sm:max-w-[860px] max-h-[90vh] overflow-y-auto" data-testid="appro-modal">
            <DialogHeader>
              <DialogTitle>Nouvel approvisionnement</DialogTitle>
              <DialogDescription>
                Bon d&apos;achat à un fournisseur. Les statuts évoluent : Brouillon → Validé (stock incrémenté).
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-2">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label className="text-sm">Fournisseur *</Label>
                  <Select
                    value={form.fournisseur_id}
                    onValueChange={(v) => setForm({ ...form, fournisseur_id: v })}
                  >
                    <SelectTrigger data-testid="select-fournisseur">
                      <SelectValue placeholder="Choisir un fournisseur" />
                    </SelectTrigger>
                    <SelectContent>
                      {fournisseurs.map((f) => (
                        <SelectItem key={f.fournisseur_id} value={f.fournisseur_id}>
                          {f.reference} — {f.nom}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label className="text-sm">Dépôt *</Label>
                  <Select value={form.depot} onValueChange={(v) => setForm({ ...form, depot: v })}>
                    <SelectTrigger data-testid="select-depot"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="principal">Principal</SelectItem>
                      <SelectItem value="secondaire">Secondaire</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-1.5">
                <Label className="text-sm">Notes (optionnel)</Label>
                <Textarea
                  data-testid="input-notes"
                  rows={2}
                  maxLength={1000}
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  placeholder="Conditions, transport, références bon de commande…"
                />
              </div>

              {/* Lignes produits */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-semibold">Lignes produits *</Label>
                  <Button variant="outline" size="sm" onClick={addLigne} data-testid="btn-add-ligne">
                    <Plus className="h-3.5 w-3.5 mr-1" /> Ajouter une ligne
                  </Button>
                </div>
                <div className="overflow-x-auto rounded-md border">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/40">
                        <th className="text-left py-2 px-2">Produit *</th>
                        <th className="text-right py-2 px-2 w-24">Qté *</th>
                        <th className="text-right py-2 px-2 w-32">Prix unitaire *</th>
                        <th className="text-right py-2 px-2 w-32">Total ligne</th>
                        <th className="py-2 px-2 w-10"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {form.lignes.map((l, idx) => (
                        <tr key={idx} className="border-b" data-testid={`appro-line-${idx}`}>
                          <td className="py-1 px-1">
                            <Select value={l.produit_id} onValueChange={(v) => updateLigne(idx, "produit_id", v)}>
                              <SelectTrigger data-testid={`select-produit-${idx}`}>
                                <SelectValue placeholder="Choisir un produit" />
                              </SelectTrigger>
                              <SelectContent className="max-h-72">
                                {produits.map((p) => (
                                  <SelectItem key={p.product_id} value={p.product_id}>
                                    {p.titre || p.nom || p.product_id}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </td>
                          <td className="py-1 px-1">
                            <Input
                              type="number" min={1} className="text-right"
                              value={l.quantite}
                              onChange={(e) => updateLigne(idx, "quantite", Number(e.target.value) || 0)}
                            />
                          </td>
                          <td className="py-1 px-1">
                            <Input
                              type="number" min={0} step="100" className="text-right"
                              value={l.prix_achat}
                              onChange={(e) => updateLigne(idx, "prix_achat", Number(e.target.value) || 0)}
                            />
                          </td>
                          <td className="py-2 px-2 text-right font-semibold tabular-nums">
                            {formatMoney((Number(l.quantite) || 0) * (Number(l.prix_achat) || 0))}
                          </td>
                          <td className="py-1 px-1 text-center">
                            {form.lignes.length > 1 && (
                              <button onClick={() => removeLigne(idx)} className="text-[#EF4444]" data-testid={`btn-remove-ligne-${idx}`}>
                                <Trash2 className="h-4 w-4" />
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-muted/30 font-semibold">
                      <tr>
                        <td colSpan={2} className="py-2 px-2">{totals.lines} ligne(s) · {totals.qte} unité(s)</td>
                        <td className="py-2 px-2 text-right">Total HT :</td>
                        <td className="py-2 px-2 text-right text-[#0A2540] dark:text-white text-base">
                          {formatMoney(totals.total)}
                        </td>
                        <td></td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowModal(false)} data-testid="btn-cancel">
                Annuler
              </Button>
              <Button
                onClick={handleSave}
                disabled={saving}
                className="bg-[#FF6200] hover:bg-[#FF6200]/90 text-white"
                data-testid="btn-save"
              >
                {saving ? "Enregistrement…" : "Créer le brouillon"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}

function KPICard({ label, value, color, testId, small }) {
  return (
    <Card data-testid={testId}>
      <CardContent className="pt-5 pb-4">
        <p className="text-xs text-muted-foreground uppercase tracking-wide">{label}</p>
        <p className={`${small ? "text-lg" : "text-2xl"} font-bold mt-2 ${color}`}>{value}</p>
      </CardContent>
    </Card>
  );
}
