import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Search, Plus, Pencil, Package, Filter, ArrowDown, ArrowUp, 
  RefreshCw, Truck, Warehouse, ClipboardList, BarChart3, ChevronLeft, ChevronRight,
  AlertCircle, RotateCw, Building2, Phone, Mail, MapPin
} from "lucide-react";
import { toast } from "sonner";

import DashboardLayout from "../components/layout/DashboardLayout";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "../components/ui/dialog";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";

import { listProducts, disableProduct } from "../services/produitsApi";
import { listFournisseurs, createFournisseur } from "../services/fournisseursApi";
import { createApprovisionnement } from "../services/approvisionnementApi";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { formatFCFA } from "../utils/format";
import { useAuth } from "../hooks/useAuth";

const WRITE_ROLES = new Set([
  "super_admin", "directeur_general", "gestionnaire_stock",
]);
const FINANCIAL_ROLES = new Set(["super_admin", "directeur_general", "comptable"]);

const formatDate = (s) => (s ? new Date(s).toLocaleDateString("fr-FR") : "-");

export default function ProduitsInventaire() {
  const navigate = useNavigate();
  const { role } = useAuth();
  const canWrite = WRITE_ROLES.has(role);
  const seePrixAchat = FINANCIAL_ROLES.has(role);

  const [activeTab, setActiveTab] = useState("produits");
  const [q, setQ] = useState("");
  const [fournisseurFilter, setFournisseurFilter] = useState("");
  const [depotFilter, setDepotFilter] = useState("");
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 20;

  const [products, setProducts] = useState({ items: [], total: 0 });
  const [fournisseurs, setFournisseurs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const dq = useDebouncedValue(q, 300);

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await listProducts({
        q: dq || undefined,
        fournisseur_id: fournisseurFilter || undefined,
        depot: depotFilter || undefined,
        page,
        page_size: PAGE_SIZE,
      });
      setProducts(r);
    } catch (e) {
      setError(e?.response?.data?.detail || "Erreur de chargement");
    } finally {
      setLoading(false);
    }
  }, [dq, fournisseurFilter, depotFilter, page]);

  const fetchFournisseurs = useCallback(async () => {
    try {
      const r = await listFournisseurs({ limit: 100 });
      setFournisseurs(r.items || r || []);
    } catch (e) {
      console.error("Erreur chargement fournisseurs:", e);
    }
  }, []);

  useEffect(() => {
    fetchProducts();
    fetchFournisseurs();
  }, [fetchProducts, fetchFournisseurs]);

  useEffect(() => { setPage(1); }, [dq, fournisseurFilter, depotFilter]);

  const totalPages = Math.max(1, Math.ceil(products.total / PAGE_SIZE));

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-[#FF6200] font-semibold">
              Module Produits / Inventaire
            </p>
            <h1 className="text-3xl font-bold tracking-tight text-[#0A2540] dark:text-white mt-1">
              Gestion des Manuels Scolaires
            </h1>
            <p className="text-sm text-gray-600 dark:text-white/60 mt-1">
              {products.total} produit{products.total > 1 ? "s" : ""} dans le catalogue.
            </p>
          </div>
          <div className="flex gap-2">
            {canWrite && (
              <Button onClick={() => setActiveTab("approvisionnement")} className="bg-[#FF6200] hover:bg-[#E65800] text-white">
                <Truck className="w-4 h-4 mr-2" /> Approvisionnement
              </Button>
            )}
            {canWrite && (
              <Button onClick={() => setActiveTab("fournisseurs")} variant="outline">
                <Building2 className="w-4 h-4 mr-2" /> Fournisseurs
              </Button>
            )}
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="produits" className="flex items-center gap-2">
              <Package className="w-4 h-4" /> Liste produits
            </TabsTrigger>
            <TabsTrigger value="inventaire" className="flex items-center gap-2">
              <ClipboardList className="w-4 h-4" /> Inventaire
            </TabsTrigger>
            <TabsTrigger value="mouvements" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" /> Mouvements
            </TabsTrigger>
            <TabsTrigger value="approvisionnement" className="flex items-center gap-2">
              <Truck className="w-4 h-4" /> Approvisionnement
            </TabsTrigger>
            <TabsTrigger value="fournisseurs" className="flex items-center gap-2">
              <Building2 className="w-4 h-4" /> Fournisseurs
            </TabsTrigger>
          </TabsList>

          <TabsContent value="produits" className="space-y-4">
            <ProduitsTab
              products={products}
              loading={loading}
              error={error}
              q={q}
              setQ={setQ}
              fournisseurFilter={fournisseurFilter}
              setFournisseurFilter={setFournisseurFilter}
              depotFilter={depotFilter}
              setDepotFilter={setDepotFilter}
              fournisseurs={fournisseurs}
              page={page}
              setPage={setPage}
              totalPages={totalPages}
              seePrixAchat={seePrixAchat}
              canWrite={canWrite}
              onRefresh={fetchProducts}
              pageSize={PAGE_SIZE}
            />
          </TabsContent>

          <TabsContent value="inventaire" className="space-y-4">
            <InventaireTab products={products} loading={loading} />
          </TabsContent>

          <TabsContent value="mouvements" className="space-y-4">
            <MouvementsTab />
          </TabsContent>

          <TabsContent value="approvisionnement" className="space-y-4">
            <ApprovisionnementTab
              fournisseurs={fournisseurs}
              products={products}
              onRefresh={fetchProducts}
              canWrite={canWrite}
            />
          </TabsContent>

          <TabsContent value="fournisseurs" className="space-y-4">
            <FournisseursTab
              fournisseurs={fournisseurs}
              onRefresh={fetchFournisseurs}
              canWrite={canWrite}
            />
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}

// Tab: Liste des produits
function ProduitsTab({
  products, loading, error, q, setQ,
  fournisseurFilter, setFournisseurFilter,
  depotFilter, setDepotFilter,
  fournisseurs, page, setPage, totalPages,
  seePrixAchat, canWrite, onRefresh, pageSize
}) {
  const PAGE_SIZE = pageSize || 20;
  const handleDisable = async (product) => {
    if (!window.confirm(`Désactiver le produit "${product.titre}" ?`)) return;
    try {
      await disableProduct(product.product_id);
      toast.success(`${product.titre} désactivé`);
      onRefresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Échec de la désactivation");
    }
  };

  return (
    <>
      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="w-5 h-5" /> Filtres
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative md:col-span-2">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <Input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Code produit, nom, ISBN..."
                className="pl-9"
              />
            </div>
            <Select value={fournisseurFilter} onValueChange={setFournisseurFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Tous fournisseurs" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Tous fournisseurs</SelectItem>
                {fournisseurs.map((f) => (
                  <SelectItem key={f.fournisseur_id} value={f.fournisseur_id}>
                    {f.nom}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={depotFilter} onValueChange={setDepotFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Tous dépôts" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Tous dépôts</SelectItem>
                <SelectItem value="principal">Dépôt principal</SelectItem>
                <SelectItem value="secondaire">Dépôt secondaire</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {error && (
        <div className="bg-red-50 border border-[#C62828]/30 text-[#C62828] rounded-lg p-4 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          {error}
          <button onClick={onRefresh} className="ml-auto text-xs font-semibold underline">
            <RotateCw className="w-3 h-3 inline mr-1" /> Réessayer
          </button>
        </div>
      )}

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 dark:bg-white/5 text-[10px] uppercase tracking-wider text-[#0A2540]/70 dark:text-white/60">
                  <th className="text-left px-4 py-3 font-semibold">Code (SKU)</th>
                  <th className="text-left px-4 py-3 font-semibold">Nom produit</th>
                  <th className="text-left px-4 py-3 font-semibold">Catégorie</th>
                  <th className="text-left px-4 py-3 font-semibold">Fournisseur</th>
                  <th className="text-right px-4 py-3 font-semibold">Stock</th>
                  {seePrixAchat && <th className="text-right px-4 py-3 font-semibold">Prix achat</th>}
                  <th className="text-right px-4 py-3 font-semibold">Prix vente</th>
                  <th className="text-right px-4 py-3 font-semibold">Stock min</th>
                  <th className="text-left px-4 py-3 font-semibold">Dépôt</th>
                  <th className="text-left px-4 py-3 font-semibold">Dernière entrée</th>
                  <th className="text-right px-4 py-3 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading && (
                  <tr><td colSpan={seePrixAchat ? 11 : 10} className="px-4 py-10 text-center text-gray-500">Chargement…</td></tr>
                )}
                {!loading && products.items.length === 0 && (
                  <tr><td colSpan={seePrixAchat ? 11 : 10} className="px-4 py-10 text-center text-gray-500">Aucun produit trouvé.</td></tr>
                )}
                {!loading && products.items.map((p) => (
                  <tr key={p.product_id} className="border-t border-gray-100 dark:border-white/10 hover:bg-gray-50 dark:hover:bg-white/5">
                    <td className="px-4 py-3 font-mono text-xs text-[#0A2540] dark:text-white/90">{p.reference}</td>
                    <td className="px-4 py-3">
                      <p className="font-semibold text-[#0A2540] dark:text-white">{p.titre}</p>
                      {p.auteur && <p className="text-[11px] text-gray-500 dark:text-white/50">{p.auteur}</p>}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant="outline">{p.categorie || "—"}</Badge>
                    </td>
                    <td className="px-4 py-3 text-gray-700 dark:text-white/80">{p.fournisseur_nom || "—"}</td>
                    <td className="px-4 py-3 text-right font-semibold text-[#0A2540] dark:text-white">{p.stock_actuel || 0}</td>
                    {seePrixAchat && (
                      <td className="px-4 py-3 text-right text-gray-700 dark:text-white/70">
                        {p.prix_achat != null ? formatFCFA(p.prix_achat) : "—"}
                      </td>
                    )}
                    <td className="px-4 py-3 text-right font-semibold text-[#0A2540] dark:text-white">
                      {formatFCFA(p.prix_vente)}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-600 dark:text-white/60">{p.stock_minimum || 0}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-white/60">{p.depot || "—"}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-white/60">{formatDate(p.derniere_entree)}</td>
                    <td className="px-4 py-3 text-right">
                      {canWrite && (
                        <div className="inline-flex items-center gap-1">
                          <button className="p-1.5 rounded hover:bg-[#FF6200]/10 text-[#0A2540] dark:text-white/80" title="Modifier">
                            <Pencil className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {products.total > PAGE_SIZE && (
            <div className="border-t border-gray-100 dark:border-white/10 px-4 py-3 flex items-center justify-between text-xs text-gray-600 dark:text-white/60">
              <span>Page {page} / {totalPages} ({products.total} résultat{products.total > 1 ? "s" : ""})</span>
              <div className="flex gap-2">
                <Button disabled={page === 1} onClick={() => setPage((p) => Math.max(1, p - 1))} variant="outline" size="sm">
                  <ChevronLeft className="w-3 h-3" /> Préc.
                </Button>
                <Button disabled={page >= totalPages} onClick={() => setPage((p) => Math.min(totalPages, p + 1))} variant="outline" size="sm">
                  Suiv. <ChevronRight className="w-3 h-3" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </>
  );
}

// Tab: Inventaire
function InventaireTab({ products, loading }) {
  const stats = products.items.reduce(
    (acc, p) => {
      acc.total += p.stock_actuel || 0;
      acc.alerte += (p.stock_actuel || 0) < (p.stock_minimum || 0) ? 1 : 0;
      acc.rupture += (p.stock_actuel || 0) === 0 ? 1 : 0;
      return acc;
    },
    { total: 0, alerte: 0, rupture: 0 }
  );

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Stock total</CardDescription>
          <CardTitle className="text-2xl text-[#FF6200]">{stats.total}</CardTitle>
        </CardHeader>
        <CardContent><Warehouse className="h-4 w-4 text-[#FF6200]" /></CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Alertes stock</CardDescription>
          <CardTitle className="text-2xl text-yellow-600">{stats.alerte}</CardTitle>
        </CardHeader>
        <CardContent><AlertCircle className="h-4 w-4 text-yellow-500" /></CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Ruptures</CardDescription>
          <CardTitle className="text-2xl text-red-600">{stats.rupture}</CardTitle>
        </CardHeader>
        <CardContent><Package className="h-4 w-4 text-red-500" /></CardContent>
      </Card>
    </div>
  );
}

// Tab: Mouvements
function MouvementsTab() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5" /> Mouvements de stock
        </CardTitle>
        <CardDescription>Historique des entrées et sorties</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-center py-12 text-gray-500">
          <BarChart3 className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <p>Fonctionnalité en cours de développement</p>
        </div>
      </CardContent>
    </Card>
  );
}

// Tab: Approvisionnement
function ApprovisionnementTab({ fournisseurs, products, onRefresh, canWrite }) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    fournisseur_id: "",
    depot: "principal",
    lignes: [{ produit_id: "", quantite: "", prix_achat: "" }]
  });
  const [saving, setSaving] = useState(false);

  const addLigne = () => {
    setForm({
      ...form,
      lignes: [...form.lignes, { produit_id: "", quantite: "", prix_achat: "" }]
    });
  };

  const removeLigne = (index) => {
    setForm({
      ...form,
      lignes: form.lignes.filter((_, i) => i !== index)
    });
  };

  const updateLigne = (index, field, value) => {
    const newLignes = [...form.lignes];
    newLignes[index][field] = value;
    setForm({ ...form, lignes: newLignes });
  };

  const handleSubmit = async () => {
    if (!form.fournisseur_id || form.lignes.some(l => !l.produit_id || !l.quantite)) {
      toast.error("Veuillez remplir tous les champs obligatoires");
      return;
    }
    try {
      setSaving(true);
      await createApprovisionnement({
        fournisseur_id: form.fournisseur_id,
        depot: form.depot,
        lignes: form.lignes.map(l => ({
          produit_id: l.produit_id,
          quantite: parseInt(l.quantite),
          prix_achat: parseFloat(l.prix_achat)
        }))
      });
      toast.success("Approvisionnement enregistré avec succès");
      setForm({
        fournisseur_id: "",
        depot: "principal",
        lignes: [{ produit_id: "", quantite: "", prix_achat: "" }]
      });
      setOpen(false);
      onRefresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erreur lors de l'enregistrement");
    } finally {
      setSaving(false);
    }
  };

  if (!canWrite) {
    return (
      <Card>
        <CardContent className="p-12 text-center text-gray-500">
          <Truck className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <p>Accès refusé</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Truck className="w-5 h-5" /> Entrée d'approvisionnement
          </CardTitle>
          <CardDescription>Enregistrer une entrée de stock provenant d'un fournisseur</CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={() => setOpen(true)} className="bg-[#FF6200] hover:bg-[#E65800] text-white">
            <Plus className="w-4 h-4 mr-2" /> Nouvel approvisionnement
          </Button>
        </CardContent>
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Nouvel approvisionnement</DialogTitle>
            <DialogDescription>Enregistrer une entrée de stock provenant d'un fournisseur</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Fournisseur *</Label>
                <Select value={form.fournisseur_id} onValueChange={(v) => setForm({ ...form, fournisseur_id: v })}>
                  <SelectTrigger>
                    <SelectValue placeholder="Sélectionner..." />
                  </SelectTrigger>
                  <SelectContent>
                    {fournisseurs.map((f) => (
                      <SelectItem key={f.fournisseur_id} value={f.fournisseur_id}>
                        {f.nom}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Dépôt *</Label>
                <Select value={form.depot} onValueChange={(v) => setForm({ ...form, depot: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="principal">Dépôt principal</SelectItem>
                    <SelectItem value="secondaire">Dépôt secondaire</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label>Produits *</Label>
              <div className="space-y-2 mt-2">
                {form.lignes.map((ligne, index) => (
                  <div key={index} className="grid grid-cols-12 gap-2 items-end">
                    <div className="col-span-5">
                      <Label className="text-xs">Produit</Label>
                      <Select value={ligne.produit_id} onValueChange={(v) => updateLigne(index, "produit_id", v)}>
                        <SelectTrigger>
                          <SelectValue placeholder="Produit..." />
                        </SelectTrigger>
                        <SelectContent>
                          {products.items.map((p) => (
                            <SelectItem key={p.product_id} value={p.product_id}>
                              {p.reference} - {p.titre}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="col-span-2">
                      <Label className="text-xs">Quantité</Label>
                      <Input
                        type="number"
                        min="1"
                        value={ligne.quantite}
                        onChange={(e) => updateLigne(index, "quantite", e.target.value)}
                        placeholder="Qté"
                      />
                    </div>
                    <div className="col-span-3">
                      <Label className="text-xs">Prix achat</Label>
                      <Input
                        type="number"
                        min="0"
                        step="0.01"
                        value={ligne.prix_achat}
                        onChange={(e) => updateLigne(index, "prix_achat", e.target.value)}
                        placeholder="Prix"
                      />
                    </div>
                    <div className="col-span-2">
                      {form.lignes.length > 1 && (
                        <Button type="button" variant="destructive" size="sm" onClick={() => removeLigne(index)}>
                          Supprimer
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
                <Button type="button" variant="outline" size="sm" onClick={addLigne}>
                  <Plus className="w-4 h-4 mr-2" /> Ajouter une ligne
                </Button>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>Annuler</Button>
            <Button onClick={handleSubmit} disabled={saving} className="bg-[#FF6200] hover:bg-[#E65800]">
              {saving ? "Enregistrement..." : "Valider l'approvisionnement"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

// Tab: Fournisseurs
function FournisseursTab({ fournisseurs, onRefresh, canWrite }) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    nom: "",
    contact: "",
    telephone: "",
    email: "",
    adresse: ""
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    if (!form.nom) {
      toast.error("Le nom du fournisseur est obligatoire");
      return;
    }
    try {
      setSaving(true);
      await createFournisseur(form);
      toast.success("Fournisseur créé avec succès");
      setForm({ nom: "", contact: "", telephone: "", email: "", adresse: "" });
      setOpen(false);
      onRefresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erreur lors de la création");
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="w-5 h-5" /> Liste des fournisseurs (imprimeurs)
          </CardTitle>
          <CardDescription>{fournisseurs.length} fournisseur{fournisseurs.length > 1 ? "s" : ""}</CardDescription>
        </CardHeader>
        <CardContent>
          {canWrite && (
            <Button onClick={() => setOpen(true)} className="bg-[#FF6200] hover:bg-[#E65800] text-white mb-4">
              <Plus className="w-4 h-4 mr-2" /> Nouveau fournisseur
            </Button>
          )}
          {fournisseurs.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Building2 className="h-12 w-12 mx-auto text-gray-400 mb-4" />
              <p>Aucun fournisseur enregistré</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {fournisseurs.map((f) => (
                <Card key={f.fournisseur_id}>
                  <CardHeader>
                    <CardTitle className="text-lg">{f.nom}</CardTitle>
                    <CardDescription>{f.contact || "—"}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    <div className="flex items-center gap-2 text-gray-600">
                      <Phone className="w-4 h-4" /> {f.telephone || "—"}
                    </div>
                    <div className="flex items-center gap-2 text-gray-600">
                      <Mail className="w-4 h-4" /> {f.email || "—"}
                    </div>
                    <div className="flex items-start gap-2 text-gray-600">
                      <MapPin className="w-4 h-4 mt-0.5" /> {f.adresse || "—"}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Nouveau fournisseur</DialogTitle>
            <DialogDescription>Ajouter un nouvel imprimeur/fournisseur</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Nom de l'imprimeur *</Label>
              <Input
                value={form.nom}
                onChange={(e) => setForm({ ...form, nom: e.target.value })}
                placeholder="Ex: Imprimerie ABC"
              />
            </div>
            <div>
              <Label>Contact</Label>
              <Input
                value={form.contact}
                onChange={(e) => setForm({ ...form, contact: e.target.value })}
                placeholder="Nom du contact"
              />
            </div>
            <div>
              <Label>Téléphone</Label>
              <Input
                value={form.telephone}
                onChange={(e) => setForm({ ...form, telephone: e.target.value })}
                placeholder="+225 XX XX XX XX XX"
              />
            </div>
            <div>
              <Label>Email</Label>
              <Input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="contact@imprimerie.com"
              />
            </div>
            <div>
              <Label>Adresse</Label>
              <Textarea
                value={form.adresse}
                onChange={(e) => setForm({ ...form, adresse: e.target.value })}
                placeholder="Adresse complète"
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>Annuler</Button>
            <Button onClick={handleSubmit} disabled={saving} className="bg-[#FF6200] hover:bg-[#E65800]">
              {saving ? "Création..." : "Créer"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
