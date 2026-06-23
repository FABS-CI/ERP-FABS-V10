/**
 * HistoriqueEnvois — Journal des envois cross-documents (WhatsApp + Email)
 * ERP FABS-CI
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Mail, MessageCircle, Filter, RefreshCw, Search } from 'lucide-react';
import DashboardLayout from '../components/layout/DashboardLayout';
import PageHeader from "../components/PageHeader";
import { Button } from '../components/ui/button';
import axios from 'axios';
import API_BASE_URL from '../config/api';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

const CANAL_LABELS = {
  email: { label: 'Email', icon: Mail, color: 'text-blue-600 bg-blue-50' },
  whatsapp: { label: 'WhatsApp', icon: MessageCircle, color: 'text-green-600 bg-green-50' },
};

const TYPE_DOC_LABELS = {
  proforma: 'Proforma',
  facture: 'Facture',
  commande: 'Commande',
  avoir: 'Avoir',
  bl: 'Bon de livraison',
  recu: 'Reçu',
};

const STATUT_COLORS = {
  envoye: 'bg-green-100 text-green-800',
  echec: 'bg-red-100 text-red-800',
  en_attente: 'bg-yellow-100 text-yellow-800',
};

export default function HistoriqueEnvois() {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 50;

  // Filtres
  const [filters, setFilters] = useState({
    date_debut: '',
    date_fin: '',
    type_document: '',
    canal: '',
    user_id: '',
  });
  const [search, setSearch] = useState('');

  const fetchLogs = useCallback(async (p = 1) => {
    setLoading(true);
    try {
      const params = { page: p, page_size: PAGE_SIZE };
      if (filters.date_debut) params.date_debut = filters.date_debut;
      if (filters.date_fin) params.date_fin = filters.date_fin;
      if (filters.type_document) params.type_document = filters.type_document;
      if (filters.canal) params.canal = filters.canal;
      if (filters.user_id) params.user_id = filters.user_id;

      const r = await axios.get(`${API_BASE_URL}/envois-historique`, { params });
      setLogs(r.data.items || []);
      setTotal(r.data.total || 0);
      setPage(p);
    } catch (err) {
      console.error('Erreur chargement historique envois:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchLogs(1);
  }, [fetchLogs]);

  const handleFilterChange = (key, value) => {
    setFilters(f => ({ ...f, [key]: value }));
  };

  const resetFilters = () => {
    setFilters({ date_debut: '', date_fin: '', type_document: '', canal: '', user_id: '' });
    setSearch('');
  };

  // Filtrage local par recherche (référence / destinataire)
  const filtered = logs.filter(log => {
    if (!search) return true;
    const s = search.toLowerCase();
    return (
      (log.reference || '').toLowerCase().includes(s) ||
      (log.destinataire || '').toLowerCase().includes(s) ||
      (log.user_email || '').toLowerCase().includes(s)
    );
  });

  const formatDate = (iso) => {
    if (!iso) return '—';
    try {
      return format(new Date(iso), 'dd/MM/yyyy HH:mm', { locale: fr });
    } catch {
      return iso;
    }
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-[#0A2540]">Journal des envois</h1>
            <p className="text-sm text-gray-500 dark:text-white/50 mt-1">
              Historique de tous les envois WhatsApp & Email — tous documents
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchLogs(page)}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Actualiser
          </Button>
        </div>

        {/* Filtres */}
        <div className="bg-white dark:bg-[#0b1e30] rounded-xl border p-4 space-y-4">
          <div className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-white/90">
            <Filter className="h-4 w-4" />
            Filtres
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {/* Date début */}
            <div>
              <label className="block text-xs text-gray-500 dark:text-white/50 mb-1">Du</label>
              <input
                type="date"
                value={filters.date_debut}
                onChange={e => handleFilterChange('date_debut', e.target.value)}
                className="w-full border rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#FF6200]/40"
              />
            </div>
            {/* Date fin */}
            <div>
              <label className="block text-xs text-gray-500 dark:text-white/50 mb-1">Au</label>
              <input
                type="date"
                value={filters.date_fin}
                onChange={e => handleFilterChange('date_fin', e.target.value)}
                className="w-full border rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#FF6200]/40"
              />
            </div>
            {/* Type document */}
            <div>
              <label className="block text-xs text-gray-500 dark:text-white/50 mb-1">Type document</label>
              <select
                value={filters.type_document}
                onChange={e => handleFilterChange('type_document', e.target.value)}
                className="w-full border rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#FF6200]/40"
              >
                <option value="">Tous</option>
                {Object.entries(TYPE_DOC_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
            </div>
            {/* Canal */}
            <div>
              <label className="block text-xs text-gray-500 dark:text-white/50 mb-1">Canal</label>
              <select
                value={filters.canal}
                onChange={e => handleFilterChange('canal', e.target.value)}
                className="w-full border rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#FF6200]/40"
              >
                <option value="">Tous</option>
                <option value="email">Email</option>
                <option value="whatsapp">WhatsApp</option>
              </select>
            </div>
            {/* Recherche */}
            <div>
              <label className="block text-xs text-gray-500 dark:text-white/50 mb-1">Recherche</label>
              <div className="relative">
                <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400" />
                <input
                  type="text"
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  placeholder="Réf, email, user…"
                  className="w-full pl-7 border rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#FF6200]/40"
                />
              </div>
            </div>
          </div>
          <div className="flex justify-end">
            <button
              onClick={resetFilters}
              className="text-xs text-gray-500 dark:text-white/50 hover:text-[#FF6200] underline"
            >
              Réinitialiser les filtres
            </button>
          </div>
        </div>

        {/* Tableau */}
        <div className="bg-white dark:bg-[#0b1e30] rounded-xl border overflow-hidden">
          <div className="px-4 py-3 border-b flex justify-between items-center">
            <span className="text-sm text-gray-500 dark:text-white/50">
              {total} envoi{total !== 1 ? 's' : ''} au total
              {search ? ` (${filtered.length} affichés)` : ''}
            </span>
          </div>

          {loading ? (
            <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
              Chargement…
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
              Aucun envoi trouvé
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 dark:bg-white/5 text-xs uppercase text-gray-500 dark:text-white/50">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium">Date</th>
                    <th className="px-4 py-3 text-left font-medium">Canal</th>
                    <th className="px-4 py-3 text-left font-medium">Type</th>
                    <th className="px-4 py-3 text-left font-medium">Référence</th>
                    <th className="px-4 py-3 text-left font-medium">Destinataire</th>
                    <th className="px-4 py-3 text-left font-medium">CC</th>
                    <th className="px-4 py-3 text-left font-medium">Objet</th>
                    <th className="px-4 py-3 text-left font-medium">Utilisateur</th>
                    <th className="px-4 py-3 text-left font-medium">Statut</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filtered.map((log, i) => {
                    const canalInfo = CANAL_LABELS[log.canal] || { label: log.canal, color: 'text-gray-600 dark:text-white/70 bg-gray-50 dark:bg-white/5' };
                    const CanalIcon = canalInfo.icon || Mail;
                    return (
                      <tr key={log.log_id || i} className="hover:bg-gray-50 dark:bg-white/5 transition-colors">
                        <td className="px-4 py-3 whitespace-nowrap text-gray-600 dark:text-white/70">
                          {formatDate(log.created_at)}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${canalInfo.color}`}>
                            <CanalIcon className="h-3 w-3" />
                            {canalInfo.label}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-gray-700 dark:text-white/90 capitalize">
                          {TYPE_DOC_LABELS[log.type_document] || log.type_document || '—'}
                        </td>
                        <td className="px-4 py-3 font-mono text-xs text-[#0A2540] font-medium">
                          {log.reference || '—'}
                        </td>
                        <td className="px-4 py-3 text-gray-600 dark:text-white/70 max-w-[160px] truncate">
                          {log.destinataire || '—'}
                        </td>
                        <td className="px-4 py-3 text-gray-500 dark:text-white/50 text-xs max-w-[120px] truncate">
                          {log.cc || '—'}
                        </td>
                        <td className="px-4 py-3 text-gray-600 dark:text-white/70 max-w-[200px] truncate">
                          {log.objet || '—'}
                        </td>
                        <td className="px-4 py-3 text-gray-500 dark:text-white/50 text-xs">
                          {log.user_email || log.user_id || '—'}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUT_COLORS[log.statut] || 'bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-white/70'}`}>
                            {log.statut || '—'}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-4 py-3 border-t flex items-center justify-between text-sm text-gray-500 dark:text-white/50">
              <span>Page {page} / {totalPages}</span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => fetchLogs(page - 1)}
                >
                  ← Précédent
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => fetchLogs(page + 1)}
                >
                  Suivant →
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
