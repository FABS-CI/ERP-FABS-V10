/**
 * Page FNE — Dashboard Enterprise (Sprint 2 V10)
 * Monitoring temps réel des factures normalisées électroniques DGI Côte d'Ivoire
 */
import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  ShieldCheck, Clock, CheckCircle2, XCircle, AlertTriangle, Activity,
  Send, RefreshCw, Settings, Search, FileText, ExternalLink, Wifi, WifiOff,
  BarChart3, Package, TrendingDown,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";
import { getFNEStats, getBalanceSticker, listFNEInvoices, pingDGI, getStickerDetail } from "../services/fneApi";

const STATUT_COLORS = {
  pending:   { label: "En attente", color: "bg-[#F59E0B] text-white", icon: Clock },
  submitted: { label: "Soumise",    color: "bg-[#0A2540] text-white", icon: Send },
  accepted:  { label: "Certifiée",  color: "bg-[#10B981] text-white", icon: CheckCircle2 },
  certified: { label: "Certifiée",  color: "bg-[#10B981] text-white", icon: CheckCircle2 },
  rejected:  { label: "Rejetée",    color: "bg-[#EF4444] text-white", icon: XCircle },
  error:     { label: "Erreur",     color: "bg-[#EF4444] text-white", icon: AlertTriangle },
  failed:    { label: "Échec",      color: "bg-[#EF4444] text-white", icon: AlertTriangle },
};

const formatNumber = (v) => new Intl.NumberFormat("fr-FR").format(v || 0);

/** Composant : Timbres fiscaux / Stickers DGI */
function StickerSection({ detail, loading }) {
  if (loading) {
    return (
      <Card className="mb-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            <Package className="h-4 w-4" /> Timbres Fiscaux (FNE)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-16 rounded-lg" />)}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!detail) return null;

  const { totaux = {}, par_mois = [], balance_sticker, mode } = detail;

  return (
    <Card className="mb-4">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            <Package className="h-4 w-4" /> Timbres Fiscaux (FNE)
          </CardTitle>
          <div className="flex items-center gap-2">
            {balance_sticker != null && (
              <Badge variant="outline" className="text-xs">
                Solde DGI : <span className="font-bold ml-1">{formatNumber(balance_sticker)}</span>
              </Badge>
            )}
            <Badge variant={mode === "production" ? "default" : "secondary"} className="text-xs capitalize">
              {mode || "sandbox"}
            </Badge>
          </div>
        </div>
        <CardDescription className="text-xs">Répartition globale des stickers émis via DGI</CardDescription>
      </CardHeader>
      <CardContent>
        {/* Totaux */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          {[
            { label: "Total émis",   value: totaux.total,      color: "text-[#0A2540] dark:text-white",  bg: "bg-slate-100 dark:bg-slate-800" },
            { label: "Certifiés",    value: totaux.certifies,  color: "text-[#10B981]", bg: "bg-emerald-50 dark:bg-emerald-900/20" },
            { label: "Rejetés",      value: totaux.rejetes,    color: "text-[#EF4444]", bg: "bg-red-50 dark:bg-red-900/20" },
            { label: "En attente",   value: totaux.en_attente, color: "text-[#F59E0B]", bg: "bg-amber-50 dark:bg-amber-900/20" },
          ].map(({ label, value, color, bg }) => (
            <div key={label} className={`rounded-lg p-3 ${bg}`}>
              <p className="text-xs text-muted-foreground mb-1">{label}</p>
              <p className={`text-2xl font-bold ${color}`}>{formatNumber(value)}</p>
            </div>
          ))}
        </div>

        {/* Répartition mensuelle */}
        {par_mois.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2 flex items-center gap-1">
              <BarChart3 className="h-3 w-3" /> Par mois (12 derniers)
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-1 pr-3 font-medium text-muted-foreground">Mois</th>
                    <th className="text-right py-1 px-2 font-medium text-muted-foreground">Total</th>
                    <th className="text-right py-1 px-2 font-medium text-[#10B981]">Certifiés</th>
                    <th className="text-right py-1 px-2 font-medium text-[#EF4444]">Rejetés</th>
                    <th className="text-right py-1 px-2 font-medium text-[#F59E0B]">En attente</th>
                  </tr>
                </thead>
                <tbody>
                  {par_mois.map((row) => (
                    <tr key={row.mois} className="border-b border-dashed last:border-0 hover:bg-muted/30">
                      <td className="py-1 pr-3 font-medium">{row.mois}</td>
                      <td className="text-right py-1 px-2">{formatNumber(row.total)}</td>
                      <td className="text-right py-1 px-2 text-[#10B981]">{formatNumber(row.certifies)}</td>
                      <td className="text-right py-1 px-2 text-[#EF4444]">{formatNumber(row.rejetes)}</td>
                      <td className="text-right py-1 px-2 text-[#F59E0B]">{formatNumber(row.en_attente)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function FNE() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [sticker, setSticker] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [filterStatus, setFilterStatus] = useState("all");
  const [search, setSearch] = useState("");
  const [pingResult, setPingResult] = useState(null);
  const [stickerDetail, setStickerDetail] = useState(null);

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [s, b, list, sd] = await Promise.all([
        getFNEStats().catch(() => null),
        getBalanceSticker().catch(() => null),
        listFNEInvoices({ limit: 50 }).catch(() => ({ invoices: [] })),
        getStickerDetail().catch(() => null),
      ]);
      setStats(s);
      setSticker(b);
      setInvoices(list.invoices || []);
      setStickerDetail(sd);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  const handlePing = async () => {
    setPingResult({ loading: true });
    try {
      const r = await pingDGI();
      setPingResult(r);
      if (r.ok) toast.success(`API DGI joignable (${r.elapsed_ms} ms)`);
      else toast.error(`API DGI injoignable : ${r.error || ""}`);
    } catch (e) {
      toast.error("Erreur ping DGI");
      setPingResult({ ok: false, error: String(e) });
    }
  };

  const visibleInvoices = invoices.filter((inv) => {
    if (filterStatus !== "all" && inv.status !== filterStatus) return false;
    if (search && !(inv.invoice_id || "").toLowerCase().includes(search.toLowerCase()) &&
        !(inv.fne_id || "").toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="fne-dashboard">
        {/* Header */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
              <ShieldCheck className="h-8 w-8 text-[#FF6200]" />
              FNE — Facture Normalisée Électronique
            </h1>
            <p className="text-muted-foreground mt-1">
              Monitoring temps réel · API DGI Côte d&apos;Ivoire ·
              {sticker?.mode === "sandbox" && (
                <span className="ml-2 px-2 py-0.5 rounded-full bg-[#F59E0B] text-white text-xs font-semibold">
                  MODE SANDBOX
                </span>
              )}
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={handlePing} data-testid="btn-ping-dgi">
              {pingResult?.ok ? <Wifi className="h-4 w-4 mr-2 text-[#10B981]" /> :
               pingResult?.ok === false ? <WifiOff className="h-4 w-4 mr-2 text-[#EF4444]" /> :
               <Activity className="h-4 w-4 mr-2" />}
              Ping DGI
            </Button>
            <Button variant="outline" onClick={loadAll} data-testid="btn-refresh">
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
              Actualiser
            </Button>
            <Button
              className="bg-[#FF6200] hover:bg-[#FF6200]/90 text-white"
              onClick={() => navigate("/fne/invoices/new")}
              data-testid="btn-new-fne"
            >
              <Send className="h-4 w-4 mr-2" />
              Nouvelle soumission
            </Button>
            <Button variant="outline" onClick={() => navigate("/fne/settings")} data-testid="btn-fne-settings">
              <Settings className="h-4 w-4 mr-2" /> Paramètres
            </Button>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {loading ? (
            Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-24 w-full rounded-lg" />)
          ) : (
            <>
              <KPICard label="Total" value={stats?.total} icon={FileText} color="text-[#0A2540]" testId="kpi-total" />
              <KPICard label="Certifiées" value={stats?.certified} icon={CheckCircle2} color="text-[#10B981]" testId="kpi-certified" />
              <KPICard label="En attente" value={stats?.pending} icon={Clock} color="text-[#F59E0B]" testId="kpi-pending" />
              <KPICard label="Soumises" value={stats?.submitted} icon={Send} color="text-[#0A2540]" testId="kpi-submitted" />
              <KPICard label="Rejetées" value={(stats?.rejected || 0) + (stats?.failed || 0)} icon={XCircle} color="text-[#EF4444]" testId="kpi-rejected" />
              <KPICard label="Taux réussite" value={`${stats?.success_rate || 0} %`} icon={Activity} color="text-[#FF6200]" testId="kpi-success-rate" />
            </>
          )}
        </div>

        {/* Balance Sticker + Avg processing */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card data-testid="card-balance-sticker">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-[#FF6200]" />
                Solde Stickers Fiscaux
              </CardTitle>
              <CardDescription>Timbres FNE restants chez la DGI</CardDescription>
            </CardHeader>
            <CardContent>
              {sticker?.mode === "sandbox" ? (
                <div className="rounded-lg bg-[#F59E0B]/10 border border-[#F59E0B]/30 p-3 text-sm text-[#0A2540] dark:text-white">
                  <AlertTriangle className="inline h-4 w-4 mr-1 text-[#F59E0B]" />
                  {sticker.warning}
                </div>
              ) : (
                <div className="space-y-1">
                  <p className="text-3xl font-bold text-[#0A2540] dark:text-white">
                    {formatNumber(sticker?.data?.balance ?? sticker?.balance)}
                  </p>
                  <p className="text-xs text-muted-foreground">NCC : {sticker?.ncc || sticker?.data?.ncc}</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card data-testid="card-avg-processing">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Activity className="h-5 w-5 text-[#FF6200]" />
                Temps moyen de traitement
              </CardTitle>
              <CardDescription>Soumission → certification</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-[#0A2540] dark:text-white">
                {stats?.avg_processing_seconds || 0} s
              </p>
              <p className="text-xs text-muted-foreground">Moyenne sur les factures certifiées</p>
            </CardContent>
          </Card>
        </div>

        {/* Stickers / Timbres fiscaux section */}
        <StickerSection detail={stickerDetail} loading={loading} />

        {/* Filters */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  data-testid="fne-search"
                  type="search"
                  placeholder="Rechercher par invoice_id ou fne_id…"
                  className="pl-9"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="w-full md:w-[220px]" data-testid="fne-status-filter">
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

        {/* Invoices list */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Factures FNE</CardTitle>
              <CardDescription>{visibleInvoices.length} facture(s)</CardDescription>
            </div>
            <Button variant="ghost" onClick={() => navigate("/fne/logs")} className="text-[#FF6200]" data-testid="btn-fne-logs">
              <ExternalLink className="h-4 w-4 mr-1" /> Journal complet
            </Button>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-40 w-full" />
            ) : visibleInvoices.length === 0 ? (
              <div className="text-center py-16 text-muted-foreground" data-testid="fne-empty">
                <ShieldCheck className="h-12 w-12 mx-auto mb-3 opacity-30" />
                <p>Aucune facture FNE pour l&apos;instant.</p>
                <p className="text-xs mt-1">
                  Les certifications apparaîtront ici dès la première soumission DGI.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto -mx-2">
                <table className="min-w-[640px] w-full text-sm" data-testid="fne-table">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-2">Invoice ID</th>
                      <th className="text-left py-3 px-2">FNE ID</th>
                      <th className="text-left py-3 px-2">Créée</th>
                      <th className="text-left py-3 px-2">Validée</th>
                      <th className="text-center py-3 px-2">Statut</th>
                      <th className="text-right py-3 px-2"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {visibleInvoices.map((inv) => {
                      const conf = STATUT_COLORS[inv.status] || { label: inv.status, color: "bg-gray-400 text-white", icon: AlertTriangle };
                      const Icon = conf.icon;
                      return (
                        <tr
                          key={inv.invoice_id}
                          className="border-b hover:bg-muted/50 cursor-pointer"
                          onClick={() => navigate(`/fne/invoices/${inv.invoice_id}`)}
                          data-testid={`fne-row-${inv.invoice_id}`}
                        >
                          <td className="py-3 px-2 font-mono">{inv.invoice_id}</td>
                          <td className="py-3 px-2 font-mono text-xs text-muted-foreground">{inv.fne_id || "—"}</td>
                          <td className="py-3 px-2">{inv.created_at?.slice(0, 19).replace("T", " ") || "—"}</td>
                          <td className="py-3 px-2">{inv.validated_at?.slice(0, 19).replace("T", " ") || "—"}</td>
                          <td className="py-3 px-2 text-center">
                            <Badge className={`${conf.color} inline-flex items-center gap-1`}>
                              <Icon className="h-3 w-3" /> {conf.label}
                            </Badge>
                          </td>
                          <td className="py-3 px-2 text-right">
                            <ExternalLink className="h-4 w-4 inline text-muted-foreground" />
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
      </div>
    </DashboardLayout>
  );
}

function KPICard({ label, value, icon: Icon, color, testId }) {
  return (
    <Card data-testid={testId}>
      <CardContent className="pt-5 pb-4">
        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground uppercase tracking-wide">{label}</p>
          <Icon className={`h-4 w-4 ${color}`} />
        </div>
        <p className="text-2xl font-bold mt-2 text-[#0A2540] dark:text-white">
          {typeof value === "number" ? formatNumber(value) : value ?? "—"}
        </p>
      </CardContent>
    </Card>
  );
}
