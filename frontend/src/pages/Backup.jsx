import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "react-query";
import {
  Database, RefreshCw, Download, Trash2, Settings, Clock,
  ArrowLeft, Home, CheckCircle2, XCircle, AlertCircle,
  CloudUpload, HardDrive, Shield, FileArchive, History,
  Play, RotateCcw, FolderOpen, ChevronRight, Loader2,
  Server, Cpu,
} from "lucide-react";
import {
  getBackupConfig, updateBackupConfig, createBackup,
  listBackups, deleteBackup, restoreBackup,
  getBackupStats,
} from "@/services/backupService";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";

/* ─── helpers ─────────────────────────────────────────── */
const fmtSize = (bytes = 0) => {
  if (!bytes) return "—";
  const k = 1024, s = ["o", "Ko", "Mo", "Go"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return (bytes / Math.pow(k, i)).toFixed(1) + " " + s[i];
};
const fmtDate = (d) => d ? new Date(d).toLocaleString("fr-FR") : "—";

/* ─── StatCard ─────────────────────────────────────────── */
const StatCard = ({ icon: Icon, label, value, sub, color }) => (
  <div className="bg-[#1E293B] border border-white/8 rounded-[14px] p-5 flex items-start gap-4">
    <div className={`w-11 h-11 rounded-[10px] flex items-center justify-center flex-shrink-0`}
      style={{ background: `${color}1a`, border: `1px solid ${color}30` }}>
      <Icon size={20} style={{ color }} />
    </div>
    <div className="min-w-0">
      <p className="text-[#94A3B8] text-xs font-medium">{label}</p>
      <p className="text-[#E2E8F0] text-lg font-semibold mt-0.5 truncate">{value}</p>
      {sub && <p className="text-[#94A3B8] text-xs mt-0.5">{sub}</p>}
    </div>
  </div>
);

/* ─── StatusBadge ──────────────────────────────────────── */
const StatusBadge = ({ statut }) => {
  const map = {
    succes:   { label: "Succès",  cls: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30" },
    en_cours: { label: "En cours", cls: "bg-blue-500/15 text-blue-400 border-blue-500/30" },
    echec:    { label: "Échec",   cls: "bg-red-500/15 text-red-400 border-red-500/30" },
  };
  const { label, cls } = map[statut] || { label: statut, cls: "bg-white dark:bg-[#0b1e30]/10 text-[#94A3B8] border-white/10" };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${cls}`}>
      {label}
    </span>
  );
};

/* ═══════════════════════════════════════════════════════ */
const Backup = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("dashboard");

  const [configData, setConfigData] = useState({
    frequence_heures: 24,
    retention_jours: 30,
    heure_execution: "02:00",
    actif: true,
    chiffrement: true,
    compression: true,
  });

  /* ── queries ── */
  const { data: config } = useQuery(["backup-config"], getBackupConfig, {
    enabled: !!user,
    onSuccess: (d) => d && setConfigData((prev) => ({ ...prev, ...d })),
  });

  const { data: diskStats, isLoading: diskLoading } = useQuery(
    ["backup-stats"],
    getBackupStats,
    { enabled: !!user, refetchInterval: 60000 }
  );

  const { data: backups = [], isLoading } = useQuery(["backups"], listBackups, {
    enabled: !!user,
    refetchInterval: 30000,
  });

  /* ── mutations ── */
  const updateConfigMut = useMutation(updateBackupConfig, {
    onSuccess: () => { queryClient.invalidateQueries(["backup-config"]); toast.success("Configuration enregistrée"); },
    onError: () => toast.error("Erreur lors de la mise à jour"),
  });

  const createMut = useMutation(createBackup, {
    onSuccess: () => {
      queryClient.invalidateQueries(["backups"]);
      queryClient.invalidateQueries(["backup-stats"]);
      toast.success("Sauvegarde lancée avec succès");
    },
    onError: () => toast.error("Erreur lors du démarrage de la sauvegarde"),
  });

  const deleteMut = useMutation(deleteBackup, {
    onSuccess: () => {
      queryClient.invalidateQueries(["backups"]);
      queryClient.invalidateQueries(["backup-stats"]);
      toast.success("Backup supprimé");
    },
    onError: () => toast.error("Erreur lors de la suppression"),
  });

  const restoreMut = useMutation(restoreBackup, {
    onSuccess: () => toast.success("Restauration effectuée"),
    onError: () => toast.error("Erreur lors de la restauration"),
  });

  /* ── handlers ── */
  const handleCreate = () => {
    if (!confirm("Lancer une sauvegarde complète maintenant ?")) return;
    createMut.mutate();
  };
  const handleDelete = (id) => {
    if (!confirm("Supprimer ce backup ?")) return;
    deleteMut.mutate(id);
  };
  const handleRestore = (id) => {
    if (!confirm("ATTENTION : la restauration remplacera toutes les données actuelles. Confirmer ?")) return;
    restoreMut.mutate(id);
  };
  const handleDownload = (id) => {
    const url = `/api/backup/backups/${id}/download`;
    // ✅ PHASE 3.2: Browser auto-sends HttpOnly session_token cookie
    fetch(url, { credentials: "include" })
      .then((res) => {
        if (!res.ok) throw new Error("Erreur téléchargement");
        return res.blob();
      })
      .then((blob) => {
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = `${id}.zip`;
        a.click();
        URL.revokeObjectURL(a.href);
        toast.success("Téléchargement démarré");
      })
      .catch(() => toast.error("Impossible de télécharger ce backup"));
  };

  /* ── computed stats ── */
  const lastSuccess = backups.find((b) => b.statut === "succes");
  const totalSize   = backups.reduce((acc, b) => acc + (b.taille_octets || 0), 0);
  const inProgress  = backups.filter((b) => b.statut === "en_cours").length;
  const failCount   = backups.filter((b) => b.statut === "echec").length;

  /* ── disk usage pct ── */
  const diskUsedPct = diskStats?.disk
    ? Math.min((diskStats.disk.used_gb / diskStats.disk.total_gb) * 100, 100)
    : 0;

  /* ── tabs ── */
  const tabs = [
    { id: "dashboard",   icon: HardDrive,    label: "Tableau de bord" },
    { id: "backups",     icon: FileArchive,  label: "Backups" },
    { id: "config",      icon: Settings,     label: "Configuration" },
  ];

  return (
    <DashboardLayout>
      <div className="p-8 space-y-6">

        {/* ── Barre navigation ── */}
        <div className="flex items-center gap-2">
          <button onClick={() => navigate(-1)}
            className="flex items-center gap-1.5 h-8 px-3 rounded-[10px] bg-white dark:bg-[#0b1e30]/5 border border-white/8 text-[#94A3B8] text-xs font-medium hover:bg-white dark:bg-[#0b1e30]/10 hover:text-[#E2E8F0] transition-all">
            <ArrowLeft size={14} /> Retour
          </button>
          <button onClick={() => navigate("/")}
            className="flex items-center gap-1.5 h-8 px-3 rounded-[10px] bg-white dark:bg-[#0b1e30]/5 border border-white/8 text-[#94A3B8] text-xs font-medium hover:bg-white dark:bg-[#0b1e30]/10 hover:text-[#E2E8F0] transition-all">
            <Home size={14} /> Accueil
          </button>
          <span className="text-white/20 text-xs ml-1">·</span>
          <span className="text-[#94A3B8] text-xs">Documents</span>
          <ChevronRight size={12} className="text-white/20" />
          <span className="text-[#E2E8F0] text-xs font-medium">Backup & Disaster Recovery</span>
        </div>

        {/* ── En-tête ── */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-[#E2E8F0]">Backup & Disaster Recovery</h1>
            <p className="text-[#94A3B8] text-sm mt-1">Sauvegarde automatique et restauration des données</p>
          </div>
          <button
            onClick={handleCreate}
            disabled={createMut.isLoading}
            className="flex items-center gap-2 h-10 px-5 rounded-[10px] text-sm font-medium text-white border-0 disabled:opacity-60 transition-opacity"
            style={{ background: "linear-gradient(90deg,#F97316,#FB923C)" }}
          >
            {createMut.isLoading
              ? <><Loader2 size={16} className="animate-spin" /> Sauvegarde en cours…</>
              : <><CloudUpload size={16} /> Sauvegarder maintenant</>}
          </button>
        </div>

        {/* ── Onglets ── */}
        <div className="flex items-center gap-1 bg-[#111827] border border-white/8 rounded-xl p-1 w-fit">
          {tabs.map(({ id, icon: Icon, label }) => (
            <button key={id} onClick={() => setActiveTab(id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-[10px] text-sm font-medium transition-all duration-200
                ${activeTab === id ? "text-white shadow-sm" : "text-[#94A3B8] hover:text-[#E2E8F0] hover:bg-white dark:bg-[#0b1e30]/5"}`}
              style={activeTab === id ? { background: "linear-gradient(90deg,#F97316,#FB923C)" } : {}}>
              <Icon size={16} />{label}
            </button>
          ))}
        </div>

        {/* ══════════════════════════════════════════ */}
        {/* TAB : TABLEAU DE BORD                      */}
        {/* ══════════════════════════════════════════ */}
        {activeTab === "dashboard" && (
          <div className="space-y-6">
            {/* KPIs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard icon={CheckCircle2} label="Dernière sauvegarde" color="#10B981"
                value={lastSuccess ? fmtDate(lastSuccess.created_at).split(" ")[0] : "—"}
                sub={lastSuccess ? fmtDate(lastSuccess.created_at).split(" ")[1] : "Aucune sauvegarde"} />
              <StatCard icon={Clock} label="Prochaine sauvegarde" color="#3B82F6"
                value={config?.heure_execution || "02:00"}
                sub="Tous les jours" />
              <StatCard icon={HardDrive} label="Taille totale sauvegardée" color="#F97316"
                value={fmtSize(totalSize)}
                sub={`${backups.length} backup${backups.length > 1 ? "s" : ""} disponible${backups.length > 1 ? "s" : ""}`} />
              <StatCard icon={failCount > 0 ? AlertCircle : Shield} label="État système" color={failCount > 0 ? "#EF4444" : "#10B981"}
                value={failCount > 0 ? `${failCount} échec${failCount > 1 ? "s" : ""}` : "Opérationnel"}
                sub={inProgress > 0 ? `${inProgress} en cours` : "Aucune erreur active"} />
            </div>

            {/* ── Stockage local ── */}
            <div className="bg-[#1E293B] border border-white/8 rounded-[14px] p-5">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-[10px] bg-[#10B981]/10 border border-[#10B981]/20 flex items-center justify-center">
                    <Server size={18} className="text-[#10B981]" />
                  </div>
                  <div>
                    <p className="text-[#E2E8F0] text-sm font-semibold">Stockage local</p>
                    <p className="text-[#94A3B8] text-xs font-mono truncate max-w-[280px]">
                      {diskStats?.backup_path || "backups/Database/"}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {diskLoading ? (
                    <Loader2 size={14} className="animate-spin text-[#94A3B8]" />
                  ) : (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border bg-emerald-500/15 text-emerald-400 border-emerald-500/30">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      Actif
                    </span>
                  )}
                </div>
              </div>

              {/* Jauge disque */}
              {diskStats?.disk && (
                <div className="mb-4 bg-[#0B1220] border border-white/8 rounded-[10px] p-3">
                  <div className="flex justify-between text-xs mb-2">
                    <span className="text-[#94A3B8]">Espace disque utilisé</span>
                    <span className="text-[#E2E8F0] font-medium">
                      {diskStats.disk.used_gb} Go / {diskStats.disk.total_gb} Go
                    </span>
                  </div>
                  <div className="h-2 bg-white dark:bg-[#0b1e30]/10 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${diskUsedPct.toFixed(1)}%`,
                        background: diskUsedPct > 85 ? "#EF4444" : diskUsedPct > 65 ? "#F97316" : "#10B981",
                      }}
                    />
                  </div>
                  <div className="flex justify-between text-xs mt-2">
                    <span className="text-[#94A3B8]">{diskUsedPct.toFixed(1)}% utilisé</span>
                    <span className="text-emerald-400 font-medium">{diskStats.disk.free_gb} Go disponibles</span>
                  </div>
                </div>
              )}

              {/* Stats fichiers ZIP */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-[#0B1220] border border-white/8 rounded-[10px] p-3 text-center">
                  <p className="text-2xl font-bold text-[#F97316]">
                    {diskStats?.backup_count ?? backups.length}
                  </p>
                  <p className="text-[#94A3B8] text-xs mt-1">Fichiers ZIP</p>
                </div>
                <div className="bg-[#0B1220] border border-white/8 rounded-[10px] p-3 text-center">
                  <p className="text-2xl font-bold text-[#3B82F6]">
                    {fmtSize(diskStats?.total_size_bytes ?? totalSize)}
                  </p>
                  <p className="text-[#94A3B8] text-xs mt-1">Taille totale</p>
                </div>
                <div className="bg-[#0B1220] border border-white/8 rounded-[10px] p-3 text-center">
                  <p className="text-2xl font-bold text-[#10B981]">
                    {config?.retention_jours ?? configData.retention_jours}j
                  </p>
                  <p className="text-[#94A3B8] text-xs mt-1">Rétention</p>
                </div>
              </div>

              {/* Arborescence */}
              <div className="mt-4 bg-[#0B1220] border border-white/8 rounded-[10px] p-4 font-mono text-xs text-[#94A3B8] space-y-1">
                <p className="text-[#E2E8F0] font-semibold mb-2">📁 backups/</p>
                {["└── Database/", "    ├── backup_2026-*.zip", "    └── … (rotation auto)"].map((l) => (
                  <p key={l} className="pl-4">{l}</p>
                ))}
              </div>
            </div>

            {/* Politique de rétention */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {[
                { label: "Sauvegardes quotidiennes", value: "30", color: "#3B82F6", sub: "30 derniers jours" },
                { label: "Sauvegardes mensuelles",   value: "12", color: "#F97316", sub: "12 derniers mois" },
                { label: "Sauvegardes annuelles",    value: "5",  color: "#8B5CF6", sub: "5 dernières années" },
              ].map(({ label, value, color, sub }) => (
                <div key={label} className="bg-[#1E293B] border border-white/8 rounded-[14px] p-5 text-center">
                  <p className="text-4xl font-bold mb-1" style={{ color }}>{value}</p>
                  <p className="text-[#E2E8F0] text-sm font-medium">{label}</p>
                  <p className="text-[#94A3B8] text-xs mt-1">{sub}</p>
                </div>
              ))}
            </div>

            {/* Derniers backups */}
            <div className="bg-[#1E293B] border border-white/8 rounded-[14px] overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4 border-b border-white/8">
                <p className="text-[#E2E8F0] text-sm font-semibold">Historique récent</p>
                <button onClick={() => setActiveTab("backups")}
                  className="text-[#F97316] text-xs hover:underline">Voir tout</button>
              </div>
              {isLoading ? (
                <div className="flex items-center justify-center py-10 text-[#94A3B8] text-sm">
                  <Loader2 size={18} className="animate-spin mr-2" /> Chargement…
                </div>
              ) : backups.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-[#94A3B8]">
                  <Database size={36} className="mb-3 opacity-30" />
                  <p className="text-sm">Aucune sauvegarde disponible</p>
                  <p className="text-xs mt-1">Cliquez sur « Sauvegarder maintenant » pour démarrer</p>
                </div>
              ) : (
                <div className="divide-y divide-white/5">
                  {backups.slice(0, 5).map((b) => (
                    <div key={b.backup_id} className="flex items-center justify-between px-5 py-3.5 hover:bg-white dark:bg-[#0b1e30]/3 transition-colors">
                      <div className="flex items-center gap-3">
                        <FileArchive size={16} className="text-[#F97316]" />
                        <div>
                          <p className="text-[#E2E8F0] text-sm font-medium">{b.type_backup || "Sauvegarde complète"}</p>
                          <p className="text-[#94A3B8] text-xs">{fmtDate(b.created_at)}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-[#94A3B8] text-xs">{fmtSize(b.taille_octets)}</span>
                        <StatusBadge statut={b.statut} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Périmètre de sauvegarde */}
            <div className="bg-[#1E293B] border border-white/8 rounded-[14px] p-5">
              <p className="text-[#E2E8F0] text-sm font-semibold mb-4">Périmètre de sauvegarde</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {[
                  { label: "Base de données",   icon: Database,   color: "#3B82F6", items: "Clients, Factures, Stocks, RH, Compta…" },
                  { label: "Fichiers",           icon: FolderOpen, color: "#F97316", items: "PDFs, logos, signatures, images, rapports" },
                  { label: "Code source",        icon: HardDrive,  color: "#10B981", items: "Frontend, backend, API, scripts, configs" },
                  { label: "Configuration ERP", icon: Settings,   color: "#8B5CF6", items: "Utilisateurs, rôles, permissions, paramètres" },
                ].map(({ label, icon: Icon, color, items }) => (
                  <div key={label} className="bg-[#0B1220] border border-white/8 rounded-[10px] p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Icon size={15} style={{ color }} />
                      <p className="text-[#E2E8F0] text-xs font-semibold">{label}</p>
                    </div>
                    <p className="text-[#94A3B8] text-xs leading-relaxed">{items}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Sécurité */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {[
                { icon: Shield,       label: "Chiffrement AES-256",      active: configData.chiffrement, color: "#10B981" },
                { icon: FileArchive,  label: "Compression ZIP",           active: configData.compression, color: "#3B82F6" },
                { icon: CheckCircle2, label: "Vérification d'intégrité",  active: true,                  color: "#F97316" },
              ].map(({ icon: Icon, label, active, color }) => (
                <div key={label} className="bg-[#1E293B] border border-white/8 rounded-[14px] p-4 flex items-center gap-3">
                  <div className="w-9 h-9 rounded-[8px] flex items-center justify-center flex-shrink-0"
                    style={{ background: `${color}1a`, border: `1px solid ${color}30` }}>
                    <Icon size={16} style={{ color }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[#E2E8F0] text-xs font-medium">{label}</p>
                  </div>
                  <span className={`text-xs font-medium ${active ? "text-emerald-400" : "text-[#94A3B8]"}`}>
                    {active ? "Actif" : "Inactif"}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════ */}
        {/* TAB : LISTE BACKUPS                        */}
        {/* ══════════════════════════════════════════ */}
        {activeTab === "backups" && (
          <Card className="bg-[#1E293B] border border-white/8 rounded-[14px] shadow-none">
            <CardHeader className="border-b border-white/8 pb-4 flex flex-row items-center justify-between">
              <CardTitle className="text-[#E2E8F0] text-base font-semibold">Historique des sauvegardes</CardTitle>
              <p className="text-[#94A3B8] text-xs">{backups.length} backup{backups.length > 1 ? "s" : ""}</p>
            </CardHeader>
            <CardContent className="p-0">
              {isLoading ? (
                <div className="flex items-center justify-center py-16 text-[#94A3B8] text-sm">
                  <Loader2 size={18} className="animate-spin mr-2" /> Chargement…
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-white/8">
                        {["ID", "Type", "Taille", "Statut", "Fichier ZIP", "Date", "Actions"].map((h) => (
                          <th key={h} className="text-left py-3 px-5 text-xs font-semibold text-[#94A3B8] uppercase tracking-wide">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {backups.map((b, i) => (
                        <tr key={b.backup_id}
                          className={`border-b border-white/5 hover:bg-white dark:bg-[#0b1e30]/3 transition-colors ${i % 2 === 0 ? "" : "bg-white dark:bg-[#0b1e30]/[0.02]"}`}>
                          <td className="py-3.5 px-5 text-xs font-mono text-[#94A3B8]">{b.backup_id}</td>
                          <td className="py-3.5 px-5 text-sm text-[#E2E8F0] capitalize">{b.type_backup || "Complet"}</td>
                          <td className="py-3.5 px-5 text-sm text-[#E2E8F0]">{fmtSize(b.taille_octets)}</td>
                          <td className="py-3.5 px-5"><StatusBadge statut={b.statut} /></td>
                          <td className="py-3.5 px-5">
                            {b.fichier_zip ? (
                              <span className="inline-flex items-center gap-1 text-[#10B981] text-xs font-mono">
                                <FileArchive size={12} /> {b.fichier_zip.split("/").pop()}
                              </span>
                            ) : (
                              <span className="text-[#94A3B8] text-xs">—</span>
                            )}
                          </td>
                          <td className="py-3.5 px-5 text-sm text-[#94A3B8]">{fmtDate(b.created_at)}</td>
                          <td className="py-3.5 px-5">
                            <div className="flex items-center gap-2">
                              <button onClick={() => handleDownload(b.backup_id)}
                                className="h-7 px-2.5 flex items-center gap-1.5 rounded-[8px] bg-[#10B981]/10 border border-[#10B981]/20 text-[#10B981] text-xs font-medium hover:bg-[#10B981]/20 transition-colors">
                                <Download size={12} /> Télécharger
                              </button>
                              <button onClick={() => handleRestore(b.backup_id)}
                                className="h-7 px-2.5 flex items-center gap-1.5 rounded-[8px] bg-[#3B82F6]/10 border border-[#3B82F6]/20 text-[#3B82F6] text-xs font-medium hover:bg-[#3B82F6]/20 transition-colors">
                                <RotateCcw size={12} /> Restaurer
                              </button>
                              <button onClick={() => handleDelete(b.backup_id)}
                                className="h-7 px-2.5 flex items-center gap-1.5 rounded-[8px] bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium hover:bg-red-500/20 transition-colors">
                                <Trash2 size={12} /> Supprimer
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {backups.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-16 text-[#94A3B8]">
                      <Database size={40} className="mb-3 opacity-30" />
                      <p className="text-sm">Aucun backup disponible</p>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* ══════════════════════════════════════════ */}
        {/* TAB : CONFIGURATION                        */}
        {/* ══════════════════════════════════════════ */}
        {activeTab === "config" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Planification */}
            <Card className="bg-[#1E293B] border border-white/8 rounded-[14px] shadow-none">
              <CardHeader className="border-b border-white/8 pb-4">
                <CardTitle className="text-[#E2E8F0] text-base font-semibold">Planification</CardTitle>
                <p className="text-[#94A3B8] text-sm">Fréquence et horaire de sauvegarde</p>
              </CardHeader>
              <CardContent className="pt-5 space-y-5">
                <div className="space-y-1.5">
                  <Label className="text-[#94A3B8] text-xs font-medium">Fréquence (heures)</Label>
                  <Input type="number" min="1" max="168"
                    value={configData.frequence_heures}
                    onChange={(e) => setConfigData({ ...configData, frequence_heures: parseInt(e.target.value) })}
                    className="h-10 bg-[#0B1220] border-white/10 text-[#E2E8F0] rounded-[10px] focus:border-[#F97316]/60" />
                  <p className="text-[#94A3B8] text-xs">24 = tous les jours, 168 = toutes les semaines</p>
                </div>
                <div className="space-y-1.5">
                  <Label className="text-[#94A3B8] text-xs font-medium">Heure d'exécution</Label>
                  <Input type="time"
                    value={configData.heure_execution}
                    onChange={(e) => setConfigData({ ...configData, heure_execution: e.target.value })}
                    className="h-10 bg-[#0B1220] border-white/10 text-[#E2E8F0] rounded-[10px] focus:border-[#F97316]/60" />
                  <p className="text-[#94A3B8] text-xs">Par défaut 02:00 — exécution en heure creuse</p>
                </div>
                <div className="space-y-1.5">
                  <Label className="text-[#94A3B8] text-xs font-medium">Rétention (jours)</Label>
                  <Input type="number" min="1" max="365"
                    value={configData.retention_jours}
                    onChange={(e) => setConfigData({ ...configData, retention_jours: parseInt(e.target.value) })}
                    className="h-10 bg-[#0B1220] border-white/10 text-[#E2E8F0] rounded-[10px] focus:border-[#F97316]/60" />
                </div>
                <div className="flex items-center justify-between py-3 border-t border-white/8">
                  <div>
                    <p className="text-[#E2E8F0] text-sm font-medium">Sauvegardes automatiques</p>
                    <p className="text-[#94A3B8] text-xs">Activer/désactiver le planificateur</p>
                  </div>
                  <button
                    onClick={() => setConfigData({ ...configData, actif: !configData.actif })}
                    className={`relative w-11 h-6 rounded-full transition-colors ${configData.actif ? "bg-[#F97316]" : "bg-white dark:bg-[#0b1e30]/10"}`}>
                    <span className={`absolute top-0.5 w-5 h-5 bg-white dark:bg-[#0b1e30] rounded-full shadow transition-transform ${configData.actif ? "translate-x-5" : "translate-x-0.5"}`} />
                  </button>
                </div>
              </CardContent>
            </Card>

            {/* Sécurité & Stockage */}
            <Card className="bg-[#1E293B] border border-white/8 rounded-[14px] shadow-none">
              <CardHeader className="border-b border-white/8 pb-4">
                <CardTitle className="text-[#E2E8F0] text-base font-semibold">Sécurité & Stockage</CardTitle>
                <p className="text-[#94A3B8] text-sm">Chiffrement, compression et stockage local</p>
              </CardHeader>
              <CardContent className="pt-5 space-y-4">
                {[
                  { key: "chiffrement", label: "Chiffrement AES-256",  sub: "Chiffrement des archives" },
                  { key: "compression", label: "Compression ZIP",       sub: "Réduire la taille des fichiers" },
                ].map(({ key, label, sub }) => (
                  <div key={key} className="flex items-center justify-between py-3 border-b border-white/8 last:border-0">
                    <div>
                      <p className="text-[#E2E8F0] text-sm font-medium">{label}</p>
                      <p className="text-[#94A3B8] text-xs">{sub}</p>
                    </div>
                    <button
                      onClick={() => setConfigData({ ...configData, [key]: !configData[key] })}
                      className={`relative w-11 h-6 rounded-full transition-colors ${configData[key] ? "bg-[#F97316]" : "bg-white dark:bg-[#0b1e30]/10"}`}>
                      <span className={`absolute top-0.5 w-5 h-5 bg-white dark:bg-[#0b1e30] rounded-full shadow transition-transform ${configData[key] ? "translate-x-5" : "translate-x-0.5"}`} />
                    </button>
                  </div>
                ))}

                {/* Info stockage local */}
                <div className="bg-[#0B1220] border border-[#10B981]/20 rounded-[10px] p-4 mt-2">
                  <div className="flex items-center gap-2 mb-2">
                    <Server size={14} className="text-[#10B981]" />
                    <p className="text-[#10B981] text-xs font-semibold">Stockage local uniquement</p>
                  </div>
                  <p className="text-[#94A3B8] text-xs leading-relaxed">
                    Les sauvegardes sont stockées localement dans{" "}
                    <span className="font-mono text-[#E2E8F0]">backups/Database/</span>.
                    Assurez-vous d'avoir suffisamment d'espace disque disponible.
                  </p>
                  {diskStats?.disk && (
                    <p className="text-[#94A3B8] text-xs mt-2">
                      Espace libre :{" "}
                      <span className="text-emerald-400 font-semibold">{diskStats.disk.free_gb} Go</span>
                      {" "}/ {diskStats.disk.total_gb} Go total
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Bouton enregistrer */}
            <div className="lg:col-span-2">
              <button
                onClick={(e) => { e.preventDefault(); updateConfigMut.mutate(configData); }}
                disabled={updateConfigMut.isLoading}
                className="h-10 px-6 text-sm font-medium text-white rounded-[10px] border-0 disabled:opacity-60 flex items-center gap-2"
                style={{ background: "linear-gradient(90deg,#F97316,#FB923C)" }}>
                {updateConfigMut.isLoading
                  ? <><Loader2 size={15} className="animate-spin" /> Enregistrement…</>
                  : <><Settings size={15} /> Enregistrer la configuration</>}
              </button>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default Backup;
