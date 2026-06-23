/**
 * EtatCompteClients.jsx
 * ÉDITIONS FABS-CI — Module État de Compte Clients
 * Accessible via : FINANCES → États de compte clients
 */
import { useState, useCallback, useRef } from "react";
import {
  FileText, Printer, Search,
  Filter, BarChart2, AlertCircle, Loader2, RefreshCw,
  ChevronDown, ChevronRight, User, MapPin, Phone, Tag,
} from "lucide-react";
import { toast } from "sonner";
import api from "../services/api";  // ✅ PHASE 3.2: Use centralized api instance (HttpOnly + CSRF)

import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";
import { TYPE_CLIENTS } from "../services/clientsApi";

// ─────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────
const API = "/api";

function fmt(n) {
  if (n == null) return "—";
  return new Intl.NumberFormat("fr-FR", { minimumFractionDigits: 0 }).format(Number(n)) + " FCFA";
}

function fmtDate(s) {
  if (!s) return "—";
  const d = new Date(s);
  if (isNaN(d)) return s;
  return d.toLocaleDateString("fr-FR");
}

function statutBadge(statut) {
  const map = {
    payee:                 { label: "Payée",         cls: "bg-green-100 text-green-700 border-green-200" },
    partiellement_payee:   { label: "Partiel",        cls: "bg-yellow-100 text-yellow-700 border-yellow-200" },
    emise:                 { label: "Émise",          cls: "bg-blue-100 text-blue-700 border-blue-200" },
    annulee:               { label: "Annulée",        cls: "bg-red-100 text-red-600 border-red-200" },
  };
  const s = map[statut] || { label: statut, cls: "bg-gray-100 text-gray-600 border-gray-200" };
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold border ${s.cls}`}>
      {s.label}
    </span>
  );
}

// ─────────────────────────────────────────────────────────────────
// Composant principal
// ─────────────────────────────────────────────────────────────────
export default function EtatCompteClients() {
  // ── Filtres ──
  const [filtre, setFiltre]             = useState("tous");
  const [anneeScolaire, setAnneeScolaire] = useState("");
  const [dateDebut, setDateDebut]       = useState("");
  const [dateFin, setDateFin]           = useState("");
  const [clientSearch, setClientSearch] = useState("");
  const [selectedClientId, setSelectedClientId] = useState("");
  const [villeFilter, setVilleFilter]   = useState("");
  const [typeClient, setTypeClient]     = useState("");
  const [representant, setRepresentant] = useState("");

  // ── État preview ──
  const [previewData, setPreviewData]   = useState(null);   // { clients_data, resume }
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [previewError, setPreviewError] = useState(null);
  const [expandedClients, setExpandedClients] = useState({});

  // ── Actions ──
  const [exporting, setExporting]       = useState(false);

  // ── Autocomplete client ──
  const [clientSuggestions, setClientSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions]     = useState(false);
  const clientSearchTimeout = useRef(null);

  // ─────────────────────────────────────────────────────────────
  // Construction des params
  // ─────────────────────────────────────────────────────────────
  const buildParams = useCallback(() => {
    const p = new URLSearchParams();
    p.set("filtre", filtre);
    if (anneeScolaire) p.set("annee_scolaire", anneeScolaire);
    if (dateDebut)     p.set("date_debut", dateDebut);
    if (dateFin)       p.set("date_fin", dateFin);
    if (selectedClientId) p.set("client_id", selectedClientId);
    if (villeFilter)   p.set("ville", villeFilter);
    if (typeClient)    p.set("type_client", typeClient);
    if (representant)  p.set("representant", representant);
    return p.toString();
  }, [filtre, anneeScolaire, dateDebut, dateFin, selectedClientId, villeFilter, typeClient, representant]);

  // ─────────────────────────────────────────────────────────────
  // Autocomplete client
  // ─────────────────────────────────────────────────────────────
  const handleClientSearchChange = (v) => {
    setClientSearch(v);
    setSelectedClientId("");
    if (!v) { setClientSuggestions([]); setShowSuggestions(false); return; }
    clearTimeout(clientSearchTimeout.current);
    clientSearchTimeout.current = setTimeout(async () => {
      try {
        // ✅ PHASE 3.2: api instance handles cookies + CSRF automatically
        const r = await api.get(`${API}/clients`, {
          params: { q: v, page_size: 8 },
        });
        setClientSuggestions(r.data.items || []);
        setShowSuggestions(true);
      } catch { setClientSuggestions([]); }
    }, 280);
  };

  const selectClient = (c) => {
    setSelectedClientId(c.client_id);
    setClientSearch(c.nom);
    setClientSuggestions([]);
    setShowSuggestions(false);
  };

  // ─────────────────────────────────────────────────────────────
  // Aperçu (chargement données JSON pour preview tableau)
  // ─────────────────────────────────────────────────────────────
  const handleApercu = useCallback(async () => {
    setLoadingPreview(true);
    setPreviewError(null);
    setPreviewData(null);
    try {
      const qs = buildParams();
      // ✅ PHASE 3.2: api instance handles cookies + CSRF automatically
      const r = await api.get(`${API}/rapports/etat-compte-clients/data?${qs}`);
      setPreviewData(r.data);
      setExpandedClients({});
    } catch (e) {
      setPreviewError(e?.response?.data?.detail || "Erreur lors du chargement des données");
    } finally {
      setLoadingPreview(false);
    }
  }, [buildParams]);

  // ─────────────────────────────────────────────────────────────
  // Export PDF
  // ─────────────────────────────────────────────────────────────
  const handleExportPdf = useCallback(async () => {
    setExporting(true);
    try {
      const qs = buildParams();
      // ✅ PHASE 3.2: fetch with credentials to include HttpOnly cookies
      const res = await fetch(`${API}/rapports/etat-compte-clients?${qs}`, {
        credentials: "include",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Erreur serveur");
      }
      const blob = await res.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `etat_compte_clients_${filtre}_${anneeScolaire || new Date().getFullYear()}.pdf`;
      a.click();
      URL.revokeObjectURL(a.href);
      toast.success("PDF généré avec succès");
    } catch (e) {
      toast.error(e.message || "Échec de l'export PDF");
    } finally {
      setExporting(false);
    }
  }, [buildParams, filtre, anneeScolaire]);

  // ─────────────────────────────────────────────────────────────
  // ─────────────────────────────────────────────────────────────
  // Imprimer
  // ─────────────────────────────────────────────────────────────
  const handlePrint = useCallback(async () => {
    setExporting(true);
    try {
      const qs = buildParams();
      // ✅ PHASE 3.2: fetch with credentials to include HttpOnly cookies
      const res = await fetch(`${API}/rapports/etat-compte-clients?${qs}`, {
        credentials: "include",
      });
      if (!res.ok) throw new Error("Erreur serveur");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const win = window.open(url, "_blank");
      if (win) {
        win.addEventListener("load", () => { win.print(); });
      }
    } catch (e) {
      toast.error(e.message || "Échec de l'impression");
    } finally {
      setExporting(false);
    }
  }, [buildParams]);

  // ─────────────────────────────────────────────────────────────
  // Toggle expansion client dans le tableau preview
  // ─────────────────────────────────────────────────────────────
  const toggleClient = (cid) => {
    setExpandedClients((prev) => ({ ...prev, [cid]: !prev[cid] }));
  };

  // ─────────────────────────────────────────────────────────────
  // Rendu
  // ─────────────────────────────────────────────────────────────
  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">

        {/* ── En-tête ── */}
        <div className="mb-6">
          <p className="text-xs uppercase tracking-[0.2em] text-[#FF6200] font-semibold">
            Finances — Rapports
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-[#0A2540] dark:text-white mt-1">
            État de Compte Clients
          </h1>
          <p className="text-sm text-gray-500 dark:text-white/50 mt-1">
            Consultez et exportez les états de compte par client, période, ville ou type.
          </p>
        </div>

        {/* ── Panneau filtres ── */}
        <div className="bg-white dark:bg-[#0b1e30] border border-gray-200 dark:border-white/10 rounded-xl p-5 mb-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Filter className="w-4 h-4 text-[#FF6200]" />
            <span className="text-sm font-semibold text-[#0A2540] dark:text-white">Filtres</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">

            {/* Filtre statut */}
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-white/60 mb-1">
                Statut paiement
              </label>
              <select
                value={filtre}
                onChange={(e) => setFiltre(e.target.value)}
                className="w-full rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-[#0A2540] text-sm text-[#0A2540] dark:text-white px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#FF6200]/40"
              >
                <option value="tous">Tous les comptes</option>
                <option value="paye">Payés (soldés)</option>
                <option value="impaye">Impayés</option>
              </select>
            </div>

            {/* Année scolaire */}
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-white/60 mb-1">
                Année scolaire
              </label>
              <input
                type="text"
                value={anneeScolaire}
                onChange={(e) => setAnneeScolaire(e.target.value)}
                placeholder="ex: 2024-2025"
                className="w-full rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-[#0A2540] text-sm text-[#0A2540] dark:text-white px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#FF6200]/40"
              />
            </div>

            {/* Date début */}
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-white/60 mb-1">
                Date début
              </label>
              <input
                type="date"
                value={dateDebut}
                onChange={(e) => setDateDebut(e.target.value)}
                className="w-full rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-[#0A2540] text-sm text-[#0A2540] dark:text-white px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#FF6200]/40"
              />
            </div>

            {/* Date fin */}
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-white/60 mb-1">
                Date fin
              </label>
              <input
                type="date"
                value={dateFin}
                onChange={(e) => setDateFin(e.target.value)}
                className="w-full rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-[#0A2540] text-sm text-[#0A2540] dark:text-white px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#FF6200]/40"
              />
            </div>

            {/* Recherche client */}
            <div className="relative">
              <label className="block text-xs font-medium text-gray-600 dark:text-white/60 mb-1">
                Client
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
                <input
                  type="text"
                  value={clientSearch}
                  onChange={(e) => handleClientSearchChange(e.target.value)}
                  onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                  placeholder="Rechercher un client…"
                  className="w-full pl-8 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-[#0A2540] text-sm text-[#0A2540] dark:text-white px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#FF6200]/40"
                />
              </div>
              {showSuggestions && clientSuggestions.length > 0 && (
                <div className="absolute z-50 mt-1 w-full bg-white dark:bg-[#0A2540] border border-gray-200 dark:border-white/10 rounded-lg shadow-lg overflow-hidden">
                  {clientSuggestions.map((c) => (
                    <button
                      key={c.client_id}
                      onMouseDown={() => selectClient(c)}
                      className="w-full text-left px-3 py-2 text-sm text-[#0A2540] dark:text-white hover:bg-[#E8F0FB] dark:hover:bg-white/10 transition"
                    >
                      <span className="font-medium">{c.nom}</span>
                      {c.ville && <span className="text-gray-400 ml-2 text-xs">{c.ville}</span>}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Ville */}
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-white/60 mb-1">
                Ville / Zone
              </label>
              <input
                type="text"
                value={villeFilter}
                onChange={(e) => setVilleFilter(e.target.value)}
                placeholder="Abidjan, Bouaké…"
                className="w-full rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-[#0A2540] text-sm text-[#0A2540] dark:text-white px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#FF6200]/40"
              />
            </div>

            {/* Type client */}
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-white/60 mb-1">
                Type client
              </label>
              <select
                value={typeClient}
                onChange={(e) => setTypeClient(e.target.value)}
                className="w-full rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-[#0A2540] text-sm text-[#0A2540] dark:text-white px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#FF6200]/40"
              >
                <option value="">Tous les types</option>
                {TYPE_CLIENTS.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>

            {/* Représentant */}
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-white/60 mb-1">
                Commercial / Représentant
              </label>
              <input
                type="text"
                value={representant}
                onChange={(e) => setRepresentant(e.target.value)}
                placeholder="Nom du représentant…"
                className="w-full rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-[#0A2540] text-sm text-[#0A2540] dark:text-white px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#FF6200]/40"
              />
            </div>
          </div>
        </div>

        {/* ── Barre d'actions ── */}
        <div className="flex flex-wrap items-center gap-2 mb-6">

          {/* Aperçu */}
          <button
            onClick={handleApercu}
            disabled={loadingPreview || exporting}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-[#0A2540] hover:bg-[#1B4F8A] text-white text-sm font-semibold shadow transition disabled:opacity-50"
          >
            {loadingPreview
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <BarChart2 className="w-4 h-4" />
            }
            Aperçu
          </button>

          {/* PDF */}
          <button
            onClick={handleExportPdf}
            disabled={exporting || loadingPreview}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-[#DC2626] hover:bg-[#B91C1C] text-white text-sm font-semibold shadow transition disabled:opacity-50"
          >
            {exporting
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <FileText className="w-4 h-4" />
            }
            PDF
          </button>

          {/* Imprimer */}
          <button
            onClick={handlePrint}
            disabled={exporting || loadingPreview}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-gray-700 hover:bg-gray-800 text-white text-sm font-semibold shadow transition disabled:opacity-50"
          >
            {exporting
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Printer className="w-4 h-4" />
            }
            Imprimer
          </button>

          {/* Reset filtres */}
          <button
            onClick={() => {
              setFiltre("tous"); setAnneeScolaire(""); setDateDebut(""); setDateFin("");
              setClientSearch(""); setSelectedClientId(""); setVilleFilter("");
              setTypeClient(""); setRepresentant(""); setPreviewData(null);
            }}
            className="inline-flex items-center gap-1.5 px-3 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 text-gray-500 dark:text-white/50 text-sm hover:bg-gray-50 dark:hover:bg-white/5 transition ml-auto"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Réinitialiser
          </button>
        </div>

        {/* ── Zone aperçu ── */}
        {loadingPreview && (
          <div className="flex items-center justify-center py-20 text-[#1B4F8A] dark:text-blue-300">
            <Loader2 className="w-7 h-7 animate-spin mr-3" />
            <span className="text-sm font-medium">Chargement des données…</span>
          </div>
        )}

        {previewError && (
          <div className="flex items-start gap-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-500/30 rounded-xl p-4 mb-4">
            <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-sm font-semibold text-red-700 dark:text-red-400">Erreur de chargement</p>
              <p className="text-xs text-red-600 dark:text-red-300 mt-0.5">{previewError}</p>
            </div>
          </div>
        )}

        {previewData && !loadingPreview && (
          <PreviewSection
            data={previewData}
            expandedClients={expandedClients}
            toggleClient={toggleClient}
          />
        )}

        {!previewData && !loadingPreview && !previewError && (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-16 h-16 rounded-2xl bg-[#E8F0FB] dark:bg-[#1B4F8A]/20 flex items-center justify-center mb-4">
              <FileText className="w-8 h-8 text-[#1B4F8A] dark:text-blue-300" />
            </div>
            <p className="text-sm font-semibold text-[#0A2540] dark:text-white/80">
              Paramétrez vos filtres et cliquez sur <strong>Aperçu</strong>
            </p>
            <p className="text-xs text-gray-400 dark:text-white/40 mt-1 max-w-xs">
              Le tableau récapitulatif apparaîtra ici. Vous pourrez ensuite exporter en PDF, Excel ou imprimer.
            </p>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

// ─────────────────────────────────────────────────────────────────
// Sous-composant : Preview tableau
// ─────────────────────────────────────────────────────────────────
function PreviewSection({ data, expandedClients, toggleClient }) {
  const { clients_data = [], resume = {} } = data;

  if (clients_data.length === 0) {
    return (
      <div className="text-center py-16">
        <p className="text-sm text-gray-500 dark:text-white/50">
          Aucune facture trouvée pour les critères sélectionnés.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">

      {/* KPI résumé */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-3 mb-4">
        {[
          { label: "Clients",       value: resume.nb_clients,   isMoney: false },
          { label: "Factures",      value: resume.nb_factures,  isMoney: false },
          { label: "Total TTC",     value: resume.total_vente,  isMoney: true  },
          { label: "Remises",       value: resume.total_remise, isMoney: true  },
          { label: "Total HT",      value: resume.total_ht,     isMoney: true  },
          { label: "Réglé",         value: resume.total_regle,  isMoney: true  },
          { label: "Solde restant", value: resume.total_solde,  isMoney: true, accent: resume.total_solde > 0 ? "red" : "green" },
        ].map((k) => (
          <div key={k.label} className="bg-white dark:bg-[#0b1e30] border border-gray-200 dark:border-white/10 rounded-xl p-3 text-center shadow-sm">
            <p className="text-[10px] uppercase tracking-wide text-gray-400 dark:text-white/40 font-medium">{k.label}</p>
            <p className={`text-sm font-bold mt-0.5 ${
              k.accent === "red"   ? "text-red-600" :
              k.accent === "green" ? "text-green-600" :
              "text-[#0A2540] dark:text-white"
            }`}>
              {k.isMoney
                ? new Intl.NumberFormat("fr-FR", { minimumFractionDigits: 0 }).format(k.value || 0)
                : (k.value || 0)
              }
              {k.isMoney && <span className="text-[9px] font-normal text-gray-400 ml-0.5">FCFA</span>}
            </p>
          </div>
        ))}
      </div>

      {/* Tableau clients */}
      <div className="space-y-2">
        {clients_data.map((entry) => {
          const client = entry.client;
          const factures = entry.factures;
          const cid = client.client_id;
          const expanded = expandedClients[cid] !== false; // ouvert par défaut
          const totalSolde = factures.reduce((s, f) => s + parseFloat(f.montant_restant || 0), 0);
          const totalTTC   = factures.reduce((s, f) => s + parseFloat(f.montant_ttc || 0), 0);
          const totalRegle = factures.reduce((s, f) => s + parseFloat(f.montant_regle || 0), 0);

          return (
            <div key={cid} className="bg-white dark:bg-[#0b1e30] border border-gray-200 dark:border-white/10 rounded-xl overflow-hidden shadow-sm">

              {/* En-tête client (cliquable) */}
              <button
                onClick={() => toggleClient(cid)}
                className="w-full flex items-center justify-between px-4 py-3 bg-[#EFF6FF] dark:bg-[#1B4F8A]/20 hover:bg-[#DBEAFE] dark:hover:bg-[#1B4F8A]/30 transition text-left"
              >
                <div className="flex items-center gap-3 min-w-0">
                  {expanded
                    ? <ChevronDown className="w-4 h-4 text-[#1B4F8A] dark:text-blue-300 flex-shrink-0" />
                    : <ChevronRight className="w-4 h-4 text-[#1B4F8A] dark:text-blue-300 flex-shrink-0" />
                  }
                  <div className="min-w-0">
                    <p className="text-sm font-bold text-[#0A2540] dark:text-white truncate">{client.nom || "—"}</p>
                    <div className="flex items-center gap-3 mt-0.5 flex-wrap">
                      {client.ville && (
                        <span className="flex items-center gap-0.5 text-[11px] text-gray-400">
                          <MapPin className="w-3 h-3" />{client.ville}
                        </span>
                      )}
                      {client.type_client && (
                        <span className="flex items-center gap-0.5 text-[11px] text-gray-400">
                          <Tag className="w-3 h-3" />{client.type_client}
                        </span>
                      )}
                      {client.representant && (
                        <span className="flex items-center gap-0.5 text-[11px] text-gray-400">
                          <User className="w-3 h-3" />{client.representant}
                        </span>
                      )}
                      {client.telephone && (
                        <span className="flex items-center gap-0.5 text-[11px] text-gray-400">
                          <Phone className="w-3 h-3" />{client.telephone}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4 flex-shrink-0 ml-3">
                  <div className="text-right hidden sm:block">
                    <p className="text-[10px] text-gray-400">TTC</p>
                    <p className="text-xs font-semibold text-[#0A2540] dark:text-white">{fmt(totalTTC)}</p>
                  </div>
                  <div className="text-right hidden sm:block">
                    <p className="text-[10px] text-gray-400">Réglé</p>
                    <p className="text-xs font-semibold text-green-600">{fmt(totalRegle)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] text-gray-400">Solde</p>
                    <p className={`text-xs font-bold ${totalSolde > 0 ? "text-red-600" : "text-green-600"}`}>
                      {fmt(totalSolde)}
                    </p>
                  </div>
                  <span className="text-[10px] text-gray-400 bg-gray-100 dark:bg-white/10 rounded px-1.5 py-0.5">
                    {factures.length} fact.
                  </span>
                </div>
              </button>

              {/* Tableau des factures */}
              {expanded && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="bg-gray-50 dark:bg-white/5">
                        {["Référence", "Date", "Montant TTC", "Remise", "Montant HT", "Réglé", "Solde", "Statut"].map((h) => (
                          <th key={h} className="px-3 py-2 text-left font-semibold text-gray-500 dark:text-white/50 whitespace-nowrap border-b border-gray-100 dark:border-white/5">
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {factures.map((f, fi) => {
                        const solde = parseFloat(f.montant_restant || 0);
                        return (
                          <tr key={f.facture_id || fi}
                            className={fi % 2 === 0 ? "bg-white dark:bg-transparent" : "bg-gray-50/60 dark:bg-white/[0.02]"}
                          >
                            <td className="px-3 py-2 font-mono text-[11px] text-[#0A2540] dark:text-white/80 border-b border-gray-50 dark:border-white/5">
                              {f.reference || "—"}
                            </td>
                            <td className="px-3 py-2 text-gray-500 dark:text-white/50 border-b border-gray-50 dark:border-white/5 whitespace-nowrap">
                              {fmtDate(f.date_facture)}
                            </td>
                            <td className="px-3 py-2 text-right font-medium text-[#0A2540] dark:text-white border-b border-gray-50 dark:border-white/5">
                              {fmt(f.montant_ttc)}
                            </td>
                            <td className="px-3 py-2 text-right text-orange-600 border-b border-gray-50 dark:border-white/5">
                              {fmt(f.remise_globale)}
                            </td>
                            <td className="px-3 py-2 text-right text-gray-600 dark:text-white/60 border-b border-gray-50 dark:border-white/5">
                              {fmt(f.montant_ht)}
                            </td>
                            <td className="px-3 py-2 text-right text-green-600 font-medium border-b border-gray-50 dark:border-white/5">
                              {fmt(f.montant_regle)}
                            </td>
                            <td className={`px-3 py-2 text-right font-bold border-b border-gray-50 dark:border-white/5 ${solde > 0 ? "text-red-600" : "text-green-600"}`}>
                              {fmt(solde)}
                            </td>
                            <td className="px-3 py-2 border-b border-gray-50 dark:border-white/5">
                              {statutBadge(f.statut)}
                            </td>
                          </tr>
                        );
                      })}
                      {/* Ligne sous-total */}
                      <tr className="bg-[#EFF6FF] dark:bg-[#1B4F8A]/10 font-semibold text-[#1B4F8A] dark:text-blue-300">
                        <td colSpan={2} className="px-3 py-2 text-[11px]">
                          Sous-total — {factures.length} facture{factures.length > 1 ? "s" : ""}
                        </td>
                        <td className="px-3 py-2 text-right">{fmt(totalTTC)}</td>
                        <td className="px-3 py-2 text-right text-orange-500">
                          {fmt(factures.reduce((s, f) => s + parseFloat(f.remise_globale || 0), 0))}
                        </td>
                        <td className="px-3 py-2 text-right">
                          {fmt(factures.reduce((s, f) => s + parseFloat(f.montant_ht || 0), 0))}
                        </td>
                        <td className="px-3 py-2 text-right text-green-600">
                          {fmt(totalRegle)}
                        </td>
                        <td className={`px-3 py-2 text-right font-bold ${totalSolde > 0 ? "text-red-600" : "text-green-600"}`}>
                          {fmt(totalSolde)}
                        </td>
                        <td className="px-3 py-2" />
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Total général */}
      <div className="flex items-center justify-between bg-[#0A2540] text-white rounded-xl px-5 py-3 mt-2 shadow">
        <p className="text-sm font-bold">
          TOTAL GÉNÉRAL — {resume.nb_clients} client{resume.nb_clients > 1 ? "s" : ""} · {resume.nb_factures} facture{resume.nb_factures > 1 ? "s" : ""}
        </p>
        <div className="flex items-center gap-6 flex-wrap">
          <div className="text-right">
            <p className="text-[10px] text-white/50">TTC</p>
            <p className="text-xs font-bold">{fmt(resume.total_vente)}</p>
          </div>
          <div className="text-right">
            <p className="text-[10px] text-white/50">Réglé</p>
            <p className="text-xs font-bold text-green-400">{fmt(resume.total_regle)}</p>
          </div>
          <div className="text-right">
            <p className="text-[10px] text-white/50">Solde restant</p>
            <p className={`text-sm font-bold ${resume.total_solde > 0 ? "text-red-400" : "text-green-400"}`}>
              {fmt(resume.total_solde)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
