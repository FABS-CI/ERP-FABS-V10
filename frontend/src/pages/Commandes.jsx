/**
 * Page Commandes - Liste et gestion des commandes
 * Sprint 6
 */
import React, { useState, useEffect } from 'react';
import { useDebouncedValue } from '../hooks/useDebouncedValue';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Filter, FileText, Calendar, TrendingUp, MessageCircle, Download } from 'lucide-react';
import { useSortableData } from '../hooks/useSortableData';
import SortTh from '../components/ui/SortTh';
import { exportCsv } from '../utils/exportCsv';
import { getCommandesPaginated } from '../services/commandesApi';
import { listClients } from '../services/clientsApi';
import { createProforma } from '../services/proformasApi';
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
  en_attente: { label: 'En attente', color: 'bg-yellow-500' },
  validee: { label: 'Validée', color: 'bg-blue-500' },
  preparee: { label: 'Préparée', color: 'bg-purple-500' },
  livree: { label: 'Livrée', color: 'bg-green-500' },
  annulee: { label: 'Annulée', color: 'bg-red-500' },
};

export default function Commandes() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [commandes, setCommandes] = useState([]);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pageData, setPageData] = useState({ total: 0, has_next: false, limit: 50 });
  const [filters, setFilters] = useState({
    statut: 'all',
    client_id: 'all',
    q: '',
    date_debut: '',
    date_fin: '',
  });

  const [stats, setStats] = useState({
    total: 0,
    en_attente: 0,
    validees: 0,
    ca_total: 0,
  });

  const canWrite = user && can(user.role, 'commandes', 'create');
  const [exporting, setExporting] = useState(false);
  const { sorted: sortedCommandes, sortKey, sortDir, requestSort } = useSortableData(commandes, null, 'asc');

  const debouncedQ = useDebouncedValue(filters.q, 350);
  // ✅ TICKET-003 : debounce sur les dates pour éviter requêtes en rafale
  const debouncedDateDebut = useDebouncedValue(filters.date_debut, 400);
  const debouncedDateFin   = useDebouncedValue(filters.date_fin, 400);

  useEffect(() => {
    fetchClients();
  }, []);

  // ✅ TICKET-003 : tous les filtres déclenchent fetchCommandes automatiquement
  useEffect(() => {
    setPage(1); // reset page on filter change
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedQ, filters.statut, filters.client_id, debouncedDateDebut, debouncedDateFin]);

  useEffect(() => {
    fetchCommandes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, debouncedQ, filters.statut, filters.client_id, debouncedDateDebut, debouncedDateFin]);

  const fetchClients = async () => {
    try {
      const data = await listClients({ actif: true, page_size: 100 });
      setClients(data.items || []);
    } catch (error) {
      console.error('Erreur chargement clients:', error);
      setClients([]);
    }
  };

  const fetchCommandes = async () => {
    setLoading(true);
    try {
      // TICKET-014 : utilise getCommandesPaginated pour avoir total + pagination
      const result = await getCommandesPaginated({
        ...filters,
        date_debut: debouncedDateDebut,
        date_fin: debouncedDateFin,
        limit: 50,
        page,
      });
      const items = result.items || [];
      setCommandes(items);
      setPageData({ total: result.total || 0, has_next: result.has_next || false, limit: result.limit || 50 });

      // Calculate stats from current page (total from server for display)
      setStats({
        total: result.total || items.length,
        en_attente: items.filter(c => c.statut === 'en_attente').length,
        validees: items.filter(c => c.statut === 'validee').length,
        ca_total: items.reduce((sum, c) => sum + (c.statut !== 'annulee' ? c.montant_total : 0), 0),
      });
    } catch (error) {
      console.error('Erreur chargement commandes:', error);
      toast.error('Erreur lors du chargement des commandes');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleSearch = () => {
    fetchCommandes();
  };

  const handleReset = () => {
    // ✅ TICKET-003 : plus de setTimeout — le useEffect réagit au changement de filters
    setFilters({
      statut: 'all',
      client_id: 'all',
      q: '',
      date_debut: '',
      date_fin: '',
    });
  };

  const handleCreateProforma = async (commande) => {
    try {
      const payload = {
        client_id: commande.client_id,
        commande_id: commande.commande_id,
        notes: `Proforma générée depuis commande ${commande.reference}`,
      };
      const proforma = await createProforma(payload);
      toast.success('Proforma créée avec succès');
      navigate(`/proformas/${proforma.proforma_id}`);
    } catch (error) {
      console.error('Erreur création proforma:', error);
      toast.error('Erreur lors de la création de la proforma');
    }
  };

  const handleExportCommandes = async () => {
    setExporting(true);
    try {
      const result = await getCommandesPaginated({
        ...filters,
        date_debut: debouncedDateDebut,
        date_fin: debouncedDateFin,
        limit: 200,
        page: 1,
      });
      const items = result.items || [];
      const headers = ['Référence', 'Client', 'Date', 'Montant TTC FCFA', 'Statut'];
      const rows = items.map((c) => [
        c.reference,
        c.client_nom || '',
        c.date_commande ? new Date(c.date_commande).toLocaleDateString('fr-FR') : '',
        String(c.montant_total || 0),
        STATUT_CONFIG[c.statut]?.label || c.statut,
      ]);
      const date = new Date().toISOString().slice(0, 10);
      exportCsv(`commandes_fabs_${date}`, headers, rows);
      toast.success(`${items.length} commandes exportées`);
    } catch (e) {
      toast.error("Échec de l'export");
    } finally {
      setExporting(false);
    }
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

  return (
    <DashboardLayout>
    <div className="space-y-6">
      {/* Header */}
      <PageHeader
        title="Commandes"
        subtitle="Gestion du cycle de vie des commandes"
        pagePath="/commandes"
        actions={
          <>
            <Button
              variant="outline"
              onClick={handleExportCommandes}
              disabled={exporting || loading}
              data-testid="btn-export-commandes"
              className="h-9"
            >
              <Download className="h-4 w-4 mr-2" />
              {exporting ? 'Export…' : 'Export'}
            </Button>
            {canWrite && (
            <Button
              onClick={() => navigate('/commandes/nouvelle')}
              className="bg-blue-600 hover:bg-blue-700 text-white h-9"
              data-testid="btn-nouvelle-commande"
            >
              <Plus className="h-4 w-4 mr-2" />
              Nouvelle
            </Button>
            )}
          </>
        }
      />

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total commandes</CardDescription>
            <CardTitle className="text-2xl">{stats.total}</CardTitle>
          </CardHeader>
          <CardContent>
            <FileText className="h-4 w-4 text-gray-500 dark:text-white/50" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>En attente</CardDescription>
            <CardTitle className="text-2xl text-yellow-600">{stats.en_attente}</CardTitle>
          </CardHeader>
          <CardContent>
            <Calendar className="h-4 w-4 text-yellow-500" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Validées</CardDescription>
            <CardTitle className="text-2xl text-blue-600">{stats.validees}</CardTitle>
          </CardHeader>
          <CardContent>
            <Filter className="h-4 w-4 text-blue-500" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>CA Total</CardDescription>
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
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Recherche</label>
              <Input
                placeholder="Référence, client, représentant, ville, téléphone..."
                value={filters.q}
                onChange={(e) => handleFilterChange('q', e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                data-testid="input-search-commande"
              />
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
          <CardTitle>Liste des commandes</CardTitle>
          <CardDescription>{commandes.length} commande(s)</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
            </div>
          ) : commandes.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 mx-auto text-gray-400 mb-4" />
              <p className="text-gray-600 dark:text-gray-400">Aucune commande trouvée</p>
            </div>
          ) : (
            <div className="overflow-x-auto -mx-2">
              <table className="min-w-[640px] w-full">
                <thead className="border-b">
                  <tr className="text-left">
                    <SortTh label="Référence" sortKey="reference" currentKey={sortKey} dir={sortDir} onSort={requestSort} className="pb-3" />
                    <SortTh label="Client" sortKey="client_nom" currentKey={sortKey} dir={sortDir} onSort={requestSort} className="pb-3" />
                    <SortTh label="Date" sortKey="date_commande" currentKey={sortKey} dir={sortDir} onSort={requestSort} className="pb-3" />
                    <SortTh label="Montant" sortKey="montant_ttc" currentKey={sortKey} dir={sortDir} onSort={requestSort} className="pb-3 text-right" />
                    <th className="pb-3 font-semibold">Statut</th>
                    <th className="pb-3 font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedCommandes.map((commande) => (
                    <tr
                      key={commande.commande_id}
                      className="border-b hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
                      onClick={() => navigate(`/commandes/${commande.commande_id}`)}
                      data-testid={`row-commande-${commande.reference}`}
                    >
                      <td className="py-3 font-mono text-sm">{commande.reference}</td>
                      <td className="py-3">{commande.client_nom || '-'}</td>
                      <td className="py-3 text-sm text-gray-600 dark:text-gray-400">
                        {formatDate(commande.date_commande)}
                      </td>
                      <td className="py-3 text-right font-semibold">
                        {formatCurrency(commande.montant_total)}
                      </td>
                      <td className="py-3">
                        <Badge className={`${STATUT_CONFIG[commande.statut].color} text-white`}>
                          {STATUT_CONFIG[commande.statut].label}
                        </Badge>
                      </td>
                      <td className="py-3">
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/commandes/${commande.commande_id}`);
                            }}
                            data-testid={`btn-voir-${commande.reference}`}
                          >
                            Voir
                          </Button>
                          {commande.statut === 'validee' && canWrite && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleCreateProforma(commande);
                              }}
                              data-testid={`btn-proforma-${commande.reference}`}
                            >
                              <MessageCircle className="h-4 w-4 mr-1" />
                              Proforma
                            </Button>
                          )}
                        </div>
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
                Page {page} · {pageData.total} commande{pageData.total > 1 ? 's' : ''} au total
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
