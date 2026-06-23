/**
 * Page Proformas — Liste et gestion des proformas
 * ERP FABS-CI V10 — Module officiel
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useDebouncedValue } from '../hooks/useDebouncedValue';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, FileText, Send, CheckCircle, Clock, XCircle, ArrowRightCircle } from 'lucide-react';
import { listProformas, getProformasDashboardStats } from '../services/proformasApi';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Skeleton } from '../components/ui/skeleton';
import { toast } from 'sonner';
import { useAuth } from '../hooks/useAuth';
import { can } from '../constants/permissions';
import DashboardLayout from '../components/layout/DashboardLayout';
import PageHeader from "../components/PageHeader";

const STATUT_CONFIG = {
  brouillon:           { label: 'Brouillon',        color: 'bg-gray-400 text-white' },
  generee:             { label: 'Générée',          color: 'bg-blue-500 text-white' },
  envoyee:             { label: 'Envoyée',          color: 'bg-indigo-500 text-white' },
  consultee:           { label: 'Consultée',        color: 'bg-purple-500 text-white' },
  acceptee:            { label: 'Acceptée',         color: 'bg-emerald-600 text-white' },
  refusee:             { label: 'Refusée',          color: 'bg-red-600 text-white' },
  expiree:             { label: 'Expirée',          color: 'bg-orange-500 text-white' },
  convertie_facture:   { label: 'Convertie facture',color: 'bg-[#FF6200] text-white' },
};

const formatMontant = (v) =>
  new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'XOF', maximumFractionDigits: 0 })
    .format(v || 0)
    .replace('XOF', 'FCFA');

export default function Proformas() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total: 0, generees: 0, acceptees: 0, converties: 0, ca_potentiel: 0 });
  const [filters, setFilters] = useState({ q: '', statut: 'all' });

  const canWrite = user && can(user.role, 'proformas');

  const debouncedQ = useDebouncedValue(filters.q, 350);

  const fetchProformas = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.statut !== 'all') params.statut = filters.statut;
      if (debouncedQ) params.q = debouncedQ;
      const data = await listProformas(params);
      setItems(data.items || []);
    } catch (e) {
      console.error(e);
      toast.error("Erreur lors du chargement des proformas");
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [filters.statut, debouncedQ]);

  const fetchStats = useCallback(async () => {
    try {
      const s = await getProformasDashboardStats();
      setStats({
        total: s.total || 0,
        generees: s.generees || 0,
        acceptees: s.acceptees || 0,
        converties: s.converties || 0,
        ca_potentiel: s.ca_potentiel || 0,
      });
    } catch {
      // stats endpoint optionnel
    }
  }, []);

  useEffect(() => {
    fetchProformas();
    fetchStats();
  }, [fetchProformas, fetchStats]);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchProformas();
  };

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="proformas-page">
        {/* Header */}
        <PageHeader
          title="Proformas"
          subtitle="Devis et propositions commerciales"
          pagePath="/proformas"
          actions={
            canWrite && (
              <Button
                data-testid="proforma-create-btn"
                onClick={() => navigate('/proformas/new')}
                className="bg-blue-600 hover:bg-blue-700 text-white h-9"
              >
                <Plus className="h-4 w-4 mr-2" />
                Nouvelle
              </Button>
            )
          }
        />

        {/* KPI */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <Card data-testid="kpi-total">
            <CardHeader className="pb-2">
              <CardDescription>Total</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <FileText className="h-5 w-5 text-blue-500" />
                {stats.total}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card data-testid="kpi-generees">
            <CardHeader className="pb-2">
              <CardDescription>Générées</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <Send className="h-5 w-5 text-indigo-500" />
                {stats.generees}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card data-testid="kpi-acceptees">
            <CardHeader className="pb-2">
              <CardDescription>Acceptées</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-emerald-600" />
                {stats.acceptees}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card data-testid="kpi-converties">
            <CardHeader className="pb-2">
              <CardDescription>Converties</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <ArrowRightCircle className="h-5 w-5 text-[#FF6200]" />
                {stats.converties}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card data-testid="kpi-ca-potentiel">
            <CardHeader className="pb-2">
              <CardDescription>CA potentiel</CardDescription>
              <CardTitle className="text-xl">{formatMontant(stats.ca_potentiel)}</CardTitle>
            </CardHeader>
          </Card>
        </div>

        {/* Filtres */}
        <Card>
          <CardContent className="pt-6">
            <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  data-testid="proforma-search-input"
                  type="search"
                  placeholder="Client, représentant, ville, téléphone..."
                  className="pl-9"
                  value={filters.q}
                  onChange={(e) => setFilters({ ...filters, q: e.target.value })}
                />
              </div>
              <Select
                value={filters.statut}
                onValueChange={(v) => setFilters({ ...filters, statut: v })}
              >
                <SelectTrigger className="w-full md:w-[220px]" data-testid="proforma-statut-filter">
                  <SelectValue placeholder="Statut" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tous les statuts</SelectItem>
                  {Object.entries(STATUT_CONFIG).map(([k, v]) => (
                    <SelectItem key={k} value={k}>{v.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button type="submit" variant="outline" data-testid="proforma-search-btn">
                <Search className="h-4 w-4 mr-2" /> Rechercher
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Liste */}
        <Card>
          <CardHeader>
            <CardTitle>Liste des proformas</CardTitle>
            <CardDescription>
              {items.length} proforma{items.length > 1 ? 's' : ''} affichée{items.length > 1 ? 's' : ''}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : items.length === 0 ? (
              <div className="text-center py-16 text-muted-foreground" data-testid="proforma-empty">
                <FileText className="h-12 w-12 mx-auto mb-3 opacity-30" />
                <p>Aucune proforma à afficher</p>
                {canWrite && (
                  <Button
                    onClick={() => navigate('/proformas/new')}
                    className="mt-4 bg-[#FF6200] hover:bg-[#FF6200]/90 text-white"
                    data-testid="proforma-empty-create-btn"
                  >
                    <Plus className="h-4 w-4 mr-2" /> Créer la première proforma
                  </Button>
                )}
              </div>
            ) : (
              <div className="overflow-x-auto -mx-2">
                <table className="min-w-[600px] w-full text-sm" data-testid="proformas-table">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-2">Référence</th>
                      <th className="text-left py-3 px-2">Client</th>
                      <th className="text-left py-3 px-2">Date</th>
                      <th className="text-left py-3 px-2">Validité</th>
                      <th className="text-right py-3 px-2">Montant TTC</th>
                      <th className="text-center py-3 px-2">Statut</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((p) => {
                      const conf = STATUT_CONFIG[p.statut] || { label: p.statut, color: 'bg-gray-400 text-white' };
                      return (
                        <tr
                          key={p.proforma_id}
                          className="border-b hover:bg-muted/50 cursor-pointer transition-colors"
                          onClick={() => navigate(`/proformas/${p.proforma_id}`)}
                          data-testid={`proforma-row-${p.proforma_id}`}
                        >
                          <td className="py-3 px-2 font-mono font-medium">{p.reference}</td>
                          <td className="py-3 px-2">{p.client_nom || p.client_id}</td>
                          <td className="py-3 px-2">{p.date_proforma || '—'}</td>
                          <td className="py-3 px-2">{p.date_validite || '—'}</td>
                          <td className="py-3 px-2 text-right font-semibold">{formatMontant(p.montant_ttc)}</td>
                          <td className="py-3 px-2 text-center">
                            <Badge className={conf.color}>{conf.label}</Badge>
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
