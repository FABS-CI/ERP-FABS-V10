import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Search, Filter, Plus, MoreHorizontal, ChevronLeft, ChevronRight,
  Pencil, PowerOff, RotateCw, AlertCircle, Download,
} from "lucide-react";
import { toast } from "sonner";

import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";
import ClientFormDialog from "../components/clients/ClientFormDialog";
import SortTh from "../components/ui/SortTh";
import { TYPE_CLIENTS, TYPE_COLOR, listClients, disableClient } from "../services/clientsApi";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { useSortableData } from "../hooks/useSortableData";
import { exportCsv } from "../utils/exportCsv";
import { formatFCFA } from "../utils/format";
import { useAuth } from "../hooks/useAuth";
import { can } from "../constants/permissions";
import { useCustomPermissions } from "../hooks/useCustomPermissions";

export default function Clients() {
  const navigate = useNavigate();
  const { role } = useAuth();
  const customPerms = useCustomPermissions();
  const canWrite = can(role, "clients") && ["super_admin", "directeur_general", "directeur_commercial", "secretariat"].includes(role) && customPerms.canCreateClients;
  const canModify = customPerms.canModifyClients;
  const canDisable = customPerms.canDisableClients;

  const [q, setQ] = useState("");
  const [typeClient, setTypeClient] = useState("");
  const [ville, setVille] = useState("");
  const [actif, setActif] = useState("true"); // "true" | "false" | ""
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 20;
  const [data, setData] = useState({ items: [], total: 0, page: 1, page_size: PAGE_SIZE });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editing, setEditing] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [exporting, setExporting] = useState(false);

  const dq = useDebouncedValue(q, 300);
  const dville = useDebouncedValue(ville, 300);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await listClients({
        q: dq || undefined,
        type_client: typeClient || undefined,
        ville: dville || undefined,
        actif: actif === "" ? undefined : actif === "true",
        page,
        page_size: PAGE_SIZE,
      });
      setData(r);
    } catch (e) {
      setError(e?.response?.data?.detail || "Erreur de chargement");
    } finally {
      setLoading(false);
    }
  }, [dq, typeClient, dville, actif, page]);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => { setPage(1); }, [dq, typeClient, dville, actif]);

  const totalPages = Math.max(1, Math.ceil(data.total / PAGE_SIZE));

  // Tri local sur la page courante
  const { sorted, sortKey, sortDir, requestSort } = useSortableData(data.items, null, "asc");

  const handleDisable = async (client) => {
    const ok = window.confirm(
      `Désactiver le client "${client.nom}" ?\n\nIl n'apparaîtra plus dans les listes mais ses données sont conservées.`
    );
    if (!ok) return;
    try {
      await disableClient(client.client_id);
      toast.success(`${client.nom} désactivé`);
      fetchData();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Échec de la désactivation");
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      // Récupère jusqu'à 500 clients avec les filtres actifs
      const r = await listClients({
        q: dq || undefined,
        type_client: typeClient || undefined,
        ville: dville || undefined,
        actif: actif === "" ? undefined : actif === "true",
        page: 1,
        page_size: 500,
      });
      const headers = ["Référence", "Nom", "Type", "Représentant", "Téléphone", "Ville", "Solde FCFA", "Statut"];
      const rows = r.items.map((c) => [
        c.reference,
        c.nom,
        TYPE_COLOR[c.type_client]?.label || c.type_client,
        c.representant || "",
        c.telephone || "",
        c.ville || "",
        c.solde != null ? String(c.solde) : "0",
        c.actif ? "Actif" : "Désactivé",
      ]);
      const date = new Date().toISOString().slice(0, 10);
      exportCsv(`clients_fabs_${date}`, headers, rows);
      toast.success(`${r.items.length} clients exportés`);
    } catch (e) {
      toast.error("Échec de l'export");
    } finally {
      setExporting(false);
    }
  };

  return (
    <DashboardLayout>
      <div data-testid="clients-page" className="max-w-7xl mx-auto">
        {/* Header */}
        <PageHeader
          title="Clients"
          subtitle={`${data.total} client${data.total > 1 ? "s" : ""} dans la base`}
          pagePath="/clients"
          actions={
            <>
              <button
                onClick={handleExport}
                disabled={exporting || loading}
                className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-[#0b1e30]/5 text-gray-700 dark:text-white text-sm font-medium hover:bg-gray-50 dark:hover:bg-white/10 transition disabled:opacity-50"
              >
                <Download className="w-4 h-4" />
                Export
              </button>
              {canWrite && (
                <button
                  data-testid="clients-new-btn"
                  onClick={() => { setEditing(null); setDialogOpen(true); }}
                  className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium shadow-sm hover:shadow-md transition"
                >
                  <Plus className="w-4 h-4" />
                  Nouveau
                </button>
              )}
            </>
          }
        />

        {/* Filters */}
        <div
          data-testid="clients-filters"
          className="bg-white dark:bg-white dark:bg-[#0b1e30]/5 rounded-xl border border-gray-200 dark:border-white/10 p-4 mb-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3"
        >
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              data-testid="clients-search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Nom, téléphone, référence, représentant..."
              className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white dark:bg-[#0b1e30]/5 focus:outline-none focus:ring-2 focus:ring-[#FF6200]/40 focus:border-[#FF6200] text-[#0A2540] dark:text-white"
            />
          </div>
          <select
            data-testid="clients-filter-type"
            value={typeClient}
            onChange={(e) => setTypeClient(e.target.value)}
            className="text-sm rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white dark:bg-[#0b1e30]/5 px-3 py-2 text-[#0A2540] dark:text-white"
          >
            <option value="">Tous les types</option>
            {TYPE_CLIENTS.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
          <div className="relative">
            <Filter className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              data-testid="clients-filter-ville"
              value={ville}
              onChange={(e) => setVille(e.target.value)}
              placeholder="Ville..."
              className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white dark:bg-[#0b1e30]/5 focus:outline-none focus:ring-2 focus:ring-[#FF6200]/40 text-[#0A2540] dark:text-white"
            />
          </div>
          <select
            data-testid="clients-filter-actif"
            value={actif}
            onChange={(e) => setActif(e.target.value)}
            className="text-sm rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white dark:bg-[#0b1e30]/5 px-3 py-2 text-[#0A2540] dark:text-white"
          >
            <option value="true">Actifs uniquement</option>
            <option value="false">Désactivés uniquement</option>
            <option value="">Tous</option>
          </select>
        </div>

        {error && (
          <div
            data-testid="clients-error"
            className="bg-red-50 border border-[#C62828]/30 text-[#C62828] rounded-lg p-4 text-sm mb-5 flex items-center gap-2"
          >
            <AlertCircle className="w-4 h-4" />
            {error}
            <button onClick={fetchData} className="ml-auto text-xs font-semibold underline">
              <RotateCw className="w-3 h-3 inline mr-1" />Réessayer
            </button>
          </div>
        )}

        {/* Table */}
        <div className="bg-white dark:bg-white dark:bg-[#0b1e30]/5 rounded-xl border border-gray-200 dark:border-white/10 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[700px]">
              <thead>
                <tr className="bg-gray-50 dark:bg-white dark:bg-[#0b1e30]/5 text-[10px] uppercase tracking-wider text-[#0A2540]/70 dark:text-white/60">
                  <th className="text-left px-4 py-3 font-semibold">Référence</th>
                  <SortTh label="Nom" sortKey="nom" currentKey={sortKey} currentDir={sortDir} onSort={requestSort} className="text-left" />
                  <SortTh label="Type" sortKey="type_client" currentKey={sortKey} currentDir={sortDir} onSort={requestSort} className="text-left" />
                  <th className="text-left px-4 py-3 font-semibold">Représentant</th>
                  <th className="text-left px-4 py-3 font-semibold">Téléphone</th>
                  <SortTh label="Ville" sortKey="ville" currentKey={sortKey} currentDir={sortDir} onSort={requestSort} className="text-left" />
                  <SortTh label="Solde" sortKey="solde" currentKey={sortKey} currentDir={sortDir} onSort={requestSort} className="text-right" />
                  <th className="text-center px-4 py-3 font-semibold">Statut</th>
                  <th className="text-right px-4 py-3 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading && (
                  <tr>
                    <td colSpan={9} className="px-4 py-10 text-center text-gray-500 dark:text-white/50">Chargement…</td>
                  </tr>
                )}
                {!loading && sorted.length === 0 && (
                  <tr>
                    <td colSpan={9} className="px-4 py-10 text-center text-gray-500 dark:text-white/50">Aucun client trouvé.</td>
                  </tr>
                )}
                {!loading && sorted.map((c) => {
                  const type = TYPE_COLOR[c.type_client] || TYPE_COLOR.particulier;
                  return (
                    <tr
                      key={c.client_id}
                      data-testid={`clients-row-${c.reference}`}
                      className="border-t border-gray-100 dark:border-white/10 cursor-pointer transition-all duration-150 hover:bg-[#F97316]/20 dark:hover:bg-[#F97316]/30 hover:shadow-md"
                      onClick={() => navigate(`/clients/${c.client_id}`)}
                    >
                      <td className="px-4 py-3 font-mono text-xs text-[#0A2540] dark:text-white/90">{c.reference}</td>
                      <td className="px-4 py-3 font-semibold text-[#0A2540] dark:text-white">{c.nom}</td>
                      <td className="px-4 py-3">
                        <span
                          className="inline-flex items-center text-[10px] uppercase tracking-wider font-bold px-2 py-0.5 rounded"
                          style={{ background: type.bg, color: type.color }}
                        >
                          {type.label}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-700 dark:text-white/80 whitespace-nowrap">{c.representant || "—"}</td>
                      <td className="px-4 py-3 text-gray-700 dark:text-white/80 whitespace-nowrap">{c.telephone || "—"}</td>
                      <td className="px-4 py-3 text-gray-700 dark:text-white/80">{c.ville || "—"}</td>
                      <td className="px-4 py-3 text-right font-semibold text-[#0A2540] dark:text-white whitespace-nowrap">
                        {c.solde ? formatFCFA(c.solde) : "—"}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {c.actif ? (
                          <span className="inline-block w-2 h-2 rounded-full bg-[#2E7D32]" title="Actif" />
                        ) : (
                          <span className="text-[10px] uppercase tracking-wider bg-gray-100 dark:bg-white dark:bg-[#0b1e30]/10 text-gray-500 dark:text-white/50 px-2 py-0.5 rounded">Désactivé</span>
                        )}
                      </td>
                      <td
                        className="px-4 py-3 text-right whitespace-nowrap"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {canWrite && c.actif && (
                          <div className="inline-flex items-center gap-1">
                            {canModify && (
                              <button
                                data-testid={`clients-edit-${c.reference}`}
                                onClick={() => { setEditing(c); setDialogOpen(true); }}
                                className="p-1.5 rounded hover:bg-[#FF6200]/10 text-[#0A2540] dark:text-white/80"
                                title="Modifier"
                              >
                                <Pencil className="w-3.5 h-3.5" />
                              </button>
                            )}
                            {canDisable && (
                              <button
                                data-testid={`clients-disable-${c.reference}`}
                                onClick={() => handleDisable(c)}
                                className="p-1.5 rounded hover:bg-[#C62828]/10 text-[#C62828]"
                                title="Désactiver"
                              >
                                <PowerOff className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                        )}
                        {!canWrite && <MoreHorizontal className="w-3.5 h-3.5 text-gray-400 inline" />}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {data.total > PAGE_SIZE && (
            <div
              data-testid="clients-pagination"
              className="border-t border-gray-100 dark:border-white/10 px-4 py-3 flex items-center justify-between text-xs text-gray-600 dark:text-white/60"
            >
              <span>Page {page} / {totalPages} ({data.total} résultat{data.total > 1 ? "s" : ""})</span>
              <div className="flex gap-2">
                <button
                  data-testid="clients-prev-page"
                  disabled={page === 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-white/10 disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-white dark:bg-[#0b1e30]/5"
                >
                  <ChevronLeft className="w-3 h-3" />Préc.
                </button>
                <button
                  data-testid="clients-next-page"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-white/10 disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-white dark:bg-[#0b1e30]/5"
                >
                  Suiv.<ChevronRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <ClientFormDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        client={editing}
        onSaved={() => fetchData()}
      />
    </DashboardLayout>
  );
}
