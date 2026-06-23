/**
 * ClientDetail.jsx — Fiche client complète ERP FABS-CI
 * 8 onglets: Info · Commandes · Proformas · Factures · BL · Paiements · Compte · Historique
 * Actions rapides · Statut enrichi · 8 KPIs
 */
import { useEffect, useState, useCallback, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft, Pencil, PowerOff, Phone, Mail, MapPin, Wallet, FileText,
  ShoppingCart, CreditCard, History, AlertCircle, Calendar, TrendingUp,
  Package, Truck, ReceiptText, BookOpen, PlusCircle, ExternalLink,
  CheckCircle2, Clock, XCircle, AlertTriangle, Building2, User, Hash,
  Send, RefreshCw, ChevronRight,
} from "lucide-react";
import { toast } from "sonner";

import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";
import ClientFormDialog from "../components/clients/ClientFormDialog";
import { getClient, disableClient, TYPE_COLOR } from "../services/clientsApi";
import { getCommandes } from "../services/commandesApi";
import { getFactures } from "../services/facturesApi";
import { getPaiements, createPaiement } from "../services/paiementsApi";
import { listProformas, createProforma } from "../services/proformasApi";
import { getBonsLivraison } from "../services/bonsLivraisonApi";
import { formatFCFA } from "../utils/format";
import { useAuth } from "../hooks/useAuth";

// ─────────────────────────────────────────────
// TABS DEFINITION
// ─────────────────────────────────────────────
const TABS = [
  { key: "info",       label: "Informations",  icon: FileText },
  { key: "commandes",  label: "Commandes",     icon: ShoppingCart },
  { key: "proformas",  label: "Proformas",     icon: ReceiptText },
  { key: "factures",   label: "Factures",      icon: FileText },
  { key: "bl",         label: "Bons de livraison", icon: Truck },
  { key: "paiements",  label: "Paiements",     icon: CreditCard },
  { key: "compte",     label: "Compte",        icon: BookOpen },
  { key: "historique", label: "Historique",    icon: History },
];

// ─────────────────────────────────────────────
// STATUT ENRICHI
// ─────────────────────────────────────────────
function computeClientStatut(client, stats) {
  if (!client.actif) return { label: "Inactif", color: "bg-gray-400", text: "text-gray-700 dark:text-white/90" };
  if (!stats) return { label: "Actif", color: "bg-green-500", text: "text-green-700" };

  const { encours, plafond, last30days, impaye } = stats;
  const tauxUtilisation = plafond > 0 ? encours / plafond : 0;

  if (impaye > 0) return { label: "Impayé", color: "bg-red-500", text: "text-red-700" };
  if (tauxUtilisation > 0.9) return { label: "Plafond critique", color: "bg-orange-500", text: "text-orange-700" };
  if (tauxUtilisation > 0.7) return { label: "Encours élevé", color: "bg-amber-500", text: "text-amber-700" };
  if (last30days > 0) return { label: "Actif récent", color: "bg-emerald-500", text: "text-emerald-700" };
  return { label: "Actif", color: "bg-green-500", text: "text-green-700" };
}

// ─────────────────────────────────────────────
// UTILS
// ─────────────────────────────────────────────
const fmt = formatFCFA;
const fmtDate = (s) => s ? new Date(s).toLocaleDateString("fr-FR") : "—";
const fmtDateTime = (s) => s ? new Date(s).toLocaleString("fr-FR") : "—";
const ago = (s) => {
  if (!s) return "—";
  const diff = Date.now() - new Date(s).getTime();
  const days = Math.floor(diff / 86400000);
  if (days === 0) return "Aujourd'hui";
  if (days === 1) return "Hier";
  if (days < 30) return `Il y a ${days} j`;
  if (days < 365) return `Il y a ${Math.floor(days / 30)} mois`;
  return `Il y a ${Math.floor(days / 365)} an(s)`;
};

// ─────────────────────────────────────────────
// STATUT BADGES (commandes / factures / BL)
// ─────────────────────────────────────────────
const CMD_STATUT = {
  brouillon:       { label: "Brouillon",  color: "bg-gray-200 dark:bg-white/10 text-gray-700 dark:text-white/90" },
  en_attente:      { label: "En attente", color: "bg-amber-100 text-amber-700" },
  validee:         { label: "Validée",    color: "bg-blue-100 text-blue-700" },
  preparee:        { label: "Préparée",   color: "bg-indigo-100 text-indigo-700" },
  livree:          { label: "Livrée",     color: "bg-green-100 text-green-700" },
  annulee:         { label: "Annulée",    color: "bg-red-100 text-red-700" },
};
const FAC_STATUT = {
  brouillon:       { label: "Brouillon",  color: "bg-gray-200 dark:bg-white/10 text-gray-700 dark:text-white/90" },
  emise:           { label: "Émise",      color: "bg-blue-100 text-blue-700" },
  partiellement_payee: { label: "Partielle", color: "bg-amber-100 text-amber-700" },
  payee:           { label: "Payée",      color: "bg-green-100 text-green-700" },
  avoir:           { label: "Avoir",      color: "bg-purple-100 text-purple-700" },
  annulee:         { label: "Annulée",    color: "bg-red-100 text-red-700" },
};
const BL_STATUT = {
  en_preparation:  { label: "En préparation", color: "bg-amber-100 text-amber-700" },
  expedie:         { label: "Expédié",    color: "bg-blue-100 text-blue-700" },
  livre:           { label: "Livré",      color: "bg-green-100 text-green-700" },
  annule:          { label: "Annulé",     color: "bg-red-100 text-red-700" },
};
const PRO_STATUT = {
  generee:         { label: "Générée",    color: "bg-blue-100 text-blue-700" },
  envoyee:         { label: "Envoyée",    color: "bg-indigo-100 text-indigo-700" },
  acceptee:        { label: "Acceptée",   color: "bg-green-100 text-green-700" },
  refusee:         { label: "Refusée",    color: "bg-red-100 text-red-700" },
  expiree:         { label: "Expirée",    color: "bg-gray-200 dark:bg-white/10 text-gray-600 dark:text-white/70" },
};

function StatusBadge({ map, value }) {
  const conf = map[value] || { label: value, color: "bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-white/70" };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold ${conf.color}`}>
      {conf.label}
    </span>
  );
}

// ─────────────────────────────────────────────
// MAIN COMPONENT
// ─────────────────────────────────────────────
export default function ClientDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { role } = useAuth();
  const canWrite = ["super_admin", "directeur_general", "directeur_commercial", "secretariat"].includes(role);
  // Bouton commander : tous les rôles ayant accès au module commandes
  const canCommande = ["super_admin", "directeur_general", "directeur_commercial", "secretariat",
    "assistante", "gestionnaire_stock", "responsable_magasinier", "comptable"].includes(role);

  const [client, setClient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState("info");
  const [edit, setEdit] = useState(false);
  const [paiementDialog, setPaiementDialog] = useState(false);
  const [creatingProforma, setCreatingProforma] = useState(false);

  // Tab data cache — lazy load, loaded once
  const loaded = useRef({});
  const [tabData, setTabData] = useState({});
  const [tabLoading, setTabLoading] = useState({});
  // tabDataRef mirrors tabData for use in callbacks without causing re-renders
  const tabDataRef = useRef({});

  // Derived stats for statut enrichi
  const [clientStats, setClientStats] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    loaded.current = {};
    tabDataRef.current = {};
    setTabData({});
    try {
      const r = await getClient(id);
      setClient(r);
    } catch (e) {
      setError(e?.response?.data?.detail || "Client introuvable");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { refresh(); }, [refresh]);

  // Lazy load tab data on first activation
  const computeStats = useCallback((factures, paiements) => {
    if (!factures || !paiements) return;
    const fList = Array.isArray(factures) ? factures : (factures?.items || []);
    const pList = Array.isArray(paiements) ? paiements : [];
    const now = Date.now();
    const ms30 = 30 * 86400000;

    const encours = fList.reduce((s, f) => {
      if (["emise", "partiellement_payee"].includes(f.statut)) {
        return s + (f.montant_ttc - (f.montant_paye || 0));
      }
      return s;
    }, 0);
    const impaye = fList.filter(f => f.statut === "emise" && f.date_echeance && new Date(f.date_echeance) < now).length;
    const last30days = pList.filter(p => p.date_paiement && (now - new Date(p.date_paiement).getTime()) < ms30).length;

    setClientStats({ encours, impaye, last30days, plafond: client?.plafond_credit || 0 });
  }, [client]);

  const loadTab = useCallback(async (key) => {
    if (loaded.current[key]) return;
    loaded.current[key] = true;
    setTabLoading((prev) => ({ ...prev, [key]: true }));
    try {
      let data = null;
      if (key === "commandes") {
        data = await getCommandes({ client_id: id, limit: 100 });
      } else if (key === "factures") {
        data = await getFactures({ client_id: id, limit: 100 });
      } else if (key === "paiements") {
        data = await getPaiements({ client_id: id, limit: 100 });
      } else if (key === "proformas") {
        data = await listProformas({ client_id: id, limit: 100 });
      } else if (key === "bl") {
        data = await getBonsLivraison({ client_id: id, limit: 100 });
      } else if (key === "compte") {
        // Compute from factures + paiements (limit max 200 côté backend)
        const [facs, pays] = await Promise.all([
          getFactures({ client_id: id, limit: 200 }),
          getPaiements({ client_id: id, limit: 200 }),
        ]);
        // Les deux endpoints retournent une liste directe
        const facsList = Array.isArray(facs) ? facs : (facs?.items || []);
        const paysList = Array.isArray(pays) ? pays : (pays?.items || []);
        data = { factures: facsList, paiements: paysList };
      } else if (key === "historique") {
        const axios = (await import("axios")).default;
        const resp = await axios.get(`/api/clients/${id}/audit-logs?limit=50`).catch(() => ({ data: [] }));
        data = Array.isArray(resp.data) ? resp.data : [];
      }
      setTabData((prev) => {
        const next = { ...prev, [key]: data };
        tabDataRef.current = next;
        return next;
      });

      // Compute stats for statut enrichi once we have factures + paiements
      if (key === "factures" || key === "paiements") {
        const current = tabDataRef.current;
        computeStats(
          key === "factures" ? data : current["factures"],
          key === "paiements" ? data : current["paiements"]
        );
      }
    } catch (e) {
      toast.error(`Erreur chargement ${key}`);
      loaded.current[key] = false;
    } finally {
      setTabLoading((prev) => ({ ...prev, [key]: false }));
    }
  }, [id, computeStats]);

  useEffect(() => {
    if (tab !== "info") {
      loadTab(tab);
    }
    // Also preload factures for KPI computation
    if (tab === "commandes" && !loaded.current["factures"]) {
      loadTab("factures");
      loadTab("paiements");
    }
  }, [tab, loadTab]);

  const handleNouvelleProforma = async () => {
    if (creatingProforma) return;
    setCreatingProforma(true);
    try {
      const p = await createProforma({
        client_id: client.client_id,
        client_nom: client.nom,
        statut: "brouillon",
        lignes: [],
      });
      toast.success("Proforma créée — redirection...");
      navigate(`/proformas/${p.proforma_id}`);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erreur création proforma");
    } finally {
      setCreatingProforma(false);
    }
  };

  const handleDisable = async () => {
    if (!window.confirm(`Désactiver "${client.nom}" ?`)) return;
    try {
      const updated = await disableClient(client.client_id);
      toast.success(`${updated.nom} désactivé`);
      setClient(updated);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Échec");
    }
  };

  // ── Loading / Error states ──
  if (loading) return (
    <DashboardLayout>
      <div className="p-8 text-sm text-gray-500 dark:text-white/50">Chargement…</div>
    </DashboardLayout>
  );

  if (error || !client) return (
    <DashboardLayout>
      <div className="bg-red-50 border border-[#C62828]/30 text-[#C62828] rounded-lg p-4 text-sm flex items-center gap-2 max-w-2xl">
        <AlertCircle className="w-4 h-4" />
        {error || "Client introuvable"}
        <button onClick={() => navigate("/clients")} className="ml-auto text-xs font-semibold underline">
          ← Retour
        </button>
      </div>
    </DashboardLayout>
  );

  // ── Derived values ──
  const type = TYPE_COLOR[client.type_client] || TYPE_COLOR.particulier;
  const statut = computeClientStatut(client, clientStats);
  const encours = clientStats?.encours ?? client.solde ?? 0;
  const plafond = client.plafond_credit ?? 0;
  const tauxCredit = plafond > 0 ? Math.min(100, Math.round((encours / plafond) * 100)) : 0;

  // Compute KPI counts from loaded tab data
  const cmdCount = (tabData.commandes?.items || tabData.commandes || []).length;
  const facCount = (Array.isArray(tabData.factures) ? tabData.factures : tabData.factures?.items || []).length;
  const payCount = (Array.isArray(tabData.paiements) ? tabData.paiements : []).length;
  const proCount = (tabData.proformas?.items || tabData.proformas || []).length;
  const blCount  = (Array.isArray(tabData.bl) ? tabData.bl : []).length;

  return (
    <DashboardLayout>
      <div data-testid="client-detail-page" className="max-w-6xl mx-auto space-y-5">

        {/* Back */}
        <button
          data-testid="client-detail-back"
          onClick={() => navigate("/clients")}
          className="inline-flex items-center gap-1.5 text-xs text-gray-500 dark:text-white/50 hover:text-[#FF6200] transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Liste des clients
        </button>

        {/* ── HEADER CARD ── */}
        <div className="bg-white dark:bg-white dark:bg-[#0b1e30]/5 rounded-xl border border-gray-200 dark:border-white/10 p-6 shadow-sm">
          <div className="flex flex-wrap items-start gap-4 justify-between">
            {/* Identity */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center flex-wrap gap-2">
                <span
                  className="inline-flex items-center text-[10px] uppercase tracking-wider font-bold px-2 py-0.5 rounded"
                  style={{ background: type.bg, color: type.color }}
                >
                  {type.label}
                </span>
                <span className="font-mono text-xs text-gray-500 dark:text-white/50">
                  {client.reference}
                </span>
                {/* Statut enrichi badge */}
                <span className={`inline-flex items-center text-[10px] uppercase tracking-wider font-bold px-2 py-0.5 rounded text-white ${statut.color}`}>
                  {statut.label}
                </span>
                {!client.actif && (
                  <span className="text-[10px] uppercase tracking-wider bg-gray-200 dark:bg-white dark:bg-[#0b1e30]/10 text-gray-500 dark:text-white/50 px-2 py-0.5 rounded">
                    Désactivé
                  </span>
                )}
              </div>
              <h1 className="text-3xl font-bold tracking-tight text-[#0A2540] dark:text-white mt-2">
                {client.nom}
              </h1>
              <div className="flex flex-wrap gap-4 mt-2 text-sm text-gray-600 dark:text-white/70">
                {client.representant && (
                  <span className="inline-flex items-center gap-1.5">
                    <User className="w-3.5 h-3.5 text-[#FF6200]" />
                    <span className="font-medium text-[#0A2540] dark:text-white/90">{client.representant}</span>
                  </span>
                )}
                {client.telephone && (
                  <span className="inline-flex items-center gap-1.5">
                    <Phone className="w-3.5 h-3.5 text-[#FF6200]" />
                    {client.telephone}
                  </span>
                )}
                {client.email && (
                  <span className="inline-flex items-center gap-1.5">
                    <Mail className="w-3.5 h-3.5 text-[#FF6200]" />
                    {client.email}
                  </span>
                )}
                {client.ville && (
                  <span className="inline-flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-[#FF6200]" />
                    {client.ville}
                  </span>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="flex flex-wrap gap-2">
              {canCommande && client.actif && (
                <button
                  onClick={() => navigate(`/commandes/nouvelle?client_id=${client.client_id}`)}
                  className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold text-white bg-blue-600 hover:bg-[#E55900]"
                  data-testid="btn-nouvelle-commande"
                >
                  <PlusCircle className="w-3.5 h-3.5" />
                  Commander
                </button>
              )}
              {canWrite && client.actif && (
                <>
                  <button
                    data-testid="client-detail-edit"
                    onClick={() => setEdit(true)}
                    className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold text-[#0A2540] dark:text-white bg-gray-100 dark:bg-white dark:bg-[#0b1e30]/10 hover:bg-gray-200 dark:hover:bg-white dark:bg-[#0b1e30]/20"
                  >
                    <Pencil className="w-3.5 h-3.5" />
                    Modifier
                  </button>
                  <button
                    data-testid="client-detail-disable"
                    onClick={handleDisable}
                    className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold text-[#C62828] bg-[#C62828]/10 hover:bg-[#C62828]/20"
                  >
                    <PowerOff className="w-3.5 h-3.5" />
                    Désactiver
                  </button>
                </>
              )}
              <button
                onClick={refresh}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold text-gray-500 dark:text-white/50 bg-gray-100 dark:bg-white dark:bg-[#0b1e30]/10 hover:bg-gray-200 dark:hover:bg-white dark:bg-[#0b1e30]/20"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* ── KPIs (8) ── */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-6 border-t border-gray-100 dark:border-white/10">
            <KPI icon={Wallet} accent="#C62828" label="Encours" value={fmt(encours)} />
            <KPI icon={CreditCard} accent="#2E7D32" label="Plafond crédit" value={fmt(plafond)} />
            <KPI icon={TrendingUp} accent="#1565C0" label="Utilisation crédit"
              value={
                <span>
                  {tauxCredit}%
                  <div className="mt-1 w-full bg-gray-200 dark:bg-white dark:bg-[#0b1e30]/10 rounded-full h-1">
                    <div
                      className={`h-1 rounded-full ${tauxCredit > 90 ? "bg-red-500" : tauxCredit > 70 ? "bg-amber-500" : "bg-green-500"}`}
                      style={{ width: `${tauxCredit}%` }}
                    />
                  </div>
                </span>
              }
            />
            <KPI icon={Calendar} accent="#7B1FA2" label="Client depuis" value={ago(client.created_at)} />
            <KPI icon={ShoppingCart} accent="#0A2540" label="Commandes" value={cmdCount || "—"} />
            <KPI icon={FileText} accent="#0277BD" label="Factures" value={facCount || "—"} />
            <KPI icon={CreditCard} accent="#00695C" label="Paiements" value={payCount || "—"} />
            <KPI icon={Truck} accent="#E65100" label="Bons de livraison" value={blCount || "—"} />
          </div>

          {/* ── Quick actions ── */}
          {canWrite && client.actif && (
            <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-gray-100 dark:border-white/10">
              <QuickAction icon={CreditCard} label="Enregistrer paiement" onClick={() => setPaiementDialog(true)} />
            </div>
          )}
        </div>

        {/* ── TABS ── */}
        <div>
          <div data-testid="client-detail-tabs" className="flex flex-wrap gap-0.5 border-b border-gray-200 dark:border-white/10">
            {TABS.map(({ key, label, icon: Icon }) => {
              const active = key === tab;
              return (
                <button
                  key={key}
                  data-testid={`client-detail-tab-${key}`}
                  onClick={() => setTab(key)}
                  className={`inline-flex items-center gap-1.5 px-3 py-2.5 text-sm font-semibold border-b-2 transition-colors ${
                    active
                      ? "border-[#FF6200] text-[#FF6200]"
                      : "border-transparent text-gray-500 dark:text-white/60 hover:text-[#0A2540] dark:hover:text-white"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {label}
                </button>
              );
            })}
          </div>

          <div className="mt-4">
            {tab === "info" && <InfoTab client={client} />}
            {tab === "commandes" && (
              <CommandesTab
                items={tabData.commandes}
                loading={tabLoading.commandes}
                onGo={(id) => navigate(`/commandes/${id}`)}
                client={client}
                canWrite={canCommande}
                navigate={navigate}
              />
            )}
            {tab === "proformas" && (
              <ProformasTab
                items={tabData.proformas}
                loading={tabLoading.proformas}
                onGo={(id) => navigate(`/proformas/${id}`)}
              />
            )}
            {tab === "factures" && (
              <FacturesTab
                items={tabData.factures}
                loading={tabLoading.factures}
                onGo={(id) => navigate(`/factures/${id}`)}
              />
            )}
            {tab === "bl" && (
              <BLTab
                items={tabData.bl}
                loading={tabLoading.bl}
                onGo={(id) => navigate(`/bons-livraison/${id}`)}
              />
            )}
            {tab === "paiements" && (
              <PaiementsTab
                items={tabData.paiements}
                loading={tabLoading.paiements}
                onGo={(id) => navigate(`/paiements/${id}`)}
              />
            )}
            {tab === "compte" && (
              <CompteTab
                data={tabData.compte}
                loading={tabLoading.compte}
                client={client}
              />
            )}
            {tab === "historique" && (
              <HistoriqueTab
                client={client}
                data={tabData.historique}
                loading={tabLoading.historique}
              />
            )}
          </div>
        </div>
      </div>

      <ClientFormDialog
        open={edit}
        onClose={() => setEdit(false)}
        client={client}
        onSaved={(saved) => { setClient(saved); setEdit(false); }}
      />
      {paiementDialog && client && (
        <PaiementQuickDialog
          client={client}
          onClose={() => setPaiementDialog(false)}
          onCreated={() => { setPaiementDialog(false); refresh(); toast.success("Paiement enregistré"); }}
        />
      )}
    </DashboardLayout>
  );
}

// ─────────────────────────────────────────────
// SHARED UI COMPONENTS
// ─────────────────────────────────────────────
function KPI({ icon: Icon, accent, label, value }) {
  return (
    <div className="flex items-start gap-3">
      <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: `${accent}18` }}>
        <Icon className="w-4.5 h-4.5" style={{ color: accent }} />
      </div>
      <div className="min-w-0">
        <p className="text-[10px] uppercase tracking-wider text-gray-500 dark:text-white/50">{label}</p>
        <div className="text-sm font-bold text-[#0A2540] dark:text-white mt-0.5">{value}</div>
      </div>
    </div>
  );
}

function QuickAction({ icon: Icon, label, onClick, disabled }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-[#0A2540] dark:text-white/80 bg-gray-50 dark:bg-white dark:bg-[#0b1e30]/5 border border-gray-200 dark:border-white/10 hover:bg-blue-600/5 hover:border-[#FF6200]/30 hover:text-[#FF6200] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <Icon className="w-3.5 h-3.5" />
      {label}
    </button>
  );
}

// ─────────────────────────────────────────────
// PAIEMENT QUICK DIALOG
// ─────────────────────────────────────────────
function PaiementQuickDialog({ client, onClose, onCreated }) {
  const [form, setForm] = useState({
    montant_total: "",
    mode_paiement: "especes",
    reference: "",
    notes: "",
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.montant_total || isNaN(Number(form.montant_total))) {
      toast.error("Montant invalide"); return;
    }
    setLoading(true);
    try {
      await createPaiement({
        client_id: client.client_id,
        client_nom: client.nom,
        montant_total: Number(form.montant_total),
        mode_paiement: form.mode_paiement,
        reference: form.reference || undefined,
        notes: form.notes || undefined,
      });
      onCreated();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erreur enregistrement paiement");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="bg-white dark:bg-[#0A2540] rounded-2xl shadow-2xl w-full max-w-md p-6 border border-gray-100 dark:border-white/10">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold text-[#0A2540] dark:text-white">Enregistrer un paiement</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-white text-xl leading-none">×</button>
        </div>
        <p className="text-sm text-gray-500 dark:text-white/60 mb-4">Client : <span className="font-semibold text-[#0A2540] dark:text-white">{client.nom}</span></p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-gray-500 dark:text-white/60 mb-1 block">Montant (FCFA) *</label>
            <input
              type="number" min="1" required
              value={form.montant_total}
              onChange={e => setForm({ ...form, montant_total: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-white dark:bg-[#0b1e30]/5 text-[#0A2540] dark:text-white text-sm focus:outline-none focus:border-[#1B4F8A]"
              placeholder="Ex: 50000"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 dark:text-white/60 mb-1 block">Mode de paiement</label>
            <select
              value={form.mode_paiement}
              onChange={e => setForm({ ...form, mode_paiement: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-white dark:bg-[#0b1e30]/5 text-[#0A2540] dark:text-white text-sm focus:outline-none focus:border-[#1B4F8A]"
            >
              <option value="especes">Espèces</option>
              <option value="virement">Virement</option>
              <option value="cheque">Chèque</option>
              <option value="mobile_money">Mobile Money</option>
              <option value="carte">Carte bancaire</option>
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 dark:text-white/60 mb-1 block">Référence (optionnel)</label>
            <input
              type="text"
              value={form.reference}
              onChange={e => setForm({ ...form, reference: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-white dark:bg-[#0b1e30]/5 text-[#0A2540] dark:text-white text-sm focus:outline-none focus:border-[#1B4F8A]"
              placeholder="N° chèque, reçu..."
            />
          </div>
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose}
              className="flex-1 py-2 rounded-lg border border-gray-200 dark:border-white/10 text-sm font-medium text-gray-600 dark:text-white/70 hover:bg-gray-50 dark:hover:bg-white dark:bg-[#0b1e30]/5 transition">
              Annuler
            </button>
            <button type="submit" disabled={loading}
              className="flex-1 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold transition disabled:opacity-50">
              {loading ? "Enregistrement…" : "Enregistrer"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function TabCard({ children, testId }) {
  return (
    <div
      data-testid={testId}
      className="bg-white dark:bg-white dark:bg-[#0b1e30]/5 rounded-xl border border-gray-200 dark:border-white/10 shadow-sm overflow-hidden"
    >
      {children}
    </div>
  );
}

function EmptyState({ icon: Icon, label }) {
  return (
    <div className="py-14 text-center text-gray-400 dark:text-white/30">
      <Icon className="w-10 h-10 mx-auto mb-2 opacity-30" />
      <p className="text-sm">{label}</p>
    </div>
  );
}

function TabSkeleton() {
  return (
    <div className="space-y-2 p-6">
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-10 bg-gray-100 dark:bg-white dark:bg-[#0b1e30]/5 rounded animate-pulse" />
      ))}
    </div>
  );
}

function TableRow({ onClick, children }) {
  return (
    <tr
      className="border-b last:border-b-0 hover:bg-gray-50 dark:hover:bg-white dark:bg-[#0b1e30]/5 cursor-pointer transition-colors"
      onClick={onClick}
    >
      {children}
    </tr>
  );
}

// ─────────────────────────────────────────────
// INFO TAB — 3 sections
// ─────────────────────────────────────────────
function InfoTab({ client }) {
  return (
    <div data-testid="client-detail-info" className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Coordonnées */}
      <TabCard>
        <div className="px-5 py-4 border-b border-gray-100 dark:border-white/10">
          <h3 className="text-xs uppercase tracking-wider font-semibold text-gray-500 dark:text-white/50 flex items-center gap-2">
            <User className="w-3.5 h-3.5" /> Coordonnées
          </h3>
        </div>
        <dl className="px-5 py-4 space-y-3">
          <InfoRow label="Nom" value={client.nom} />
          <InfoRow label="Téléphone" value={client.telephone} />
          <InfoRow label="Email" value={client.email} />
          <InfoRow label="Adresse" value={client.adresse} />
          <InfoRow label="Ville" value={client.ville} />
          <InfoRow label="Pays" value={client.pays || "Côte d'Ivoire"} />
        </dl>
      </TabCard>

      {/* Informations commerciales */}
      <TabCard>
        <div className="px-5 py-4 border-b border-gray-100 dark:border-white/10">
          <h3 className="text-xs uppercase tracking-wider font-semibold text-gray-500 dark:text-white/50 flex items-center gap-2">
            <Building2 className="w-3.5 h-3.5" /> Commercial
          </h3>
        </div>
        <dl className="px-5 py-4 space-y-3">
          <InfoRow label="Référence" value={client.reference} mono />
          <InfoRow label="Type client" value={TYPE_COLOR[client.type_client]?.label || client.type_client} />
          <InfoRow label="Plafond crédit" value={formatFCFA(client.plafond_credit)} />
          <InfoRow label="Encours / Solde" value={formatFCFA(client.solde)} />
          <InfoRow label="Représentant" value={client.representant || "—"} />
          <InfoRow label="Statut" value={client.actif ? "Actif" : "Désactivé"} />
        </dl>
      </TabCard>

      {/* Méta */}
      <TabCard>
        <div className="px-5 py-4 border-b border-gray-100 dark:border-white/10">
          <h3 className="text-xs uppercase tracking-wider font-semibold text-gray-500 dark:text-white/50 flex items-center gap-2">
            <Hash className="w-3.5 h-3.5" /> Métadonnées
          </h3>
        </div>
        <dl className="px-5 py-4 space-y-3">
          <InfoRow label="ID" value={client.client_id} mono />
          <InfoRow label="Créé le" value={fmtDateTime(client.created_at)} />
          <InfoRow label="Mis à jour" value={fmtDateTime(client.updated_at)} />
          <InfoRow label="Notes" value={client.notes || "—"} />
        </dl>
      </TabCard>
    </div>
  );
}

function InfoRow({ label, value, mono }) {
  return (
    <div>
      <dt className="text-[10px] uppercase tracking-wider font-semibold text-gray-400 dark:text-white/40">{label}</dt>
      <dd className={`text-sm text-[#0A2540] dark:text-white mt-0.5 break-words ${mono ? "font-mono text-xs" : ""}`}>
        {value || "—"}
      </dd>
    </div>
  );
}

// ─────────────────────────────────────────────
// COMMANDES TAB
// ─────────────────────────────────────────────
function CommandesTab({ items, loading, onGo, client, canWrite, navigate }) {
  const list = Array.isArray(items) ? items : (items?.items || []);
  return (
    <TabCard testId="client-detail-commandes">
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 dark:border-white/10">
        <h3 className="text-sm font-semibold text-[#0A2540] dark:text-white">
          Commandes ({list.length})
        </h3>
        {canWrite && client.actif && (
          <button
            onClick={() => navigate(`/commandes/nouvelle?client_id=${client.client_id}`)}
            className="inline-flex items-center gap-1 text-xs text-[#FF6200] font-semibold hover:underline"
          >
            <PlusCircle className="w-3.5 h-3.5" /> Nouvelle commande
          </button>
        )}
      </div>
      {loading ? <TabSkeleton /> : list.length === 0 ? (
        <EmptyState icon={ShoppingCart} label="Aucune commande pour ce client" />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50 dark:bg-white dark:bg-[#0b1e30]/5 text-xs text-gray-500 dark:text-white/50 uppercase tracking-wider">
                <th className="px-5 py-3 text-left">Référence</th>
                <th className="px-5 py-3 text-left">Date</th>
                <th className="px-5 py-3 text-left">Statut</th>
                <th className="px-5 py-3 text-right">Montant</th>
                <th className="px-5 py-3 text-left">Dernière MAJ</th>
                <th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {list.map((c) => (
                <TableRow key={c.commande_id} onClick={() => onGo(c.commande_id)}>
                  <td className="px-5 py-3 font-mono text-xs">{c.reference}</td>
                  <td className="px-5 py-3">{fmtDate(c.date_commande)}</td>
                  <td className="px-5 py-3"><StatusBadge map={CMD_STATUT} value={c.statut} /></td>
                  <td className="px-5 py-3 text-right font-semibold">{fmt(c.montant_total)}</td>
                  <td className="px-5 py-3 text-xs text-gray-400">{ago(c.updated_at)}</td>
                  <td className="px-5 py-3 text-right"><ChevronRight className="w-4 h-4 text-gray-400 ml-auto" /></td>
                </TableRow>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </TabCard>
  );
}

// ─────────────────────────────────────────────
// PROFORMAS TAB
// ─────────────────────────────────────────────
function ProformasTab({ items, loading, onGo }) {
  const list = Array.isArray(items) ? items : (items?.items || []);
  return (
    <TabCard testId="client-detail-proformas">
      <div className="px-5 py-4 border-b border-gray-100 dark:border-white/10">
        <h3 className="text-sm font-semibold text-[#0A2540] dark:text-white">Proformas ({list.length})</h3>
      </div>
      {loading ? <TabSkeleton /> : list.length === 0 ? (
        <EmptyState icon={ReceiptText} label="Aucune proforma pour ce client" />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50 dark:bg-white dark:bg-[#0b1e30]/5 text-xs text-gray-500 dark:text-white/50 uppercase tracking-wider">
                <th className="px-5 py-3 text-left">Référence</th>
                <th className="px-5 py-3 text-left">Émission</th>
                <th className="px-5 py-3 text-left">Expiration</th>
                <th className="px-5 py-3 text-left">Statut</th>
                <th className="px-5 py-3 text-right">Montant TTC</th>
                <th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {list.map((p) => (
                <TableRow key={p.proforma_id} onClick={() => onGo(p.proforma_id)}>
                  <td className="px-5 py-3 font-mono text-xs">{p.reference || p.numero_proforma}</td>
                  <td className="px-5 py-3">{fmtDate(p.date_emission)}</td>
                  <td className="px-5 py-3">{fmtDate(p.date_expiration)}</td>
                  <td className="px-5 py-3"><StatusBadge map={PRO_STATUT} value={p.statut_proforma} /></td>
                  <td className="px-5 py-3 text-right font-semibold">{fmt(p.montant_ttc)}</td>
                  <td className="px-5 py-3 text-right"><ChevronRight className="w-4 h-4 text-gray-400 ml-auto" /></td>
                </TableRow>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </TabCard>
  );
}

// ─────────────────────────────────────────────
// FACTURES TAB
// ─────────────────────────────────────────────
function FacturesTab({ items, loading, onGo }) {
  const list = Array.isArray(items) ? items : (items?.items || []);
  const totalDu = list.reduce((s, f) => {
    if (["emise", "partiellement_payee"].includes(f.statut)) return s + (f.montant_ttc - (f.montant_paye || 0));
    return s;
  }, 0);
  return (
    <TabCard testId="client-detail-factures">
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 dark:border-white/10">
        <h3 className="text-sm font-semibold text-[#0A2540] dark:text-white">Factures ({list.length})</h3>
        {totalDu > 0 && (
          <span className="text-xs font-semibold text-red-600">
            Restant dû : {fmt(totalDu)}
          </span>
        )}
      </div>
      {loading ? <TabSkeleton /> : list.length === 0 ? (
        <EmptyState icon={FileText} label="Aucune facture pour ce client" />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50 dark:bg-white dark:bg-[#0b1e30]/5 text-xs text-gray-500 dark:text-white/50 uppercase tracking-wider">
                <th className="px-5 py-3 text-left">Référence</th>
                <th className="px-5 py-3 text-left">Date</th>
                <th className="px-5 py-3 text-left">Échéance</th>
                <th className="px-5 py-3 text-left">Statut</th>
                <th className="px-5 py-3 text-right">TTC</th>
                <th className="px-5 py-3 text-right">Payé</th>
                <th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {list.map((f) => (
                <TableRow key={f.facture_id} onClick={() => onGo(f.facture_id)}>
                  <td className="px-5 py-3 font-mono text-xs">{f.reference}</td>
                  <td className="px-5 py-3">{fmtDate(f.date_emission)}</td>
                  <td className="px-5 py-3">
                    {f.date_echeance ? (
                      <span className={new Date(f.date_echeance) < Date.now() && f.statut !== "payee" ? "text-red-600 font-semibold" : ""}>
                        {fmtDate(f.date_echeance)}
                      </span>
                    ) : "—"}
                  </td>
                  <td className="px-5 py-3"><StatusBadge map={FAC_STATUT} value={f.statut} /></td>
                  <td className="px-5 py-3 text-right font-semibold">{fmt(f.montant_ttc)}</td>
                  <td className="px-5 py-3 text-right text-green-600">{fmt(f.montant_paye)}</td>
                  <td className="px-5 py-3 text-right"><ChevronRight className="w-4 h-4 text-gray-400 ml-auto" /></td>
                </TableRow>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </TabCard>
  );
}

// ─────────────────────────────────────────────
// BONS DE LIVRAISON TAB
// ─────────────────────────────────────────────
function BLTab({ items, loading, onGo }) {
  const list = Array.isArray(items) ? items : [];
  return (
    <TabCard testId="client-detail-bl">
      <div className="px-5 py-4 border-b border-gray-100 dark:border-white/10">
        <h3 className="text-sm font-semibold text-[#0A2540] dark:text-white">Bons de livraison ({list.length})</h3>
      </div>
      {loading ? <TabSkeleton /> : list.length === 0 ? (
        <EmptyState icon={Truck} label="Aucun bon de livraison pour ce client" />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50 dark:bg-white dark:bg-[#0b1e30]/5 text-xs text-gray-500 dark:text-white/50 uppercase tracking-wider">
                <th className="px-5 py-3 text-left">Référence</th>
                <th className="px-5 py-3 text-left">Date création</th>
                <th className="px-5 py-3 text-left">Livraison prévue</th>
                <th className="px-5 py-3 text-left">Statut</th>
                <th className="px-5 py-3 text-left">Commande liée</th>
                <th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {list.map((bl) => (
                <TableRow key={bl.bl_id} onClick={() => onGo(bl.bl_id)}>
                  <td className="px-5 py-3 font-mono text-xs">{bl.reference}</td>
                  <td className="px-5 py-3">{fmtDate(bl.date_creation)}</td>
                  <td className="px-5 py-3">{fmtDate(bl.date_livraison_prevue)}</td>
                  <td className="px-5 py-3"><StatusBadge map={BL_STATUT} value={bl.statut} /></td>
                  <td className="px-5 py-3 font-mono text-xs text-gray-400">{bl.commande_reference || "—"}</td>
                  <td className="px-5 py-3 text-right"><ChevronRight className="w-4 h-4 text-gray-400 ml-auto" /></td>
                </TableRow>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </TabCard>
  );
}

// ─────────────────────────────────────────────
// PAIEMENTS TAB
// ─────────────────────────────────────────────
function PaiementsTab({ items, loading, onGo }) {
  const list = Array.isArray(items) ? items : [];
  const totalEncaisse = list.reduce((s, p) => s + (p.montant_total || 0), 0);
  const MODES = {
    especes: "Espèces", cheque: "Chèque", virement: "Virement", mobile_money: "Mobile Money",
  };
  return (
    <TabCard testId="client-detail-paiements">
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 dark:border-white/10">
        <h3 className="text-sm font-semibold text-[#0A2540] dark:text-white">Paiements ({list.length})</h3>
        {totalEncaisse > 0 && (
          <span className="text-xs font-semibold text-green-600">
            Total encaissé : {fmt(totalEncaisse)}
          </span>
        )}
      </div>
      {loading ? <TabSkeleton /> : list.length === 0 ? (
        <EmptyState icon={CreditCard} label="Aucun paiement pour ce client" />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50 dark:bg-white dark:bg-[#0b1e30]/5 text-xs text-gray-500 dark:text-white/50 uppercase tracking-wider">
                <th className="px-5 py-3 text-left">Référence</th>
                <th className="px-5 py-3 text-left">Date</th>
                <th className="px-5 py-3 text-left">Mode</th>
                <th className="px-5 py-3 text-right">Montant</th>
                <th className="px-5 py-3 text-right">Affecté</th>
                <th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {list.map((p) => (
                <TableRow key={p.paiement_id} onClick={() => onGo(p.paiement_id)}>
                  <td className="px-5 py-3 font-mono text-xs">{p.reference}</td>
                  <td className="px-5 py-3">{fmtDate(p.date_paiement)}</td>
                  <td className="px-5 py-3 text-xs">{MODES[p.mode_paiement] || p.mode_paiement}</td>
                  <td className="px-5 py-3 text-right font-semibold text-green-700">{fmt(p.montant_total)}</td>
                  <td className="px-5 py-3 text-right">{fmt(p.montant_affecte)}</td>
                  <td className="px-5 py-3 text-right"><ChevronRight className="w-4 h-4 text-gray-400 ml-auto" /></td>
                </TableRow>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </TabCard>
  );
}

// ─────────────────────────────────────────────
// COMPTE TAB (récapitulatif financier)
// ─────────────────────────────────────────────
function CompteTab({ data, loading, client }) {
  if (loading || !data) return <TabCard><TabSkeleton /></TabCard>;

  const fList = Array.isArray(data.factures) ? data.factures : (data.factures?.items || []);
  const pList = Array.isArray(data.paiements) ? data.paiements : [];

  const totalFacture = fList.reduce((s, f) => s + (f.montant_ttc || 0), 0);
  const totalPaye = pList.reduce((s, p) => s + (p.montant_total || 0), 0);
  const solde = totalFacture - totalPaye;

  const facturesImpayees = fList.filter(f => ["emise", "partiellement_payee"].includes(f.statut));
  const facturesEnRetard = facturesImpayees.filter(f => f.date_echeance && new Date(f.date_echeance) < Date.now());

  return (
    <div className="space-y-4" data-testid="client-detail-compte">
      {/* Récap financier */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <SummaryCard label="Total facturé" value={fmt(totalFacture)} color="text-[#0A2540]" dark />
        <SummaryCard label="Total encaissé" value={fmt(totalPaye)} color="text-green-600" />
        <SummaryCard label="Solde dû" value={fmt(Math.max(0, solde))} color={solde > 0 ? "text-red-600" : "text-green-600"} />
      </div>

      {/* Plafond & utilisation */}
      <TabCard>
        <div className="px-5 py-4">
          <h3 className="text-sm font-semibold text-[#0A2540] dark:text-white mb-3">Limite de crédit</h3>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-gray-500 dark:text-white/50">Encours</span>
                <span className="font-semibold">{fmt(client.solde || 0)} / {fmt(client.plafond_credit)}</span>
              </div>
              <div className="w-full bg-gray-100 dark:bg-white dark:bg-[#0b1e30]/10 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${
                    (client.solde / client.plafond_credit) > 0.9 ? "bg-red-500" :
                    (client.solde / client.plafond_credit) > 0.7 ? "bg-amber-500" : "bg-green-500"
                  }`}
                  style={{ width: `${Math.min(100, client.plafond_credit > 0 ? (client.solde / client.plafond_credit) * 100 : 0)}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </TabCard>

      {/* Factures en retard */}
      {facturesEnRetard.length > 0 && (
        <TabCard>
          <div className="px-5 py-4 border-b border-gray-100 dark:border-white/10 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-500" />
            <h3 className="text-sm font-semibold text-red-600">{facturesEnRetard.length} facture(s) en retard</h3>
          </div>
          <div className="px-5 py-3 space-y-2">
            {facturesEnRetard.map(f => (
              <div key={f.facture_id} className="flex justify-between text-sm">
                <span className="font-mono text-xs">{f.reference}</span>
                <span className="text-red-600 font-semibold">{fmt(f.montant_ttc - (f.montant_paye || 0))}</span>
                <span className="text-xs text-gray-400">Échu le {fmtDate(f.date_echeance)}</span>
              </div>
            ))}
          </div>
        </TabCard>
      )}

      {/* Derniers paiements */}
      <TabCard>
        <div className="px-5 py-4 border-b border-gray-100 dark:border-white/10">
          <h3 className="text-sm font-semibold text-[#0A2540] dark:text-white">Derniers paiements</h3>
        </div>
        {pList.length === 0 ? (
          <EmptyState icon={CreditCard} label="Aucun paiement enregistré" />
        ) : (
          <div className="px-5 py-2 space-y-2">
            {pList.slice(0, 5).map(p => (
              <div key={p.paiement_id} className="flex justify-between items-center text-sm py-1.5 border-b border-gray-50 dark:border-white/5 last:border-0">
                <span className="font-mono text-xs text-gray-500 dark:text-white/50">{p.reference}</span>
                <span className="text-xs text-gray-400">{fmtDate(p.date_paiement)}</span>
                <span className="font-semibold text-green-700">{fmt(p.montant_total)}</span>
              </div>
            ))}
          </div>
        )}
      </TabCard>
    </div>
  );
}

function SummaryCard({ label, value, color, dark }) {
  return (
    <div className={`rounded-xl border p-5 ${dark ? "bg-[#0A2540] dark:bg-white dark:bg-[#0b1e30]/5 border-[#0A2540]/20" : "bg-white dark:bg-white dark:bg-[#0b1e30]/5 border-gray-200 dark:border-white/10"}`}>
      <p className={`text-[10px] uppercase tracking-wider ${dark ? "text-white/60" : "text-gray-500 dark:text-white/50"}`}>{label}</p>
      <p className={`text-xl font-bold mt-1 ${dark ? "text-white" : color}`}>{value}</p>
    </div>
  );
}

// ─────────────────────────────────────────────
// HISTORIQUE TAB
// ─────────────────────────────────────────────
function HistoriqueTab({ client, data, loading }) {
  const logs = Array.isArray(data) ? data : [];

  const ACTION_ICONS = {
    CREATE: PlusCircle, UPDATE: Pencil, DELETE: XCircle,
    VALIDATE: CheckCircle2, DISABLE: PowerOff,
    CREATE_PROFORMA_AUTO: ReceiptText, CREATE_BL_AUTO: Truck,
    CREATE_PAIEMENT: CreditCard, VALIDATE_COMMANDE: CheckCircle2,
  };

  return (
    <TabCard testId="client-detail-historique">
      <div className="px-5 py-4 border-b border-gray-100 dark:border-white/10">
        <h3 className="text-sm font-semibold text-[#0A2540] dark:text-white">Historique des actions</h3>
      </div>
      {loading ? <TabSkeleton /> : logs.length === 0 ? (
        <EmptyState icon={History} label="Aucune action enregistrée pour ce client" />
      ) : (
        <div className="divide-y divide-gray-50 dark:divide-white/5">
          {logs.map((log, i) => {
            const actionKey = Object.keys(ACTION_ICONS).find(k => (log.action || "").includes(k)) || "UPDATE";
            const Icon = ACTION_ICONS[actionKey] || Clock;
            return (
              <div key={log.audit_id || i} className="flex items-start gap-3 px-5 py-3">
                <div className="w-7 h-7 rounded-full bg-blue-600/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Icon className="w-3.5 h-3.5 text-[#FF6200]" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-[#0A2540] dark:text-white font-medium">
                    {log.action}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {log.resource_type} · {fmtDateTime(log.timestamp || log.date_action)}
                  </p>
                  {log.details && typeof log.details === "object" && (
                    <p className="text-xs text-gray-500 dark:text-white/40 mt-0.5 truncate">
                      {Object.entries(log.details).slice(0, 3).map(([k, v]) => `${k}: ${v}`).join(" · ")}
                    </p>
                  )}
                </div>
                <span className="text-[10px] text-gray-400 flex-shrink-0">{ago(log.timestamp || log.date_action)}</span>
              </div>
            );
          })}
        </div>
      )}
    </TabCard>
  );
}
