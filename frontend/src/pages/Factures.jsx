/**
 * Page Factures - Liste et gestion des factures
 * Sprint 7
 */
import React, { useState, useEffect } from 'react';
import { useDebouncedValue } from '../hooks/useDebouncedValue';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Filter, FileText, Banknote, TrendingUp, AlertCircle, Download } from 'lucide-react';
import { getFacturesPaginated, getFactures } from '../services/facturesApi';
import { useSortableData } from '../hooks/useSortableData';
import SortTh from '../components/ui/SortTh';
import { exportCsv } from '../utils/exportCsv';
import { listClients } from '../services/clientsApi';
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
import PageHeader from '../components/PageHeader';

const STATUT_CONFIG = {
  brouillon: { label: 'Brouillon', color: 'bg-gray-500' },
  emise: { label: 'Émise', color: 'bg-blue-500' },
  partiellement_payee: { label: 'Partiellement payée', color: 'bg-orange-500' },
  payee: { label: 'Payée', color: 'bg-green-500' },
  annulee: { label: 'Annulée', color: 'bg-red-500' },
  // ✅ TICKET-001 : clé avoir ajoutée (évite TypeError sur STATUT_CONFIG["avoir"])
  avoir: { label: 'Avoir', color: 'bg-purple-500' },
};

// ✅ TICKET-001 : guard défensif — évite tout crash futur sur statut inconnu
const getStatutConfig = (statut) =>
  STATUT_CONFIG[statut] ?? { label: statut ?? '—', color: 'bg-gray-400' };

const FNE_STATUS_CONFIG = {
  pending: { label: '⏳ En attente DGI', color: 'bg-orange-500' },
  certified: { label: '✅ Certifiée DGI', color: 'bg-green-500' },
  rejected: { label: '❌ Rejetée DGI', color: 'bg-red-500' },
  failed: { label: '🔴 Échec technique', color: 'bg-red-700' },
};

const TYPE_CONFIG = {
  facture: { label: 'Facture', color: 'text-blue-600' },
  avoir: { label: 'Avoir', color: 'text-red-600' },
};

export default function Factures() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [factures, setFactures] = useState([]);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pageData, setPageData] = useState({ total: 0, has_next: false, limit: 50 });
  const [filters, setFilters] = useState({
    type_facture: 'all',
    statut: 'all',
    client_id: 'all',
    q: '',
    date_debut: '',
    date_fin: '',
  });

  const [stats, setStats] = useState({
    total: 0,
    emises: 0,
    impayees: 0,
    ca_total: 0,
  });

  const canWrite = user && can(user.role, 'factures', 'create');
  const [exporting, setExporting] = useState(false);
  const { sorted: sortedFactures, sortKey, sortDir, requestSort } = useSortableData(factures, null, 'asc');

  const debouncedQ = useDebouncedValue(filters.q, 350);

  useEffect(() => {
    fetchClients();
  }, []);

  // Reset page on filter/search change
  useEffect(() => {
    setPage(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedQ, filters.statut, filters.type_facture, filters.client_id]);

  useEffect(() => {
    fetchFactures();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, debouncedQ, filters.statut, filters.type_facture, filters.client_id, filters.date_debut, filters.date_fin]);

  const fetchClients = async () => {
    try {
      const data = await listClients({ actif: true, page_size: 100 });
      setClients(data.items || []);
    } catch (error) {
      console.error('Erreur chargement clients:', error);
      setClients([]);
    }
  };

  const fetchFactures = async () => {
    setLoading(true);
    try {
      // TICKET-014 : utilise getFacturesPaginated pour avoir total + pagination
      const result = await getFacturesPaginated({ ...filters, limit: 50, page });
      const items = result.items || [];
      setFactures(items);
      setPageData({ total: result.total || 0, has_next: result.has_next || false, limit: result.limit || 50 });

      setStats({
        total: result.total || items.length,
        emises: items.filter(f => f.statut === 'emise').length,
        impayees: items.filter(f => ['emise', 'partiellement_payee'].includes(f.statut)).length,
        ca_total: items
          .filter(f => f.statut !== 'annulee' && f.type_facture === 'facture')
          .reduce((sum, f) => sum + f.montant_ttc, 0),
      });
    } catch (error) {
      console.error('Erreur chargement factures:', error);
      toast.error('Erreur lors du chargement des factures');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleSearch = () => {
    fetchFactures();
  };

  const handleReset = () => {
    setFilters({
      type_facture: 'all',
      statut: 'all',
      client_id: 'all',
      q: '',
      date_debut: '',
      date_fin: '',
    });
    setTimeout(() => fetchFactures(), 100);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('fr-FR', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount) + ' FCFA';
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('fr-FR');
  };

  const handleExportFactures = async () => {
    setExporting(true);
    try {
      const data = await getFactures({ ...filters, limit: 500 });
      const rows = (Array.isArray(data) ? data : data?.items ?? []).map(f => ({
        'Référence': f.reference || '',
        'Type': f.type_facture || '',
        'Client': f.client_nom || '',
        'Date': f.date_facture ? new Date(f.date_facture).toLocaleDateString('fr-FR') : '',
        'Montant TTC (FCFA)': f.montant_ttc ?? 0,
        'Restant dû (FCFA)': f.restant_du ?? 0,
        'Statut': f.statut || '',
        'FNE': f.fne_status || '',
      }));
      exportCsv(rows, `factures_${new Date().toISOString().slice(0, 10)}.csv`);
      toast.success(`${rows.length} factures exportées`);
    } catch (err) {
      console.error(err);
      toast.error("Erreur lors de l'export");
    } finally {
      setExporting(false);
    }
  };

  return (
    <DashboardLayout>
    <div className="space-y-6">
      {/* Header */}
      <PageHeader
        title="Factures"
        subtitle="Gestion et suivi des factures"
        pagePath="/factures"
        actions={
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportFactures}
              disabled={exporting || factures.length === 0}
              title="Exporter en CSV"
            >
              <Download className="h-4 w-4 mr-2" />
              {exporting ? 'Export...' : 'Export'}
            </Button>
            {canWrite && (
              <Button
                onClick={() => navigate('/commandes')}
                size="sm"
                className="bg-blue-600 hover:bg-blue-700 text-white"
                data-testid="btn-nouvelle-facture"
                title="Depuis une commande validée"
              >
                <Plus className="h-4 w-4 mr-2" />
                Générer
              </Button>
            )}
          </>
        }
      />

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total factures</CardDescription>
            <CardTitle className="text-2xl">{stats.total}</CardTitle>
          </CardHeader>
          <CardContent>
            <FileText className="h-4 w-4 text-gray-500 dark:text-white/50" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Émises</CardDescription>
            <CardTitle className="text-2xl text-blue-600">{stats.emises}</CardTitle>
          </CardHeader>
          <CardContent>
            <Banknote className="h-4 w-4 text-blue-500" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Impayées</CardDescription>
            <CardTitle className="text-2xl text-orange-600">{stats.impayees}</CardTitle>
          </CardHeader>
          <CardContent>
            <AlertCircle className="h-4 w-4 text-orange-500" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>CA Total (TTC)</CardDescription>
            <CardTitle className="text-2xl text-green-600">{formatCurrency(stats.ca_total)}</CardTitle>
          </CardHeader>
          <CardContent>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center">
            <Filter className="h-5 w-5 mr-2" />
            Filtres
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Recherche</label>
              <Input
                placeholder="Client, représentant, ville, téléphone..."
                value={filters.q}
                onChange={(e) => handleFilterChange('q', e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                data-testid="input-search-facture"
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Type</label>
              <Select value={filters.type_facture} onValueChange={(v) => handleFilterChange('type_facture', v)}>
                <SelectTrigger data-testid="select-type">
                  <SelectValue placeholder="Tous" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tous</SelectItem>
                  <SelectItem value="facture">Facture</SelectItem>
                  <SelectItem value="avoir">Avoir</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Statut</label>
              <Select value={filters.statut} onValueChange={(v) => handleFilterChange('statut', v)}>
                <SelectTrigger data-testid="select-statut">
                  <SelectValue placeholder="Tous" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tous</SelectItem>
                  {Object.entries(STATUT_CONFIG).map(([key, config]) => (
                    <SelectItem key={key} value={key}>{config.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Client</label>
              <Select value={filters.client_id} onValueChange={(v) => handleFilterChange('client_id', v)}>
                <SelectTrigger data-testid="select-client">
                  <SelectValue placeholder="Tous" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tous</SelectItem>
                  {clients.map((client) => (
                    <SelectItem key={client.client_id} value={client.client_id}>
                      {client.nom}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Date début</label>
              <Input
                type="date"
                value={filters.date_debut}
                onChange={(e) => handleFilterChange('date_debut', e.target.value)}
                data-testid="input-date-debut"
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Date fin</label>
              <Input
                type="date"
                value={filters.date_fin}
                onChange={(e) => handleFilterChange('date_fin', e.target.value)}
                data-testid="input-date-fin"
              />
            </div>
          </div>

          <div className="flex gap-2 mt-4">
            <Button onClick={handleSearch} data-testid="btn-appliquer-filtres">
              <Search className="h-4 w-4 mr-2" />
              Appliquer
            </Button>
            <Button variant="outline" onClick={handleReset} data-testid="btn-reset-filtres">
              Réinitialiser
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>Liste des factures</CardTitle>
          <CardDescription>{factures.length} facture(s)</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
            </div>
          ) : factures.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 mx-auto text-gray-400 mb-4" />
              <p className="text-gray-600 dark:text-gray-400">Aucune facture trouvée</p>
            </div>
          ) : (
            <div className="overflow-x-auto -mx-2">
              <table className="min-w-[680px] w-full">
                <thead className="border-b">
                  <tr className="text-left">
                    <SortTh label="Référence" sortKey="reference" currentKey={sortKey} dir={sortDir} onSort={requestSort} className="pb-3" />
                    <th className="pb-3 font-semibold">Type</th>
                    <SortTh label="Client" sortKey="client_nom" currentKey={sortKey} dir={sortDir} onSort={requestSort} className="pb-3" />
                    <SortTh label="Date" sortKey="date_facture" currentKey={sortKey} dir={sortDir} onSort={requestSort} className="pb-3" />
                    <SortTh label="Montant TTC" sortKey="montant_ttc" currentKey={sortKey} dir={sortDir} onSort={requestSort} className="pb-3 text-right" />
                    <SortTh label="Restant" sortKey="restant_du" currentKey={sortKey} dir={sortDir} onSort={requestSort} className="pb-3 text-right" />
                    <th className="pb-3 font-semibold">Statut</th>
                    <th className="pb-3 font-semibold">FNE</th>
                    <th className="pb-3 font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedFactures.map((facture) => (
                    <tr
                      key={facture.facture_id}
                      className="border-b hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
                      onClick={() => navigate(`/factures/${facture.facture_id}`)}
                      data-testid={`row-facture-${facture.reference}`}
                    >
                      <td className="py-3 font-mono text-sm">{facture.reference}</td>
                      <td className="py-3">
                        <span className={`font-medium ${TYPE_CONFIG[facture.type_facture].color}`}>
                          {TYPE_CONFIG[facture.type_facture].label}
                        </span>
                      </td>
                      <td className="py-3">{facture.client_nom || '-'}</td>
                      <td className="py-3 text-sm text-gray-600 dark:text-gray-400">
                        {formatDate(facture.date_facture)}
                      </td>
                      <td className="py-3 text-right font-semibold">
                        {formatCurrency(facture.montant_ttc)}
                      </td>
                      <td className="py-3 text-right">
                        <span className={facture.montant_restant > 0 ? 'text-orange-600 font-semibold' : 'text-gray-500 dark:text-white/50'}>
                          {formatCurrency(facture.montant_restant)}
                        </span>
                      </td>
                      <td className="py-3">
                        {/* ✅ TICKET-001 : utilise getStatutConfig (guard défensif) */}
                        <Badge className={`${getStatutConfig(facture.statut).color} text-white`}>
                          {getStatutConfig(facture.statut).label}
                        </Badge>
                      </td>
                      <td className="py-3">
                        {facture.fne_status && FNE_STATUS_CONFIG[facture.fne_status] ? (
                          <Badge className={`${FNE_STATUS_CONFIG[facture.fne_status].color} text-white`}>
                            {FNE_STATUS_CONFIG[facture.fne_status].label}
                          </Badge>
                        ) : (
                          <span className="text-gray-400 text-sm">-</span>
                        )}
                      </td>
                      <td className="py-3">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/factures/${facture.facture_id}`);
                          }}
                          data-testid={`btn-voir-${facture.reference}`}
                        >
                          Voir
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {/* TICKET-014 — Pagination */}
          {pageData.total > 0 && (
            <div className="flex items-center justify-between mt-4 pt-4 border-t">
              <span className="text-sm text-gray-500 dark:text-white/50">
                Page {page} · {pageData.total} facture{pageData.total > 1 ? 's' : ''} au total
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1 || loading}
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                >
                  ← Précédent
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!pageData.has_next || loading}
                  onClick={() => setPage(p => p + 1)}
                >
                  Suivant →
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
    </DashboardLayout>
  );
}
