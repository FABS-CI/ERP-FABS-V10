/**
 * ProduitsInventaire.jsx — Module Logistique FABS v2
 * Onglets: Dashboard / Inventaire Global / Par Matière / Par Niveau / Par Cycle /
 *          Inventaire Physique / Dépôts / Alertes / Produits / Approvisionnement / Fournisseurs
 */
import { useEffect, useState, useCallback, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  Search, Plus, Pencil, Package, Filter, ArrowDown, ArrowUp,
  RefreshCw, Truck, Warehouse, ClipboardList, BarChart3, ChevronLeft, ChevronRight,
  AlertCircle, RotateCw, Building2, Phone, Mail, MapPin, TrendingDown, TrendingUp,
  BookOpen, Layers, Target, Activity, Bell, AlertTriangle, CheckCircle2,
  BookMarked, GraduationCap, Grid3X3, Boxes, MoveRight, Info, ArrowRightLeft,
  Calendar, User, FileText, Eye, Zap, Download, Printer
} from "lucide-react";
import { toast } from "sonner";

import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle
} from "../components/ui/dialog";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";

import { listProducts, disableProduct } from "../services/produitsApi";
import { listFournisseurs, createFournisseur } from "../services/fournisseursApi";
import { createApprovisionnement } from "../services/approvisionnementApi";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { formatFCFA } from "../utils/format";
import { useAuth } from "../hooks/useAuth";
import api from "../services/api";
import { downloadPdf, printPdf } from "../utils/pdfActions";

// ─────────────────────────────────────────
const WRITE_ROLES    = new Set(["super_admin", "directeur_general", "gestionnaire_stock", "responsable_magasinier"]);
const READ_LOG_ROLES = new Set(["super_admin", "directeur_general", "gestionnaire_stock", "responsable_magasinier", "service_logistique"]);
const FINANCIAL_ROLES = new Set(["super_admin", "directeur_general", "comptable"]);

const fmt = (s) => (s ? new Date(s).toLocaleDateString("fr-FR") : "—");
const shortNum = (n) => n >= 1e6 ? `${(n/1e6).toFixed(1)}M` : n >= 1e3 ? `${(n/1e3).toFixed(0)}k` : String(n ?? 0);

// ─────────────────────────────────────────
// Stat mini-card
function StatCard({ label, value, sub, icon: Icon, color = "#FF6200", bg = "#FFF4EE" }) {
  return (
    <Card className="overflow-hidden">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs text-gray-500 dark:text-white/50 uppercase tracking-wide font-medium">{label}</p>
            <p className="text-2xl font-bold mt-1" style={{ color }}>{value}</p>
            {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
          </div>
          <div className="p-2 rounded-lg" style={{ background: bg }}>
            {Icon && <Icon className="w-5 h-5" style={{ color }} />}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Barre de progression simple
function ProgressBar({ value, max, color = "#FF6200" }) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return (
    <div className="h-1.5 bg-gray-100 dark:bg-white/10 rounded-full overflow-hidden">
      <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: color }} />
    </div>
  );
}

// ─────────────────────────────────────────
// Hook: fetch logistique
function useLogistique() {
  const [dashboard, setDashboard] = useState(null);
  const [invGlobal,  setInvGlobal]  = useState(null);
  const [invMatiere, setInvMatiere] = useState(null);
  const [invNiveau,  setInvNiveau]  = useState(null);
  const [invCycle,   setInvCycle]   = useState(null);
  const [alertes,    setAlertes]    = useState(null);
  const [depots,     setDepots]     = useState(null);
  const [topVentes,  setTopVentes]  = useState(null);
  const [dormants,   setDormants]   = useState(null);
  const [loadingMap, setLoadingMap] = useState({});
  const [errMap,     setErrMap]     = useState({});

  const fetch_ = useCallback(async (key, path, setter) => {
    setLoadingMap(m => ({ ...m, [key]: true }));
    setErrMap(e => ({ ...e, [key]: null }));
    try {
      const r = await api.get(path);
      setter(r.data);
    } catch (e) {
      setErrMap(m => ({ ...m, [key]: e?.response?.data?.detail || "Erreur" }));
    } finally {
      setLoadingMap(m => ({ ...m, [key]: false }));
    }
  }, []);

  const refresh = useCallback((key) => {
    const map = {
      dashboard: ["/stock/dashboard-logistique", setDashboard],
      global:    ["/stock/inventaire-global", setInvGlobal],
      matiere:   ["/stock/inventaire-par-matiere", setInvMatiere],
      niveau:    ["/stock/inventaire-par-niveau", setInvNiveau],
      cycle:     ["/stock/inventaire-par-cycle", setInvCycle],
      alertes:   ["/stock/alertes-logistiques", setAlertes],
      depots:    ["/stock/depots", setDepots],
      top:       ["/stock/top-ventes?periode_jours=90&limit=15", setTopVentes],
      dormants:  ["/stock/produits-dormants?jours_inactivite=90", setDormants],
    };
    if (key && map[key]) {
      fetch_(key, map[key][0], map[key][1]);
    } else {
      Object.entries(map).forEach(([k, [path, setter]]) => fetch_(k, path, setter));
    }
  }, [fetch_]);

  useEffect(() => { refresh(); }, [refresh]);

  return {
    dashboard, invGlobal, invMatiere, invNiveau, invCycle,
    alertes, depots, topVentes, dormants,
    loadingMap, errMap, refresh
  };
}

// ─────────────────────────────────────────
// Page principale
export default function ProduitsInventaire() {
  const { role } = useAuth();
  const canWrite    = WRITE_ROLES.has(role);
  const canReadLog  = READ_LOG_ROLES.has(role);
  const seePrixAchat = FINANCIAL_ROLES.has(role);

  const [activeTab, setActiveTab] = useState("dashboard");
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 20;
  const dq = useDebouncedValue(q, 300);

  const [products, setProducts]     = useState({ items: [], total: 0 });
  const [fournisseurs, setFournisseurs] = useState([]);
  const [loadingProd, setLoadingProd] = useState(true);

  const log = useLogistique();

  const fetchProducts = useCallback(async () => {
    setLoadingProd(true);
    try {
      const r = await listProducts({ q: dq || undefined, page, page_size: PAGE_SIZE });
      setProducts(r);
    } catch { /* silent */ }
    finally { setLoadingProd(false); }
  }, [dq, page]);

  const fetchFournisseurs = useCallback(async () => {
    try {
      const r = await listFournisseurs({ limit: 100 });
      setFournisseurs(r.items || r || []);
    } catch { /* silent */ }
  }, []);

  useEffect(() => { fetchProducts(); fetchFournisseurs(); }, [fetchProducts, fetchFournisseurs]);
  useEffect(() => { setPage(1); }, [dq]);

  const totalPages = Math.max(1, Math.ceil(products.total / PAGE_SIZE));

  // Nombre d'alertes actives pour le badge
  const nbAlertes = (log.alertes?.resume?.nb_ruptures || 0) + (log.alertes?.resume?.nb_faibles || 0);

  const TABS = [
    { id: "dashboard",   label: "Dashboard",        icon: Activity },
    { id: "global",      label: "Global",           icon: Warehouse },
    { id: "matiere",     label: "Par matière",      icon: BookOpen },
    { id: "niveau",      label: "Par niveau",       icon: GraduationCap },
    { id: "cycle",       label: "Par cycle",        icon: Layers },
    { id: "physique",    label: "Inventaire phys.", icon: ClipboardList },
    { id: "depots",      label: "Dépôts",           icon: Boxes },
    { id: "alertes",     label: nbAlertes > 0 ? `Alertes (${nbAlertes})` : "Alertes", icon: Bell },
    { id: "stats",       label: "Statistiques",     icon: BarChart3 },
    { id: "produits",    label: "Produits",         icon: Package },
    { id: "appro",       label: "Appro.",           icon: Truck },
    { id: "fournisseurs",label: "Fournisseurs",     icon: Building2 },
  ];

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto space-y-5">
        {/* Header */}
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-[#FF6200] font-semibold">
              Module Logistique & Stock
            </p>
            <h1 className="text-2xl font-bold tracking-tight text-[#0A2540] dark:text-white mt-1">
              Gestion des Manuels Scolaires — Éditions FABS CI
            </h1>
            <p className="text-sm text-gray-500 dark:text-white/60 mt-1">
              {log.dashboard?.resume?.total_references ?? "—"} références ·{" "}
              {shortNum(log.dashboard?.resume?.total_quantite)} unités ·{" "}
              {formatFCFA(log.dashboard?.resume?.valeur_stock_fcfa ?? 0)} en stock
            </p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => log.refresh()} variant="outline" size="sm">
              <RefreshCw className="w-4 h-4 mr-1" /> Actualiser
            </Button>
            {canWrite && (
              <Button onClick={() => setActiveTab("appro")} className="bg-[#FF6200] hover:bg-[#E65800] text-white" size="sm">
                <Truck className="w-4 h-4 mr-1" /> Approvisionnement
              </Button>
            )}
          </div>
        </div>

        {/* Tabs scrollable */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <div className="overflow-x-auto pb-1">
            <TabsList className="inline-flex w-auto min-w-full gap-0.5 h-auto p-1 flex-nowrap">
              {TABS.map(({ id, label, icon: Icon }) => (
                <TabsTrigger
                  key={id}
                  value={id}
                  className="flex items-center gap-1.5 whitespace-nowrap text-xs px-3 py-2 data-[state=active]:bg-[#FF6200] data-[state=active]:text-white"
                >
                  <Icon className="w-3.5 h-3.5 flex-shrink-0" />
                  {label}
                </TabsTrigger>
              ))}
            </TabsList>
          </div>

          {/* ── DASHBOARD ── */}
          <TabsContent value="dashboard">
            <DashboardTab log={log} />
          </TabsContent>

          {/* ── INVENTAIRE GLOBAL ── */}
          <TabsContent value="global">
            <InventaireGlobalTab log={log} seePrixAchat={seePrixAchat} />
          </TabsContent>

          {/* ── PAR MATIÈRE ── */}
          <TabsContent value="matiere">
            <ParMatiereTab log={log} />
          </TabsContent>

          {/* ── PAR NIVEAU ── */}
          <TabsContent value="niveau">
            <ParNiveauTab log={log} seePrixAchat={seePrixAchat} />
          </TabsContent>

          {/* ── PAR CYCLE ── */}
          <TabsContent value="cycle">
            <ParCycleTab log={log} />
          </TabsContent>

          {/* ── INVENTAIRE PHYSIQUE ── */}
          <TabsContent value="physique">
            <InventairePhysiqueTab products={products} canWrite={canWrite} onRefresh={() => { fetchProducts(); log.refresh("dashboard"); }} />
          </TabsContent>

          {/* ── DÉPÔTS ── */}
          <TabsContent value="depots">
            <DepotsTab log={log} canWrite={canWrite} products={products} />
          </TabsContent>

          {/* ── ALERTES ── */}
          <TabsContent value="alertes">
            <AlertesTab log={log} />
          </TabsContent>

          {/* ── STATISTIQUES ── */}
          <TabsContent value="stats">
            <StatsTab log={log} seePrixAchat={seePrixAchat} />
          </TabsContent>

          {/* ── PRODUITS ── */}
          <TabsContent value="produits">
            <ProduitsTab
              products={products} loading={loadingProd}
              q={q} setQ={setQ}
              page={page} setPage={setPage} totalPages={totalPages}
              seePrixAchat={seePrixAchat} canWrite={canWrite}
              onRefresh={fetchProducts} pageSize={PAGE_SIZE}
            />
          </TabsContent>

          {/* ── APPROVISIONNEMENT ── */}
          <TabsContent value="appro">
            <ApprovisionnementTab fournisseurs={fournisseurs} products={products} onRefresh={fetchProducts} canWrite={canWrite} />
          </TabsContent>

          {/* ── FOURNISSEURS ── */}
          <TabsContent value="fournisseurs">
            <FournisseursTab fournisseurs={fournisseurs} onRefresh={fetchFournisseurs} canWrite={canWrite} />
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}

// ═══════════════════════════════════════════
// TAB: DASHBOARD
// ═══════════════════════════════════════════
function DashboardTab({ log }) {
  const d = log.dashboard;
  const loading = log.loadingMap.dashboard;

  if (loading) return <LoadingState />;
  if (!d) return <ErrorState msg={log.errMap.dashboard} onRetry={() => log.refresh("dashboard")} />;

  const r = d.resume;
  const a30 = d.activite_30j;

  return (
    <div className="space-y-6">
      {/* KPIs principaux */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard label="Références" value={r.total_references} sub="produits actifs" icon={Package} />
        <StatCard label="Stock total" value={shortNum(r.total_quantite)} sub="unités en dépôt" icon={Warehouse} color="#0A2540" bg="#EEF2F8" />
        <StatCard label="Valeur stock" value={formatFCFA(r.valeur_stock_fcfa)} sub="au prix d'achat" icon={TrendingUp} color="#16a34a" bg="#F0FDF4" />
        <StatCard label="Dépôts" value={r.nb_depots} sub="entrepôts actifs" icon={Boxes} color="#7C3AED" bg="#F5F3FF" />
      </div>

      {/* Alertes résumé */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard label="Ruptures" value={r.nb_ruptures} sub="stock = 0" icon={AlertTriangle} color="#DC2626" bg="#FEF2F2" />
        <StatCard label="Alertes faibles" value={r.nb_alertes_faibles} sub="sous seuil" icon={AlertCircle} color="#D97706" bg="#FFFBEB" />
        <StatCard label="Surstocks" value={r.nb_surstocks} sub="surcharge" icon={TrendingDown} color="#2563EB" bg="#EFF6FF" />
        <StatCard label="Inactifs (90j)" value={r.nb_inactifs} sub="sans mouvement" icon={Zap} color="#6B7280" bg="#F9FAFB" />
      </div>

      {/* Activité 30 jours */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#FF6200]" /> Activité des 30 derniers jours
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-6">
            <div className="text-center">
              <p className="text-3xl font-bold text-[#0A2540] dark:text-white">{a30.total_mouvements}</p>
              <p className="text-xs text-gray-500 dark:text-white/50 mt-1">Mouvements totaux</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-green-600">{a30.entrees}</p>
              <p className="text-xs text-gray-500 dark:text-white/50 mt-1">Entrées</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-[#FF6200]">{a30.sorties}</p>
              <p className="text-xs text-gray-500 dark:text-white/50 mt-1">Sorties</p>
            </div>
          </div>
          {a30.total_mouvements === 0 && (
            <p className="text-center text-xs text-gray-400 mt-4 border-t pt-3">Aucun mouvement enregistré ces 30 derniers jours.</p>
          )}
        </CardContent>
      </Card>

      {/* Inventaires en cours */}
      {r.inventaires_en_cours > 0 && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="p-4 flex items-center gap-3">
            <ClipboardList className="w-5 h-5 text-blue-600" />
            <p className="text-sm text-blue-800">
              <strong>{r.inventaires_en_cours}</strong> inventaire{r.inventaires_en_cours > 1 ? "s" : ""} physique en cours (brouillon)
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════
// TAB: INVENTAIRE GLOBAL
// ═══════════════════════════════════════════
function InventaireGlobalTab({ log, seePrixAchat }) {
  const d = log.invGlobal;
  const loading = log.loadingMap.global;
  const [exporting, setExporting] = useState(false);

  const exportPDF = async (categorie = null) => {
    setExporting(true);
    try {
      const params = categorie ? `?categorie=${encodeURIComponent(categorie)}` : "";
      const resp = await api.get(`/stock/export-etat-stock${params}`, { responseType: "blob" });
      const url = URL.createObjectURL(new Blob([resp.data], { type: "application/pdf" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = `etat_stock_${new Date().toISOString().slice(0,10)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      toast.error("Échec de l'export PDF");
    } finally {
      setExporting(false);
    }
  };

  const printStock = () => {
    window.print();
  };

  if (loading) return <LoadingState />;
  if (!d) return <ErrorState msg={log.errMap.global} onRetry={() => log.refresh("global")} />;

  const t = d.totaux;
  const cats = d.par_categorie || [];
  const maxQty = Math.max(...cats.map(c => c.quantite_totale), 1);

  return (
    <div className="space-y-5">
      {/* Boutons export */}
      <div className="flex items-center justify-end gap-2 flex-wrap print:hidden">
        <Button
          variant="outline"
          size="sm"
          onClick={printStock}
          className="text-gray-600 dark:text-white/70 border-gray-300 dark:border-white/10"
        >
          <Printer className="w-4 h-4 mr-1.5" />
          Imprimer
        </Button>
        <Button
          size="sm"
          onClick={() => exportPDF()}
          disabled={exporting}
          className="bg-[#FF6200] hover:bg-[#e55800] text-white"
        >
          <Download className="w-4 h-4 mr-1.5" />
          {exporting ? "Export en cours…" : "Exporter PDF"}
        </Button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard label="Références" value={t.nb_references} icon={Package} />
        <StatCard label="Quantité totale" value={shortNum(t.quantite_totale)} sub="exemplaires" icon={Warehouse} color="#0A2540" bg="#EEF2F8" />
        {seePrixAchat && (
          <StatCard label="Valeur achat" value={formatFCFA(t.valeur_achat_fcfa)} icon={TrendingUp} color="#16a34a" bg="#F0FDF4" />
        )}
        <StatCard label="Valeur vente" value={formatFCFA(t.valeur_vente_fcfa)} icon={Target} color="#7C3AED" bg="#F5F3FF" />
      </div>

      {seePrixAchat && t.marge_potentielle_fcfa > 0 && (
        <Card className="border-green-200 bg-green-50">
          <CardContent className="p-4 flex items-center gap-3">
            <TrendingUp className="w-5 h-5 text-green-600" />
            <p className="text-sm text-green-800">
              Marge potentielle si tout vendu : <strong>{formatFCFA(t.marge_potentielle_fcfa)}</strong>
            </p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-semibold">Répartition par catégorie</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {cats.map((cat) => (
              <div key={cat.categorie}>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="font-medium text-[#0A2540] dark:text-white">{cat.categorie}</span>
                  <div className="flex items-center gap-4 text-gray-500 dark:text-white/50 text-xs">
                    <span>{cat.nb_references} réf.</span>
                    <span className="font-semibold text-[#0A2540] dark:text-white">{cat.quantite_totale.toLocaleString()} ex.</span>
                    {seePrixAchat && <span>{formatFCFA(cat.valeur_fcfa)}</span>}
                  </div>
                </div>
                <ProgressBar value={cat.quantite_totale} max={maxQty} />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ═══════════════════════════════════════════
// TAB: PAR MATIÈRE
// ═══════════════════════════════════════════
function ParMatiereTab({ log }) {
  const d = log.invMatiere;
  const loading = log.loadingMap.matiere;
  const [expanded, setExpanded] = useState(null);

  if (loading) return <LoadingState />;
  if (!d) return <ErrorState msg={log.errMap.matiere} onRetry={() => log.refresh("matiere")} />;

  const matieres = d.par_matiere || [];
  const maxQty = Math.max(...matieres.map(m => m.quantite_totale), 1);

  const COLORS = ["#FF6200","#0A2540","#16a34a","#7C3AED","#D97706","#2563EB","#DC2626","#0891b2","#be185d"];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500 dark:text-white/50">{d.nb_matieres} matières identifiées dans le catalogue</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {matieres.map((m, i) => {
          const color = COLORS[i % COLORS.length];
          const isOpen = expanded === m.matiere;
          return (
            <Card key={m.matiere} className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setExpanded(isOpen ? null : m.matiere)}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ background: color }} />
                    <span className="font-semibold text-sm text-[#0A2540] dark:text-white">{m.matiere}</span>
                  </div>
                  <Badge variant="outline" className="text-xs">{m.nb_references} réf.</Badge>
                </div>
                <p className="text-2xl font-bold" style={{ color }}>{m.quantite_totale.toLocaleString()}</p>
                <p className="text-xs text-gray-500 dark:text-white/50 mt-0.5">exemplaires en stock</p>
                <ProgressBar value={m.quantite_totale} max={maxQty} color={color} />

                {isOpen && m.produits?.length > 0 && (
                  <div className="mt-3 pt-3 border-t space-y-1.5">
                    {m.produits.map(p => (
                      <div key={p.produit_id} className="flex items-center justify-between text-xs">
                        <span className="text-gray-600 dark:text-white/70 truncate max-w-[65%]">{p.titre}</span>
                        <span className="font-semibold text-[#0A2540] dark:text-white">{p.stock_actuel}</span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════
// TAB: PAR NIVEAU
// ═══════════════════════════════════════════
function ParNiveauTab({ log, seePrixAchat }) {
  const d = log.invNiveau;
  const loading = log.loadingMap.niveau;

  if (loading) return <LoadingState />;
  if (!d) return <ErrorState msg={log.errMap.niveau} onRetry={() => log.refresh("niveau")} />;

  const niveaux = d.par_niveau || [];
  const maxQty = Math.max(...niveaux.map(n => n.quantite_totale), 1);

  const catColor = {
    "Maternelle": "#be185d", "Primaire": "#16a34a",
    "Premier cycle": "#2563EB", "Second cycle": "#7C3AED", "Livre commun": "#D97706"
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 dark:bg-white dark:bg-[#0b1e30]/5 text-[10px] uppercase tracking-wider text-gray-500 dark:text-white/50">
                <th className="text-left px-4 py-3 font-semibold">Niveau</th>
                <th className="text-left px-4 py-3 font-semibold">Catégorie</th>
                <th className="text-right px-4 py-3 font-semibold">Références</th>
                <th className="text-right px-4 py-3 font-semibold">Quantité</th>
                {seePrixAchat && <th className="text-right px-4 py-3 font-semibold">Valeur</th>}
                <th className="px-4 py-3 font-semibold w-32">Proportion</th>
              </tr>
            </thead>
            <tbody>
              {niveaux.map((n) => {
                const color = catColor[n.categorie] || "#6B7280";
                return (
                  <tr key={n.niveau} className="border-t border-gray-100 dark:border-white/10 hover:bg-gray-50 dark:hover:bg-white dark:bg-[#0b1e30]/5">
                    <td className="px-4 py-3 font-semibold text-[#0A2540] dark:text-white">{n.niveau}</td>
                    <td className="px-4 py-3">
                      <Badge variant="outline" style={{ borderColor: color, color }}>{n.categorie}</Badge>
                    </td>
                    <td className="px-4 py-3 text-right text-gray-700 dark:text-white/80">{n.nb_references}</td>
                    <td className="px-4 py-3 text-right font-semibold text-[#0A2540] dark:text-white">{n.quantite_totale.toLocaleString()}</td>
                    {seePrixAchat && <td className="px-4 py-3 text-right text-gray-500 dark:text-white/50">{formatFCFA(n.valeur_fcfa)}</td>}
                    <td className="px-4 py-3">
                      <ProgressBar value={n.quantite_totale} max={maxQty} color={color} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}

// ═══════════════════════════════════════════
// TAB: PAR CYCLE
// ═══════════════════════════════════════════
function ParCycleTab({ log }) {
  const d = log.invCycle;
  const loading = log.loadingMap.cycle;

  if (loading) return <LoadingState />;
  if (!d) return <ErrorState msg={log.errMap.cycle} onRetry={() => log.refresh("cycle")} />;

  const cycles = d.par_cycle || [];
  const maxQty = Math.max(...cycles.map(c => c.quantite_totale), 1);
  const totalQty = cycles.reduce((s, c) => s + c.quantite_totale, 0);

  const CYCLE_CFG = {
    "Primaire":    { color: "#16a34a", icon: "🏫" },
    "Collège":     { color: "#2563EB", icon: "📚" },
    "Lycée":       { color: "#7C3AED", icon: "🎓" },
    "Tous cycles": { color: "#D97706", icon: "📖" },
  };

  return (
    <div className="space-y-5">
      {/* KPI cycles */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {cycles.map((c) => {
          const cfg = CYCLE_CFG[c.cycle] || { color: "#6B7280", icon: "📦" };
          const pct = totalQty > 0 ? ((c.quantite_totale / totalQty) * 100).toFixed(1) : 0;
          return (
            <Card key={c.cycle}>
              <CardContent className="p-4">
                <p className="text-2xl mb-1">{cfg.icon}</p>
                <p className="font-semibold text-sm text-[#0A2540] dark:text-white">{c.cycle}</p>
                <p className="text-2xl font-bold mt-1" style={{ color: cfg.color }}>{c.quantite_totale.toLocaleString()}</p>
                <p className="text-xs text-gray-400 mt-0.5">{pct}% du stock · {c.nb_references} réf.</p>
                <ProgressBar value={c.quantite_totale} max={maxQty} color={cfg.color} />
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Tableau détaillé */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-semibold">Détail par cycle</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[10px] uppercase tracking-wider text-gray-500 dark:text-white/50 border-b">
                <th className="text-left py-2 font-semibold">Cycle</th>
                <th className="text-left py-2 font-semibold">Catégories</th>
                <th className="text-right py-2 font-semibold">Références</th>
                <th className="text-right py-2 font-semibold">Quantité</th>
                <th className="text-right py-2 font-semibold">% stock</th>
              </tr>
            </thead>
            <tbody>
              {cycles.map((c) => {
                const cfg = CYCLE_CFG[c.cycle] || { color: "#6B7280" };
                const pct = totalQty > 0 ? ((c.quantite_totale / totalQty) * 100).toFixed(1) : 0;
                return (
                  <tr key={c.cycle} className="border-t border-gray-100 dark:border-white/10">
                    <td className="py-3 font-semibold" style={{ color: cfg.color }}>{c.cycle}</td>
                    <td className="py-3 text-xs text-gray-500 dark:text-white/50">{(c.categories || []).join(", ")}</td>
                    <td className="py-3 text-right">{c.nb_references}</td>
                    <td className="py-3 text-right font-semibold text-[#0A2540] dark:text-white">{c.quantite_totale.toLocaleString()}</td>
                    <td className="py-3 text-right text-gray-500 dark:text-white/50">{pct}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}

// ═══════════════════════════════════════════
// TAB: INVENTAIRE PHYSIQUE
// ═══════════════════════════════════════════
function InventairePhysiqueTab({ products, canWrite, onRefresh }) {
  const [inventaires, setInventaires] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [exporting, setExporting] = useState(false);

  const exportPDF = async () => {
    setExporting(true);
    try {
      const resp = await api.get("/stock/export-etat-stock", { responseType: "blob" });
      const url = URL.createObjectURL(new Blob([resp.data], { type: "application/pdf" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = `etat_stock_${new Date().toISOString().slice(0, 10)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Échec de l'export PDF");
    } finally {
      setExporting(false);
    }
  };

  const fetchInventaires = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.get("/stock/inventaire");
      setInventaires(r.data || []);
    } catch { /* silent */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchInventaires(); }, [fetchInventaires]);

  const handleRegulariser = async (inv) => {
    if (!window.confirm(`Régulariser l'inventaire ${inv.reference} ? Cette action mettra à jour tous les stocks.`)) return;
    try {
      await api.post(`/stock/inventaire/${inv.inventaire_id}/regulariser`);
      toast.success(`Inventaire ${inv.reference} régularisé`);
      fetchInventaires();
      onRefresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erreur de régularisation");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <p className="text-sm text-gray-500 dark:text-white/50">{inventaires.length} inventaire{inventaires.length > 1 ? "s" : ""} enregistré{inventaires.length > 1 ? "s" : ""}</p>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.print()}
            className="text-gray-600 dark:text-white/70 border-gray-300 dark:border-white/10 print:hidden"
          >
            <Printer className="w-4 h-4 mr-1.5" />
            Imprimer
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={exportPDF}
            disabled={exporting}
            className="text-[#FF6200] border-[#FF6200] hover:bg-[#FFF4EE] print:hidden"
          >
            <Download className="w-4 h-4 mr-1.5" />
            {exporting ? "Export…" : "PDF stocks"}
          </Button>
          {canWrite && (
            <Button onClick={() => setShowCreate(true)} className="bg-[#FF6200] hover:bg-[#E65800] text-white" size="sm">
              <Plus className="w-4 h-4 mr-1" /> Nouvel inventaire
            </Button>
          )}
        </div>
      </div>

      {loading ? <LoadingState /> : (
        <Card>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 dark:bg-white dark:bg-[#0b1e30]/5 text-[10px] uppercase tracking-wider text-gray-500 dark:text-white/50">
                  <th className="text-left px-4 py-3 font-semibold">Référence</th>
                  <th className="text-left px-4 py-3 font-semibold">Date</th>
                  <th className="text-left px-4 py-3 font-semibold">Type</th>
                  <th className="text-left px-4 py-3 font-semibold">Dépôt</th>
                  <th className="text-right px-4 py-3 font-semibold">Écart total</th>
                  <th className="text-left px-4 py-3 font-semibold">Statut</th>
                  <th className="text-right px-4 py-3 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {inventaires.length === 0 && (
                  <tr><td colSpan={7} className="px-4 py-10 text-center text-gray-400">Aucun inventaire physique enregistré.</td></tr>
                )}
                {inventaires.map((inv) => (
                  <tr key={inv.inventaire_id} className="border-t border-gray-100 dark:border-white/10 hover:bg-gray-50 dark:bg-white/5">
                    <td className="px-4 py-3 font-mono text-xs">{inv.reference}</td>
                    <td className="px-4 py-3">{fmt(inv.date_inventaire)}</td>
                    <td className="px-4 py-3">
                      <Badge variant="outline">{inv.type_inventaire || "complet"}</Badge>
                    </td>
                    <td className="px-4 py-3 text-gray-500 dark:text-white/50 text-xs">{inv.depot || "principal"}</td>
                    <td className="px-4 py-3 text-right font-semibold" style={{ color: inv.total_ecart < 0 ? "#DC2626" : inv.total_ecart > 0 ? "#16a34a" : "#6B7280" }}>
                      {inv.total_ecart > 0 ? "+" : ""}{inv.total_ecart}
                    </td>
                    <td className="px-4 py-3">
                      <Badge className={inv.statut === "regularise" ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"}>
                        {inv.statut === "regularise" ? "Régularisé" : "Brouillon"}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-right">
                      {inv.statut === "brouillon" && canWrite && (
                        <Button size="sm" variant="outline" onClick={() => handleRegulariser(inv)}>
                          <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Régulariser
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}

      {showCreate && (
        <CreerInventaireDialog
          products={products}
          onClose={() => setShowCreate(false)}
          onCreated={() => { fetchInventaires(); onRefresh(); }}
        />
      )}
    </div>
  );
}

// Dialog: Créer inventaire physique
function CreerInventaireDialog({ products, onClose, onCreated }) {
  const [type, setType] = useState("complet");
  const [depot, setDepot] = useState("principal");
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [responsable, setResponsable] = useState("");
  const [notes, setNotes] = useState("");
  const [lignes, setLignes] = useState([]);
  const [saving, setSaving] = useState(false);

  // Pour inventaire complet : pré-remplir toutes les lignes avec stock théorique
  useEffect(() => {
    if (type === "complet" && products.items?.length > 0) {
      setLignes(products.items.map(p => ({
        produit_id: p.product_id || p.produit_id,
        titre: p.titre,
        stock_theorique: p.stock_actuel || 0,
        quantite_comptee: p.stock_actuel || 0,
      })));
    } else if (type !== "complet") {
      setLignes([]);
    }
  }, [type, products.items]);

  const updateLigne = (produit_id, qty) => {
    setLignes(prev => prev.map(l => l.produit_id === produit_id ? { ...l, quantite_comptee: parseInt(qty) || 0 } : l));
  };

  const handleSubmit = async () => {
    if (lignes.length === 0) { toast.error("Aucune ligne à inventorier"); return; }
    setSaving(true);
    try {
      await api.post("/stock/inventaire", {
        date_inventaire: date,
        type_inventaire: type,
        depot,
        responsable: responsable || null,
        notes: notes || null,
        lignes: lignes.map(l => ({ produit_id: l.produit_id, quantite_comptee: l.quantite_comptee })),
      });
      toast.success("Inventaire créé avec succès");
      onCreated();
      onClose();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erreur de création");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Nouvel inventaire physique</DialogTitle>
          <DialogDescription>Créer une session d'inventaire pour constater les écarts de stock.</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Type d'inventaire</Label>
              <Select value={type} onValueChange={setType}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="complet">Complet (tous produits)</SelectItem>
                  <SelectItem value="partiel">Partiel (sélection)</SelectItem>
                  <SelectItem value="tournant">Tournant (par dépôt)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Date d'inventaire</Label>
              <Input type="date" value={date} onChange={e => setDate(e.target.value)} />
            </div>
            <div>
              <Label>Dépôt</Label>
              <Select value={depot} onValueChange={setDepot}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="principal">Dépôt Principal</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Responsable</Label>
              <Input placeholder="Nom du responsable" value={responsable} onChange={e => setResponsable(e.target.value)} />
            </div>
          </div>
          <div>
            <Label>Notes</Label>
            <Textarea placeholder="Observations…" value={notes} onChange={e => setNotes(e.target.value)} rows={2} />
          </div>

          {type === "complet" && lignes.length > 0 && (
            <div>
              <Label className="mb-2 block">Quantités comptées ({lignes.length} articles)</Label>
              <div className="max-h-64 overflow-y-auto border rounded-lg">
                <table className="w-full text-xs">
                  <thead className="bg-gray-50 dark:bg-white/5 sticky top-0">
                    <tr>
                      <th className="text-left px-3 py-2 font-semibold">Produit</th>
                      <th className="text-right px-3 py-2 font-semibold">Théorique</th>
                      <th className="text-right px-3 py-2 font-semibold">Compté</th>
                    </tr>
                  </thead>
                  <tbody>
                    {lignes.map(l => (
                      <tr key={l.produit_id} className="border-t">
                        <td className="px-3 py-1.5 max-w-[200px] truncate">{l.titre}</td>
                        <td className="px-3 py-1.5 text-right text-gray-500 dark:text-white/50">{l.stock_theorique}</td>
                        <td className="px-3 py-1.5 text-right">
                          <input
                            type="number" min={0}
                            value={l.quantite_comptee}
                            onChange={e => updateLigne(l.produit_id, e.target.value)}
                            className="w-16 text-right border rounded px-1.5 py-0.5 text-xs"
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {type !== "complet" && (
            <div className="p-4 bg-blue-50 rounded-lg text-sm text-blue-700">
              <Info className="w-4 h-4 inline mr-1" />
              Pour un inventaire {type === "partiel" ? "partiel" : "tournant"}, les lignes peuvent être ajoutées manuellement après création.
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Annuler</Button>
          <Button onClick={handleSubmit} disabled={saving} className="bg-[#FF6200] hover:bg-[#E65800] text-white">
            {saving ? "Création…" : "Créer l'inventaire"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ═══════════════════════════════════════════
// TAB: DÉPÔTS
// ═══════════════════════════════════════════
function DepotsTab({ log, canWrite }) {
  const d = log.depots;
  const loading = log.loadingMap.depots;
  const [showCreate, setShowCreate] = useState(false);
  const [showTransfert, setShowTransfert] = useState(false);

  if (loading) return <LoadingState />;
  if (!d) return <ErrorState msg={log.errMap.depots} onRetry={() => log.refresh("depots")} />;

  const depots = d.depots || [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500 dark:text-white/50">{d.nb_depots} dépôt{d.nb_depots > 1 ? "s" : ""} actif{d.nb_depots > 1 ? "s" : ""}</p>
        {canWrite && (
          <div className="flex gap-2">
            <Button onClick={() => setShowTransfert(true)} variant="outline" size="sm">
              <ArrowRightLeft className="w-4 h-4 mr-1" /> Transfert
            </Button>
            <Button onClick={() => setShowCreate(true)} className="bg-[#FF6200] hover:bg-[#E65800] text-white" size="sm">
              <Plus className="w-4 h-4 mr-1" /> Nouveau dépôt
            </Button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {depots.map((depot) => (
          <Card key={depot.depot_id || depot.code}>
            <CardContent className="p-5">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <p className="font-semibold text-[#0A2540] dark:text-white">{depot.nom}</p>
                  <p className="text-xs font-mono text-gray-400 mt-0.5">{depot.code}</p>
                </div>
                <Badge variant="outline" className="text-xs">
                  {depot.code === "PRINCIPAL" ? "Principal" : "Secondaire"}
                </Badge>
              </div>
              {depot.adresse && (
                <p className="text-xs text-gray-500 dark:text-white/50 flex items-center gap-1 mb-2">
                  <MapPin className="w-3 h-3" /> {depot.adresse}
                </p>
              )}
              {depot.responsable && (
                <p className="text-xs text-gray-500 dark:text-white/50 flex items-center gap-1 mb-3">
                  <User className="w-3 h-3" /> {depot.responsable}
                </p>
              )}
              <div className="grid grid-cols-3 gap-2 pt-3 border-t text-center">
                <div>
                  <p className="text-lg font-bold text-[#0A2540] dark:text-white">{depot.nb_references ?? "—"}</p>
                  <p className="text-[10px] text-gray-400">Références</p>
                </div>
                <div>
                  <p className="text-lg font-bold text-[#FF6200]">{(depot.quantite_totale ?? 0).toLocaleString()}</p>
                  <p className="text-[10px] text-gray-400">Unités</p>
                </div>
                <div>
                  <p className="text-xs font-bold text-green-600">{formatFCFA(depot.valeur_fcfa ?? 0)}</p>
                  <p className="text-[10px] text-gray-400">Valeur</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {showCreate && (
        <CreerDepotDialog onClose={() => setShowCreate(false)} onCreated={() => { log.refresh("depots"); setShowCreate(false); }} />
      )}
      {showTransfert && (
        <TransfertDialog depots={depots} onClose={() => setShowTransfert(false)} />
      )}
    </div>
  );
}

function CreerDepotDialog({ onClose, onCreated }) {
  const [form, setForm] = useState({ nom: "", code: "", adresse: "", responsable: "", description: "" });
  const [saving, setSaving] = useState(false);
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const handleSubmit = async () => {
    if (!form.nom || !form.code) { toast.error("Nom et code requis"); return; }
    setSaving(true);
    try {
      await api.post("/stock/depots", form);
      toast.success(`Dépôt ${form.nom} créé`);
      onCreated();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erreur de création");
    } finally { setSaving(false); }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Nouveau dépôt</DialogTitle>
          <DialogDescription>Créer un nouvel entrepôt / dépôt de stockage.</DialogDescription>
        </DialogHeader>
        <div className="space-y-3 py-2">
          <div className="grid grid-cols-2 gap-3">
            <div><Label>Nom *</Label><Input value={form.nom} onChange={e => set("nom", e.target.value)} placeholder="Dépôt Nord" /></div>
            <div><Label>Code *</Label><Input value={form.code} onChange={e => set("code", e.target.value.toUpperCase())} placeholder="NORD" /></div>
          </div>
          <div><Label>Adresse</Label><Input value={form.adresse} onChange={e => set("adresse", e.target.value)} placeholder="Adresse…" /></div>
          <div><Label>Responsable</Label><Input value={form.responsable} onChange={e => set("responsable", e.target.value)} placeholder="Nom du responsable" /></div>
          <div><Label>Description</Label><Textarea value={form.description} onChange={e => set("description", e.target.value)} rows={2} /></div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Annuler</Button>
          <Button onClick={handleSubmit} disabled={saving} className="bg-[#FF6200] hover:bg-[#E65800] text-white">
            {saving ? "Création…" : "Créer"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function TransfertDialog({ depots, onClose }) {
  const [form, setForm] = useState({ produit_id: "", depot_source: "", depot_destination: "", quantite: 1, motif: "" });
  const [produits, setProduits] = useState([]);
  const [saving, setSaving] = useState(false);
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  useEffect(() => {
    api.get("/produits?page=1&page_size=100").then(r => setProduits(r.data?.items || [])).catch(() => {});
  }, []);

  const handleSubmit = async () => {
    if (!form.produit_id || !form.depot_source || !form.depot_destination) { toast.error("Remplir tous les champs"); return; }
    setSaving(true);
    try {
      await api.post("/stock/depots/transfert", { ...form, quantite: Number(form.quantite) });
      toast.success("Transfert enregistré");
      onClose();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erreur de transfert");
    } finally { setSaving(false); }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Transfert entre dépôts</DialogTitle>
        </DialogHeader>
        <div className="space-y-3 py-2">
          <div>
            <Label>Produit</Label>
            <Select value={form.produit_id} onValueChange={v => set("produit_id", v)}>
              <SelectTrigger><SelectValue placeholder="Sélectionner un produit" /></SelectTrigger>
              <SelectContent>
                {produits.map(p => <SelectItem key={p.product_id || p.produit_id} value={p.product_id || p.produit_id}>{p.titre}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Dépôt source</Label>
              <Select value={form.depot_source} onValueChange={v => set("depot_source", v)}>
                <SelectTrigger><SelectValue placeholder="Source" /></SelectTrigger>
                <SelectContent>
                  {depots.map(d => <SelectItem key={d.code} value={d.code}>{d.nom}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Dépôt destination</Label>
              <Select value={form.depot_destination} onValueChange={v => set("depot_destination", v)}>
                <SelectTrigger><SelectValue placeholder="Destination" /></SelectTrigger>
                <SelectContent>
                  {depots.map(d => <SelectItem key={d.code} value={d.code}>{d.nom}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div><Label>Quantité</Label><Input type="number" min={1} value={form.quantite} onChange={e => set("quantite", e.target.value)} /></div>
          <div><Label>Motif</Label><Input value={form.motif} onChange={e => set("motif", e.target.value)} placeholder="Motif du transfert…" /></div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Annuler</Button>
          <Button onClick={handleSubmit} disabled={saving} className="bg-[#FF6200] hover:bg-[#E65800] text-white">
            {saving ? "En cours…" : "Transférer"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ═══════════════════════════════════════════
// TAB: ALERTES LOGISTIQUES
// ═══════════════════════════════════════════
function AlertesTab({ log }) {
  const d = log.alertes;
  const loading = log.loadingMap.alertes;
  const [section, setSection] = useState("ruptures");

  if (loading) return <LoadingState />;
  if (!d) return <ErrorState msg={log.errMap.alertes} onRetry={() => log.refresh("alertes")} />;

  const r = d.resume;
  const SECTIONS = [
    { id: "ruptures", label: "Ruptures", count: r.nb_ruptures, color: "#DC2626", data: d.ruptures },
    { id: "faibles",  label: "Stock faible", count: r.nb_faibles, color: "#D97706", data: d.faibles },
    { id: "surstocks",label: "Surstock", count: r.nb_surstocks, color: "#2563EB", data: d.surstocks },
    { id: "inactifs", label: "Inactifs 90j", count: r.nb_inactifs, color: "#6B7280", data: d.inactifs },
  ];

  const current = SECTIONS.find(s => s.id === section);

  return (
    <div className="space-y-5">
      {/* Résumé */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {SECTIONS.map(s => (
          <button key={s.id} onClick={() => setSection(s.id)}
            className={`text-left p-4 rounded-xl border-2 transition-all ${section === s.id ? "border-current shadow-md" : "border-gray-200 dark:border-white/10 hover:border-gray-300 dark:border-white/10"}`}
            style={section === s.id ? { borderColor: s.color } : {}}>
            <p className="text-2xl font-bold" style={{ color: s.color }}>{s.count}</p>
            <p className="text-xs text-gray-500 dark:text-white/50 mt-0.5">{s.label}</p>
          </button>
        ))}
      </div>

      {/* Liste alertes */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-semibold flex items-center gap-2" style={{ color: current.color }}>
            <AlertTriangle className="w-4 h-4" /> {current.label} — {current.count} produit{current.count > 1 ? "s" : ""}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {current.data?.length === 0 ? (
            <div className="p-8 text-center text-green-600 font-medium">
              <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-green-500" />
              Aucune alerte dans cette catégorie
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 dark:bg-white dark:bg-[#0b1e30]/5 text-[10px] uppercase tracking-wider text-gray-500 dark:text-white/50">
                  <th className="text-left px-4 py-3 font-semibold">Produit</th>
                  <th className="text-left px-4 py-3 font-semibold">Catégorie</th>
                  <th className="text-right px-4 py-3 font-semibold">Stock</th>
                  <th className="text-right px-4 py-3 font-semibold">Seuil</th>
                  <th className="text-left px-4 py-3 font-semibold">Message</th>
                </tr>
              </thead>
              <tbody>
                {current.data.map((a) => (
                  <tr key={a.produit_id} className="border-t border-gray-100 dark:border-white/10 hover:bg-gray-50 dark:bg-white/5">
                    <td className="px-4 py-3">
                      <p className="font-medium text-[#0A2540] dark:text-white text-xs leading-tight">{a.titre}</p>
                      <p className="text-[10px] text-gray-400">{a.niveau_scolaire}</p>
                    </td>
                    <td className="px-4 py-3"><Badge variant="outline" className="text-[10px]">{a.categorie}</Badge></td>
                    <td className="px-4 py-3 text-right font-bold" style={{ color: current.color }}>{a.stock_actuel}</td>
                    <td className="px-4 py-3 text-right text-gray-400">{a.seuil_alerte ?? "—"}</td>
                    <td className="px-4 py-3 text-xs text-gray-500 dark:text-white/50">{a.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ═══════════════════════════════════════════
// TAB: STATISTIQUES ÉDITORIALES
// ═══════════════════════════════════════════
function StatsTab({ log, seePrixAchat }) {
  const topVentes = log.topVentes;
  const dormants  = log.dormants;
  const loadTop   = log.loadingMap.top;
  const loadDorm  = log.loadingMap.dormants;

  return (
    <div className="space-y-6">
      {/* Top ventes */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-green-600" /> Top 15 ventes — 90 derniers jours
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loadTop ? <div className="p-8 text-center text-gray-400">Chargement…</div> : (
            topVentes?.top_ventes?.length > 0 ? (
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-white/5 text-[10px] uppercase tracking-wider text-gray-500 dark:text-white/50">
                    <th className="text-left px-4 py-3">#</th>
                    <th className="text-left px-4 py-3">Produit</th>
                    <th className="text-left px-4 py-3">Matière</th>
                    <th className="text-right px-4 py-3">Qté sortie</th>
                    <th className="text-right px-4 py-3">Stock actuel</th>
                    {seePrixAchat && <th className="text-right px-4 py-3">CA potentiel</th>}
                  </tr>
                </thead>
                <tbody>
                  {topVentes.top_ventes.map((p, i) => (
                    <tr key={p.produit_id} className="border-t border-gray-100 dark:border-white/10 hover:bg-gray-50 dark:bg-white/5">
                      <td className="px-4 py-3 text-gray-400 font-bold">{i + 1}</td>
                      <td className="px-4 py-3">
                        <p className="font-medium text-[#0A2540] dark:text-white text-xs">{p.titre}</p>
                        <p className="text-[10px] text-gray-400">{p.niveau_scolaire}</p>
                      </td>
                      <td className="px-4 py-3"><Badge variant="outline" className="text-[10px]">{p.matiere}</Badge></td>
                      <td className="px-4 py-3 text-right font-bold text-green-600">{p.quantite_sortie}</td>
                      <td className="px-4 py-3 text-right text-gray-700 dark:text-white/90">{p.stock_actuel}</td>
                      {seePrixAchat && <td className="px-4 py-3 text-right text-gray-500 dark:text-white/50">{formatFCFA(p.chiffre_affaires_potentiel)}</td>}
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-8 text-center text-gray-400">Aucune sortie enregistrée sur 90 jours.</div>
            )
          )}
        </CardContent>
      </Card>

      {/* Produits dormants */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <TrendingDown className="w-4 h-4 text-gray-500 dark:text-white/50" /> Produits dormants — {dormants?.nb_dormants ?? "—"} références sans mouvement (90j)
          </CardTitle>
          {dormants?.valeur_totale_immobilisee > 0 && (
            <CardDescription className="text-[#DC2626] font-semibold">
              Valeur immobilisée : {formatFCFA(dormants.valeur_totale_immobilisee)}
            </CardDescription>
          )}
        </CardHeader>
        <CardContent className="p-0">
          {loadDorm ? <div className="p-8 text-center text-gray-400">Chargement…</div> : (
            dormants?.produits_dormants?.length > 0 ? (
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-white/5 text-[10px] uppercase tracking-wider text-gray-500 dark:text-white/50">
                    <th className="text-left px-4 py-3">Produit</th>
                    <th className="text-left px-4 py-3">Matière</th>
                    <th className="text-right px-4 py-3">Stock</th>
                    {seePrixAchat && <th className="text-right px-4 py-3">Valeur immobilisée</th>}
                  </tr>
                </thead>
                <tbody>
                  {dormants.produits_dormants.map(p => (
                    <tr key={p.produit_id} className="border-t border-gray-100 dark:border-white/10 hover:bg-gray-50 dark:bg-white/5">
                      <td className="px-4 py-3">
                        <p className="font-medium text-[#0A2540] dark:text-white text-xs">{p.titre}</p>
                        <p className="text-[10px] text-gray-400">{p.niveau_scolaire}</p>
                      </td>
                      <td className="px-4 py-3"><Badge variant="outline" className="text-[10px]">{p.matiere}</Badge></td>
                      <td className="px-4 py-3 text-right text-gray-700 dark:text-white/90">{p.stock_actuel}</td>
                      {seePrixAchat && <td className="px-4 py-3 text-right text-[#DC2626] font-semibold">{formatFCFA(p.valeur_immobilisee_fcfa)}</td>}
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-8 text-center text-green-600">
                <CheckCircle2 className="w-8 h-8 mx-auto mb-2" />
                Tous les produits ont eu des mouvements récents.
              </div>
            )
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ═══════════════════════════════════════════
// TAB: LISTE PRODUITS (repris et amélioré)
// ═══════════════════════════════════════════
function ProduitsTab({ products, loading, q, setQ, page, setPage, totalPages, seePrixAchat, canWrite, onRefresh, pageSize }) {
  const PAGE_SIZE = pageSize || 20;
  const [pdfLoading, setPdfLoading] = useState(false);

  const handleDownload = async () => {
    setPdfLoading(true);
    await downloadPdf("/stock/export-etat-stock?filtre=produits", `catalogue_produits_fabs_${new Date().toISOString().slice(0,10)}.pdf`);
    setPdfLoading(false);
  };

  const handlePrint = async () => {
    setPdfLoading(true);
    await printPdf("/stock/export-etat-stock?filtre=produits");
    setPdfLoading(false);
  };

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Search className="w-4 h-4" /> Recherche
            </CardTitle>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={handlePrint} disabled={pdfLoading}>
                <Printer className="w-3.5 h-3.5 mr-1.5" /> Imprimer
              </Button>
              <Button size="sm" onClick={handleDownload} disabled={pdfLoading}
                className="bg-[#FF6200] hover:bg-[#e05500] text-white">
                <Download className="w-3.5 h-3.5 mr-1.5" /> Télécharger PDF
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Titre, référence, niveau scolaire…"
            className="max-w-sm"
          />
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 dark:bg-white dark:bg-[#0b1e30]/5 text-[10px] uppercase tracking-wider text-gray-500 dark:text-white/50">
                  <th className="text-left px-4 py-3">Réf.</th>
                  <th className="text-left px-4 py-3">Titre</th>
                  <th className="text-left px-4 py-3">Catégorie</th>
                  <th className="text-left px-4 py-3">Niveau</th>
                  <th className="text-right px-4 py-3">Stock</th>
                  {seePrixAchat && <th className="text-right px-4 py-3">Prix achat</th>}
                  <th className="text-right px-4 py-3">Prix vente</th>
                  <th className="text-right px-4 py-3">Seuil</th>
                  <th className="text-right px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading && (
                  <tr><td colSpan={seePrixAchat ? 9 : 8} className="px-4 py-10 text-center text-gray-400">Chargement…</td></tr>
                )}
                {!loading && products.items.length === 0 && (
                  <tr><td colSpan={seePrixAchat ? 9 : 8} className="px-4 py-10 text-center text-gray-400">Aucun produit trouvé.</td></tr>
                )}
                {!loading && products.items.map((p) => {
                  const stockOk = (p.stock_actuel || 0) > (p.stock_minimum || p.seuil_alerte || 20);
                  const stockBas = !stockOk && (p.stock_actuel || 0) > 0;
                  return (
                    <tr key={p.product_id || p.produit_id} className="border-t border-gray-100 dark:border-white/10 hover:bg-gray-50 dark:hover:bg-white dark:bg-[#0b1e30]/5">
                      <td className="px-4 py-3 font-mono text-xs text-gray-500 dark:text-white/50">{p.reference || "—"}</td>
                      <td className="px-4 py-3">
                        <p className="font-semibold text-[#0A2540] dark:text-white text-xs leading-snug">{p.titre}</p>
                      </td>
                      <td className="px-4 py-3"><Badge variant="outline" className="text-[10px]">{p.categorie || "—"}</Badge></td>
                      <td className="px-4 py-3 text-xs text-gray-500 dark:text-white/50">{p.niveau_scolaire || "—"}</td>
                      <td className="px-4 py-3 text-right">
                        <span className={`font-bold text-sm ${stockBas ? "text-orange-500" : (p.stock_actuel || 0) === 0 ? "text-red-600" : "text-[#0A2540] dark:text-white"}`}>
                          {p.stock_actuel || 0}
                        </span>
                      </td>
                      {seePrixAchat && (
                        <td className="px-4 py-3 text-right text-gray-500 dark:text-white/50 text-xs">
                          {p.prix_achat != null ? formatFCFA(p.prix_achat) : "—"}
                        </td>
                      )}
                      <td className="px-4 py-3 text-right font-semibold text-xs text-[#0A2540] dark:text-white">
                        {formatFCFA(p.prix_vente)}
                      </td>
                      <td className="px-4 py-3 text-right text-xs text-gray-400">
                        {p.stock_minimum || p.seuil_alerte || 20}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {canWrite && (
                          <button className="p-1.5 rounded hover:bg-[#FF6200]/10 text-[#0A2540] dark:text-white/80" title="Modifier">
                            <Pencil className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {products.total > PAGE_SIZE && (
            <div className="border-t border-gray-100 dark:border-white/10 px-4 py-3 flex items-center justify-between text-xs text-gray-500 dark:text-white/50">
              <span>Page {page}/{totalPages} — {products.total} produit{products.total > 1 ? "s" : ""}</span>
              <div className="flex gap-2">
                <Button disabled={page === 1} onClick={() => setPage(p => Math.max(1, p - 1))} variant="outline" size="sm">
                  <ChevronLeft className="w-3 h-3" /> Préc.
                </Button>
                <Button disabled={page >= totalPages} onClick={() => setPage(p => Math.min(totalPages, p + 1))} variant="outline" size="sm">
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

// ═══════════════════════════════════════════
// TAB: APPROVISIONNEMENT (préservé)
// ═══════════════════════════════════════════
function ApprovisionnementTab({ fournisseurs, products, onRefresh, canWrite }) {
  const [form, setForm] = useState({
    fournisseur_id: "", produit_id: "", quantite: 1,
    prix_unitaire: "", date_livraison: "", notes: ""
  });
  const [saving, setSaving] = useState(false);
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.fournisseur_id || !form.produit_id || !form.quantite) {
      toast.error("Fournisseur, produit et quantité sont requis");
      return;
    }
    setSaving(true);
    try {
      await createApprovisionnement({
        ...form,
        quantite: parseInt(form.quantite),
        prix_unitaire: form.prix_unitaire ? parseFloat(form.prix_unitaire) : undefined,
      });
      toast.success("Approvisionnement enregistré");
      setForm({ fournisseur_id: "", produit_id: "", quantite: 1, prix_unitaire: "", date_livraison: "", notes: "" });
      onRefresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erreur d'enregistrement");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2"><Truck className="w-5 h-5 text-[#FF6200]" /> Enregistrer un approvisionnement</CardTitle>
        <CardDescription>Saisir une entrée de stock depuis un fournisseur.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label>Fournisseur *</Label>
            <Select value={form.fournisseur_id} onValueChange={v => set("fournisseur_id", v)}>
              <SelectTrigger><SelectValue placeholder="Sélectionner un fournisseur" /></SelectTrigger>
              <SelectContent>
                {fournisseurs.map(f => <SelectItem key={f.fournisseur_id} value={f.fournisseur_id}>{f.nom}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Produit *</Label>
            <Select value={form.produit_id} onValueChange={v => set("produit_id", v)}>
              <SelectTrigger><SelectValue placeholder="Sélectionner un produit" /></SelectTrigger>
              <SelectContent>
                {(products.items || []).map(p => (
                  <SelectItem key={p.product_id || p.produit_id} value={p.product_id || p.produit_id}>
                    {p.titre} (stock: {p.stock_actuel || 0})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><Label>Quantité *</Label><Input type="number" min={1} value={form.quantite} onChange={e => set("quantite", e.target.value)} /></div>
            <div><Label>Prix unitaire (FCFA)</Label><Input type="number" min={0} value={form.prix_unitaire} onChange={e => set("prix_unitaire", e.target.value)} placeholder="Optionnel" /></div>
          </div>
          <div><Label>Date de livraison prévue</Label><Input type="date" value={form.date_livraison} onChange={e => set("date_livraison", e.target.value)} /></div>
          <div><Label>Notes</Label><Textarea value={form.notes} onChange={e => set("notes", e.target.value)} rows={2} placeholder="Observations…" /></div>
          <Button type="submit" disabled={saving || !canWrite} className="bg-[#FF6200] hover:bg-[#E65800] text-white w-full">
            {saving ? "Enregistrement…" : "Enregistrer l'approvisionnement"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

// ═══════════════════════════════════════════
// TAB: FOURNISSEURS (préservé)
// ═══════════════════════════════════════════
function FournisseursTab({ fournisseurs, onRefresh, canWrite }) {
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ nom: "", email: "", telephone: "", adresse: "", notes: "" });
  const [saving, setSaving] = useState(false);
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const handleCreate = async () => {
    if (!form.nom) { toast.error("Le nom est requis"); return; }
    setSaving(true);
    try {
      await createFournisseur(form);
      toast.success(`Fournisseur ${form.nom} créé`);
      setShowCreate(false);
      setForm({ nom: "", email: "", telephone: "", adresse: "", notes: "" });
      onRefresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erreur de création");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500 dark:text-white/50">{fournisseurs.length} fournisseur{fournisseurs.length > 1 ? "s" : ""}</p>
        {canWrite && (
          <Button onClick={() => setShowCreate(true)} className="bg-[#FF6200] hover:bg-[#E65800] text-white" size="sm">
            <Plus className="w-4 h-4 mr-1" /> Nouveau fournisseur
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {fournisseurs.length === 0 && (
          <p className="col-span-3 text-center text-gray-400 py-8">Aucun fournisseur enregistré.</p>
        )}
        {fournisseurs.map((f) => (
          <Card key={f.fournisseur_id}>
            <CardContent className="p-4">
              <p className="font-semibold text-[#0A2540] dark:text-white">{f.nom}</p>
              {f.email && <p className="text-xs text-gray-500 dark:text-white/50 flex items-center gap-1 mt-1"><Mail className="w-3 h-3" />{f.email}</p>}
              {f.telephone && <p className="text-xs text-gray-500 dark:text-white/50 flex items-center gap-1"><Phone className="w-3 h-3" />{f.telephone}</p>}
              {f.adresse && <p className="text-xs text-gray-500 dark:text-white/50 flex items-center gap-1"><MapPin className="w-3 h-3" />{f.adresse}</p>}
              {f.notes && <p className="text-xs text-gray-400 mt-2 border-t pt-2">{f.notes}</p>}
            </CardContent>
          </Card>
        ))}
      </div>

      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Nouveau fournisseur</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div><Label>Nom *</Label><Input value={form.nom} onChange={e => set("nom", e.target.value)} placeholder="Nom de la société" /></div>
            <div><Label>Email</Label><Input type="email" value={form.email} onChange={e => set("email", e.target.value)} /></div>
            <div><Label>Téléphone</Label><Input value={form.telephone} onChange={e => set("telephone", e.target.value)} /></div>
            <div><Label>Adresse</Label><Input value={form.adresse} onChange={e => set("adresse", e.target.value)} /></div>
            <div><Label>Notes</Label><Textarea value={form.notes} onChange={e => set("notes", e.target.value)} rows={2} /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreate(false)}>Annuler</Button>
            <Button onClick={handleCreate} disabled={saving} className="bg-[#FF6200] hover:bg-[#E65800] text-white">
              {saving ? "Création…" : "Créer"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ═══════════════════════════════════════════
// Helpers UI
// ═══════════════════════════════════════════
function LoadingState() {
  return (
    <div className="py-16 text-center text-gray-400">
      <RefreshCw className="w-6 h-6 mx-auto mb-2 animate-spin" />
      <p className="text-sm">Chargement des données…</p>
    </div>
  );
}

function ErrorState({ msg, onRetry }) {
  return (
    <div className="py-10 text-center">
      <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
      <p className="text-sm text-red-600 mb-3">{msg || "Impossible de charger les données"}</p>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          <RotateCw className="w-4 h-4 mr-1" /> Réessayer
        </Button>
      )}
    </div>
  );
}
