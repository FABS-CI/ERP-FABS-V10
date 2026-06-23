/**
 * Page Business Intelligence — V10 Enterprise (Sprint 5)
 * Dashboard exécutif consolidé avec graphiques Recharts + forecasting
 */
import React, { useState, useEffect, useCallback, useMemo } from "react";
import {
  TrendingUp, TrendingDown, BarChart3 as BarChartIcon, DollarSign,
  Truck, Target, Users, Package, RefreshCw, Calendar, Wallet, Receipt,
} from "lucide-react";
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";
import API_BASE_URL from "../config/api";
import {
  getDashboardGlobal, forecastVentes, forecastDepenses, analyseRentabiliteClient,
} from "../services/biAnalyticsService";

// Palette officielle FABS-CI
const COLORS = {
  primary: "#FF6200",
  secondary: "#0A2540",
  success: "#10B981",
  warning: "#F59E0B",
  error: "#EF4444",
  bg: "#F9FAFB",
};
const CHART_COLORS = [COLORS.primary, COLORS.secondary, COLORS.success, COLORS.warning, COLORS.error, "#8B5CF6", "#EC4899"];

const formatMoney = (v) =>
  new Intl.NumberFormat("fr-FR").format(Math.round(v || 0)) + " FCFA";

const PERIODES = [
  { value: 7, label: "7 derniers jours" },
  { value: 30, label: "30 derniers jours" },
  { value: 90, label: "90 derniers jours" },
  { value: 180, label: "6 derniers mois" },
  { value: 365, label: "12 derniers mois" },
];

export default function BIAnalytics() {
  const [jours, setJours] = useState(30);
  const [tab, setTab] = useState("executive");
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [forecastV, setForecastV] = useState(null);
  const [forecastD, setForecastD] = useState(null);
  const [rentClients, setRentClients] = useState(null);
  const [clientsMap, setClientsMap] = useState({});
  const [produitsMap, setProduitsMap] = useState({});

  // Charger maps noms (clients & produits) pour résoudre les IDs
  const loadMaps = useCallback(async () => {
    try {
      const [cli, prod] = await Promise.all([
        axios.get(`${API_BASE_URL}/clients?limit=500`).then((r) => r.data).catch(() => []),
        axios.get(`${API_BASE_URL}/produits?limit=500`).then((r) => r.data).catch(() => ({ items: [] })),
      ]);
      const cliList = Array.isArray(cli) ? cli : cli?.items || [];
      const prodList = Array.isArray(prod) ? prod : prod?.items || [];
      setClientsMap(Object.fromEntries(cliList.map((c) => [c.client_id, c.nom || c.raison_sociale || c.email || c.client_id])));
      setProduitsMap(Object.fromEntries(prodList.map((p) => [p.product_id || p.produit_id, p.titre || p.reference])));
    } catch {
      // ignore
    }
  }, []);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getDashboardGlobal(jours);
      setDashboard(data);
    } catch (e) {
      toast.error("Erreur chargement Dashboard BI");
    } finally {
      setLoading(false);
    }
  }, [jours]);

  const loadForecast = useCallback(async () => {
    try {
      const [v, d] = await Promise.all([
        forecastVentes(3).catch(() => null),
        forecastDepenses(3).catch(() => null),
      ]);
      setForecastV(v);
      setForecastD(d);
    } catch { /* */ }
  }, []);

  const loadAnalyses = useCallback(async () => {
    try {
      const today = new Date();
      const debut = new Date(today.getTime() - 90 * 86400000);
      const data = await analyseRentabiliteClient(
        debut.toISOString().split("T")[0],
        today.toISOString().split("T")[0],
      );
      setRentClients(data);
    } catch { /* */ }
  }, []);

  useEffect(() => { loadMaps(); }, [loadMaps]);
  useEffect(() => { loadDashboard(); }, [loadDashboard]);
  useEffect(() => { if (tab === "forecast") loadForecast(); }, [tab, loadForecast]);
  useEffect(() => { if (tab === "analyses") loadAnalyses(); }, [tab, loadAnalyses]);

  // ──────────────── Data transformations ────────────────
  const topClientsChart = useMemo(() => {
    if (!dashboard?.ventes?.top_clients) return [];
    const data = dashboard.ventes.top_clients;
    // Vérifier si c'est un array ou un object
    let entries = [];
    if (Array.isArray(data)) {
      entries = data;
    } else if (data && typeof data === 'object') {
      entries = Object.entries(data);
    }
    if (!Array.isArray(entries)) return [];
    return entries.slice(0, 7).map(([id, montant]) => ({
      name: clientsMap[id] || `Client ${String(id).slice(-6)}`,
      montant: Math.round(montant || 0),
    }));
  }, [dashboard, clientsMap]);

  const topProduitsChart = useMemo(() => {
    if (!dashboard?.ventes?.top_produits) return [];
    const data = dashboard.ventes.top_produits;
    // Vérifier si c'est un array ou un object
    let entries = [];
    if (Array.isArray(data)) {
      entries = data;
    } else if (data && typeof data === 'object') {
      entries = Object.entries(data);
    }
    if (!Array.isArray(entries)) return [];
    return entries.slice(0, 7).map(([id, qty]) => ({
      name: produitsMap[id] || `Produit ${String(id || "?").slice(-6)}`,
      quantite: qty || 0,
    }));
  }, [dashboard, produitsMap]);

  const financeChart = useMemo(() => {
    const f = dashboard?.finance;
    if (!f) return [];
    return [
      { name: "Revenus",  value: Math.round(f.revenus  || 0), color: COLORS.success },
      { name: "Dépenses", value: Math.round(f.depenses || 0), color: COLORS.error },
      { name: "Bénéfice", value: Math.round(f.benefice || 0), color: COLORS.primary },
    ];
  }, [dashboard]);

  const forecastChart = useMemo(() => {
    if (!forecastV?.previsions) return [];
    const prev = forecastV.previsions;
    const entries = Array.isArray(prev) ? prev : Object.entries(prev || {});
    return entries.map((p, idx) => {
      // p peut être un object ou un [key, value]
      const item = Array.isArray(p) && typeof p[0] === 'string' ? { mois: p[0], valeur: p[1] } : p;
      return {
        mois: item.mois || item.label || item[0] || `Mois +${idx + 1}`,
        ventes: Math.round(item.prevision || item.valeur || item[1] || 0),
        depenses: 0,
      };
    });
  }, [forecastV]);

  const periodLabel = PERIODES.find((p) => p.value === jours)?.label || `${jours} jours`;
  const croissance = dashboard?.ventes?.croissance ?? 0;
  const isPositive = croissance > 0;

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="bi-analytics-page">
        {/* Header */}
        <div className="flex items-start justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
              <BarChartIcon className="h-8 w-8 text-[#FF6200]" />
              Business Intelligence
            </h1>
            <p className="text-muted-foreground mt-1">
              Tableau de bord exécutif consolidé · <span className="font-semibold">{periodLabel}</span>
            </p>
          </div>
          <div className="flex gap-2 items-end">
            <Select value={String(jours)} onValueChange={(v) => setJours(Number(v))}>
              <SelectTrigger className="w-[200px]" data-testid="bi-period-select">
                <Calendar className="h-4 w-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PERIODES.map((p) => (
                  <SelectItem key={p.value} value={String(p.value)}>{p.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={loadDashboard} data-testid="bi-refresh">
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} /> Actualiser
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={tab} onValueChange={setTab}>
          <TabsList>
            <TabsTrigger value="executive" data-testid="bi-tab-executive">Dashboard exécutif</TabsTrigger>
            <TabsTrigger value="forecast" data-testid="bi-tab-forecast">Prévisions</TabsTrigger>
            <TabsTrigger value="analyses" data-testid="bi-tab-analyses">Rentabilité clients</TabsTrigger>
          </TabsList>

          {/* ═══════════ EXECUTIVE ═══════════ */}
          <TabsContent value="executive" className="space-y-6 mt-6">
            {/* KPI principaux */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <KPICard
                label="Chiffre d'affaires"
                value={loading ? null : formatMoney(dashboard?.ventes?.ventes_totales)}
                icon={DollarSign}
                color={COLORS.primary}
                trend={croissance}
                testId="kpi-ca"
              />
              <KPICard
                label="Commandes"
                value={loading ? null : (dashboard?.ventes?.nombre_commandes || 0)}
                icon={Receipt}
                color={COLORS.secondary}
                testId="kpi-commandes"
              />
              <KPICard
                label="Panier moyen"
                value={loading ? null : formatMoney(dashboard?.ventes?.panier_moyen)}
                icon={Wallet}
                color={COLORS.success}
                testId="kpi-panier"
              />
              <KPICard
                label="Taux de marge"
                value={loading ? null : `${(dashboard?.finance?.taux_marge || 0).toFixed(1)} %`}
                icon={Target}
                color={COLORS.warning}
                testId="kpi-marge"
              />
            </div>

            {/* KPI secondaires */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <SubKPI label="Bénéfice net"      value={formatMoney(dashboard?.finance?.benefice)}            icon={TrendingUp} color={COLORS.success}  testId="sub-benefice" />
              <SubKPI label="Missions logistiques" value={dashboard?.logistique?.nombre_missions || 0}      icon={Truck}      color={COLORS.secondary} testId="sub-missions" />
              <SubKPI label="Factures impayées" value={dashboard?.finance?.factures_impayees || 0}          icon={Receipt}    color={COLORS.error}     testId="sub-impayees" />
            </div>

            {/* Charts: Finance breakdown + Top clients */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Bar Top clients */}
              <Card data-testid="card-top-clients-chart">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="h-5 w-5 text-[#FF6200]" /> Top clients
                  </CardTitle>
                  <CardDescription>Chiffre d'affaires par client sur la période</CardDescription>
                </CardHeader>
                <CardContent>
                  {topClientsChart.length === 0 ? (
                    <EmptyChart label="Pas encore de ventes sur la période" />
                  ) : (
                    <ResponsiveContainer width="100%" height={260}>
                      <BarChart data={topClientsChart} layout="vertical" margin={{ left: 12, right: 12 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis type="number" tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} stroke="#0A2540" fontSize={11} />
                        <YAxis type="category" dataKey="name" width={140} stroke="#0A2540" fontSize={11} />
                        <Tooltip formatter={(v) => formatMoney(v)} />
                        <Bar dataKey="montant" fill={COLORS.primary} radius={[0, 6, 6, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </CardContent>
              </Card>

              {/* Pie Finance */}
              <Card data-testid="card-finance-pie">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <DollarSign className="h-5 w-5 text-[#FF6200]" /> Ventilation financière
                  </CardTitle>
                  <CardDescription>Revenus · Dépenses · Bénéfice</CardDescription>
                </CardHeader>
                <CardContent>
                  {financeChart.every((d) => d.value === 0) ? (
                    <EmptyChart label="Données financières insuffisantes" />
                  ) : (
                    <ResponsiveContainer width="100%" height={260}>
                      <PieChart>
                        <Pie
                          data={financeChart}
                          dataKey="value"
                          nameKey="name"
                          cx="50%"
                          cy="50%"
                          outerRadius={90}
                          label={(d) => `${d.name}: ${formatMoney(d.value)}`}
                        >
                          {financeChart.map((entry, idx) => (
                            <Cell key={idx} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(v) => formatMoney(v)} />
                      </PieChart>
                    </ResponsiveContainer>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Top produits */}
            <Card data-testid="card-top-produits-chart">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Package className="h-5 w-5 text-[#FF6200]" /> Top produits (quantités vendues)
                </CardTitle>
              </CardHeader>
              <CardContent>
                {topProduitsChart.length === 0 ? (
                  <EmptyChart label="Pas encore de produits vendus sur la période" />
                ) : (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={topProduitsChart} margin={{ left: 12, right: 12, bottom: 60 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="name" stroke="#0A2540" fontSize={11} angle={-30} textAnchor="end" height={80} />
                      <YAxis stroke="#0A2540" fontSize={11} />
                      <Tooltip />
                      <Bar dataKey="quantite" fill={COLORS.secondary} radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ═══════════ FORECAST ═══════════ */}
          <TabsContent value="forecast" className="space-y-6 mt-6">
            <Card data-testid="card-forecast-ventes">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-[#FF6200]" /> Prévisions ventes — 3 prochains mois
                </CardTitle>
                <CardDescription>Modèle : moyenne mobile sur l'historique</CardDescription>
              </CardHeader>
              <CardContent>
                {!forecastV ? (
                  <Skeleton className="h-72 w-full" />
                ) : forecastChart.length === 0 ? (
                  <EmptyChart label="Historique insuffisant pour générer une prévision" />
                ) : (
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={forecastChart}>
                      <defs>
                        <linearGradient id="fillVentes" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.6} />
                          <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="mois" stroke="#0A2540" fontSize={11} />
                      <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} stroke="#0A2540" fontSize={11} />
                      <Tooltip formatter={(v) => formatMoney(v)} />
                      <Area type="monotone" dataKey="ventes" stroke={COLORS.primary} strokeWidth={2} fill="url(#fillVentes)" />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <ForecastCard title="Prévision ventes" data={forecastV} testId="fc-ventes" />
              <ForecastCard title="Prévision dépenses" data={forecastD} testId="fc-depenses" />
            </div>
          </TabsContent>

          {/* ═══════════ ANALYSES ═══════════ */}
          <TabsContent value="analyses" className="space-y-6 mt-6">
            <Card data-testid="card-rentabilite-clients">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-[#FF6200]" /> Rentabilité par client (90 jours)
                </CardTitle>
                <CardDescription>Top 10 contributeurs au CA</CardDescription>
              </CardHeader>
              <CardContent>
                {!rentClients ? (
                  <Skeleton className="h-40 w-full" />
                ) : !rentClients.clients || rentClients.clients.length === 0 ? (
                  <EmptyChart label="Aucune analyse de rentabilité disponible" />
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm" data-testid="rentabilite-table">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-2 px-2">Rang</th>
                          <th className="text-left py-2 px-2">Client</th>
                          <th className="text-right py-2 px-2">CA</th>
                          <th className="text-right py-2 px-2">Commandes</th>
                          <th className="text-right py-2 px-2">Panier moyen</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rentClients.clients.slice(0, 10).map((c, idx) => (
                          <tr key={idx} className="border-b hover:bg-muted/30">
                            <td className="py-2 px-2">
                              <Badge className={idx < 3 ? "bg-[#FF6200] text-white" : "bg-gray-300 text-[#0A2540]"}>
                                #{idx + 1}
                              </Badge>
                            </td>
                            <td className="py-2 px-2 font-medium">{clientsMap[c.client_id] || c.client_id}</td>
                            <td className="py-2 px-2 text-right font-semibold tabular-nums">{formatMoney(c.ca || c.total)}</td>
                            <td className="py-2 px-2 text-right">{c.nombre_commandes || c.commandes || "—"}</td>
                            <td className="py-2 px-2 text-right tabular-nums">{c.panier_moyen ? formatMoney(c.panier_moyen) : "—"}</td>
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

// ────────────────────────── Sub-components ──────────────────────────

function KPICard({ label, value, icon: Icon, color, trend, testId }) {
  return (
    <Card data-testid={testId}>
      <CardContent className="pt-5 pb-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-xs text-muted-foreground uppercase tracking-wide">{label}</p>
            {value === null ? (
              <Skeleton className="h-8 w-32 mt-2" />
            ) : (
              <p className="text-2xl font-bold mt-2 text-[#0A2540] dark:text-white">{value}</p>
            )}
            {trend !== undefined && (
              <div className="flex items-center gap-1 mt-2 text-xs">
                {trend > 0 ? (
                  <><TrendingUp className="h-3 w-3 text-[#10B981]" /><span className="text-[#10B981] font-semibold">+{Number(trend).toFixed(1)}%</span></>
                ) : trend < 0 ? (
                  <><TrendingDown className="h-3 w-3 text-[#EF4444]" /><span className="text-[#EF4444] font-semibold">{Number(trend).toFixed(1)}%</span></>
                ) : (
                  <span className="text-muted-foreground">Stable</span>
                )}
                <span className="text-muted-foreground">vs période précédente</span>
              </div>
            )}
          </div>
          <div className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0" style={{ backgroundColor: `${color}20` }}>
            <Icon className="h-5 w-5" style={{ color }} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function SubKPI({ label, value, icon: Icon, color, testId }) {
  return (
    <Card data-testid={testId}>
      <CardContent className="pt-4 pb-4 flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${color}20` }}>
          <Icon className="h-5 w-5" style={{ color }} />
        </div>
        <div>
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className="text-lg font-bold text-[#0A2540] dark:text-white">{value}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function ForecastCard({ title, data, testId }) {
  return (
    <Card data-testid={testId}>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {!data ? (
          <Skeleton className="h-20 w-full" />
        ) : data.previsions && data.previsions.length > 0 ? (
          data.previsions.slice(0, 3).map((p, i) => (
            <div key={i} className="flex justify-between border-b py-2 last:border-0">
              <span className="text-sm">{p.mois || p.label || `Mois +${i + 1}`}</span>
              <span className="font-semibold tabular-nums">{formatMoney(p.prevision || p.valeur)}</span>
            </div>
          ))
        ) : (
          <p className="text-sm text-muted-foreground text-center py-4">Pas de prévision disponible</p>
        )}
      </CardContent>
    </Card>
  );
}

function EmptyChart({ label }) {
  return (
    <div className="h-60 flex items-center justify-center text-muted-foreground">
      <div className="text-center">
        <BarChartIcon className="h-10 w-10 mx-auto mb-2 opacity-30" />
        <p className="text-sm">{label}</p>
      </div>
    </div>
  );
}
