import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { CheckCircle, XCircle, FileCheck, Shield, History, Plus, ArrowLeft, Home } from "lucide-react";
import { listWorkflows, createWorkflow, createApprovalStep, rejectWorkflow, listAuditLogs } from "@/services/workflowApprovalsService";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";

const WorkflowApprovals = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("workflows");
  const [showCreate, setShowCreate] = useState(false);
  const [formData, setFormData] = useState({
    type_entite: "commande",
    entite_id: "",
    niveau_requis: 2,
    approbateurs: "",
    description: "",
  });

  const { data: workflows, isLoading } = useQuery(
    ["workflows"],
    () => listWorkflows(),
    { enabled: !!user && activeTab === "workflows" }
  );

  const { data: auditLogs } = useQuery(
    ["audit-logs"],
    () => listAuditLogs(),
    { enabled: !!user && activeTab === "audit" }
  );

  const createMutation = useMutation(createWorkflow, {
    onSuccess: () => {
      queryClient.invalidateQueries(["workflows"]);
      toast.success("Workflow créé avec succès");
      setShowCreate(false);
      setFormData({ type_entite: "commande", entite_id: "", niveau_requis: 2, approbateurs: "", description: "" });
    },
    onError: () => toast.error("Erreur lors de la création"),
  });

  const approveMutation = useMutation(createApprovalStep, {
    onSuccess: () => { queryClient.invalidateQueries(["workflows"]); toast.success("Approbation enregistrée"); },
    onError: () => toast.error("Erreur lors de l'approbation"),
  });

  const rejectMutation = useMutation(
    ({ workflowId, commentaire }) => rejectWorkflow(workflowId, commentaire),
    {
      onSuccess: () => { queryClient.invalidateQueries(["workflows"]); toast.success("Workflow rejeté"); },
      onError: () => toast.error("Erreur lors du rejet"),
    }
  );

  const handleCreate = (e) => {
    e.preventDefault();
    createMutation.mutate({ ...formData, approbateurs: formData.approbateurs.split(",").map((s) => s.trim()) });
  };

  const handleApprove = (workflowId) => approveMutation.mutate({ workflow_id: workflowId, approbateur_id: user.user_id });

  const handleReject = (workflowId) => {
    const commentaire = prompt("Commentaire de rejet:");
    if (commentaire) rejectMutation.mutate({ workflowId, commentaire });
  };

  const getStatutBadge = (statut) => {
    const map = {
      en_attente: { label: "En attente", style: "bg-yellow-500/15 text-yellow-400 border-yellow-500/30" },
      approuve:   { label: "Approuvé",   style: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30" },
      rejete:     { label: "Rejeté",     style: "bg-red-500/15 text-red-400 border-red-500/30" },
    };
    const { label, style } = map[statut] || { label: statut, style: "bg-[#1E293B] text-[#94A3B8] border-white/10" };
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${style}`}>
        {label}
      </span>
    );
  };

  const tabs = [
    { id: "workflows",  icon: FileCheck, label: "Workflows" },
    { id: "signatures", icon: Shield,    label: "Signatures" },
    { id: "audit",      icon: History,   label: "Audit Logs" },
  ];

  if (isLoading) return (
    <div className="p-8 flex items-center justify-center min-h-[200px]">
      <span className="text-[#94A3B8] text-sm">Chargement...</span>
    </div>
  );

  return (
    <div className="p-8 space-y-6">
      {/* Barre de navigation */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-1.5 h-8 px-3 rounded-[10px] bg-white dark:bg-[#0b1e30]/5 border border-white/8 text-[#94A3B8] text-xs font-medium hover:bg-white dark:bg-[#0b1e30]/10 hover:text-[#E2E8F0] transition-all"
        >
          <ArrowLeft size={14} />
          Retour
        </button>
        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-1.5 h-8 px-3 rounded-[10px] bg-white dark:bg-[#0b1e30]/5 border border-white/8 text-[#94A3B8] text-xs font-medium hover:bg-white dark:bg-[#0b1e30]/10 hover:text-[#E2E8F0] transition-all"
        >
          <Home size={14} />
          Accueil
        </button>
        {/* Fil d'Ariane */}
        <span className="text-white/20 text-xs ml-1">·</span>
        <span className="text-[#94A3B8] text-xs">Administration</span>
        <span className="text-white/20 text-xs">·</span>
        <span className="text-[#E2E8F0] text-xs font-medium">Workflow Approbations</span>
      </div>

      {/* En-tête */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-[#E2E8F0]">Workflow Approbations</h1>
          <p className="text-[#94A3B8] text-sm mt-1">Approbations multi-niveaux et signature électronique</p>
        </div>

        {/* Boutons de navigation onglets */}
        <div className="flex items-center gap-1 bg-[#111827] border border-white/8 rounded-xl p-1">
          {tabs.map(({ id, icon: Icon, label }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-[10px] text-sm font-medium transition-all duration-200
                ${activeTab === id
                  ? "text-white shadow-sm"
                  : "text-[#94A3B8] hover:text-[#E2E8F0] hover:bg-white dark:bg-[#0b1e30]/5"
                }
              `}
              style={activeTab === id ? { background: "linear-gradient(90deg,#F97316,#FB923C)" } : {}}
            >
              <Icon size={16} />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Onglet Workflows */}
      {activeTab === "workflows" && (
        <Card className="bg-[#1E293B] border border-white/8 rounded-[14px] shadow-none">
          <CardHeader className="flex flex-row items-center justify-between pb-4 border-b border-white/8">
            <CardTitle className="text-[#E2E8F0] text-base font-semibold">Workflows d'approbation</CardTitle>
            <Dialog open={showCreate} onOpenChange={setShowCreate}>
              <DialogTrigger asChild>
                <Button
                  className="h-9 px-4 text-sm font-medium text-white rounded-[10px] border-0"
                  style={{ background: "linear-gradient(90deg,#F97316,#FB923C)" }}
                >
                  <Plus size={16} className="mr-2" />
                  Nouveau workflow
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#1E293B] border border-white/10 rounded-[14px] text-[#E2E8F0] max-w-md shadow-2xl">
                <DialogHeader>
                  <DialogTitle className="text-[#E2E8F0] font-semibold">Créer un workflow</DialogTitle>
                  <p className="text-[#94A3B8] text-sm">Définir un workflow d'approbation multi-niveaux</p>
                </DialogHeader>
                <form onSubmit={handleCreate} className="space-y-4 mt-2">
                  <div className="space-y-1.5">
                    <Label className="text-[#94A3B8] text-xs font-medium">Type d'entité</Label>
                    <select
                      value={formData.type_entite}
                      onChange={(e) => setFormData({ ...formData, type_entite: e.target.value })}
                      className="w-full h-10 px-3 bg-[#0B1220] border border-white/10 rounded-[10px] text-[#E2E8F0] text-sm focus:outline-none focus:border-[#F97316]/60 transition-colors"
                      required
                    >
                      <option value="commande">Commande</option>
                      <option value="facture">Facture</option>
                      <option value="paiement">Paiement</option>
                      <option value="mission">Mission</option>
                      <option value="achat">Achat</option>
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-[#94A3B8] text-xs font-medium">ID Entité</Label>
                    <Input
                      value={formData.entite_id}
                      onChange={(e) => setFormData({ ...formData, entite_id: e.target.value })}
                      className="h-10 bg-[#0B1220] border-white/10 text-[#E2E8F0] rounded-[10px] focus:border-[#F97316]/60"
                      placeholder="Ex: CMD-2024-001"
                      required
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-[#94A3B8] text-xs font-medium">Niveau requis (1–5)</Label>
                    <Input
                      type="number"
                      min="1"
                      max="5"
                      value={formData.niveau_requis}
                      onChange={(e) => setFormData({ ...formData, niveau_requis: parseInt(e.target.value) })}
                      className="h-10 bg-[#0B1220] border-white/10 text-[#E2E8F0] rounded-[10px] focus:border-[#F97316]/60"
                      required
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-[#94A3B8] text-xs font-medium">Approbateurs (IDs séparés par virgule)</Label>
                    <Input
                      value={formData.approbateurs}
                      onChange={(e) => setFormData({ ...formData, approbateurs: e.target.value })}
                      className="h-10 bg-[#0B1220] border-white/10 text-[#E2E8F0] rounded-[10px] focus:border-[#F97316]/60"
                      placeholder="user1, user2, user3"
                      required
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-[#94A3B8] text-xs font-medium">Description</Label>
                    <Input
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      className="h-10 bg-[#0B1220] border-white/10 text-[#E2E8F0] rounded-[10px] focus:border-[#F97316]/60"
                      placeholder="Description optionnelle"
                    />
                  </div>
                  <Button
                    type="submit"
                    className="w-full h-10 text-sm font-medium text-white rounded-[10px] border-0 mt-2"
                    style={{ background: "linear-gradient(90deg,#F97316,#FB923C)" }}
                    disabled={createMutation.isLoading}
                  >
                    {createMutation.isLoading ? "Création..." : "Créer le workflow"}
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/8">
                    <th className="text-left py-3 px-5 text-xs font-semibold text-[#94A3B8] uppercase tracking-wide">Workflow</th>
                    <th className="text-left py-3 px-5 text-xs font-semibold text-[#94A3B8] uppercase tracking-wide">Type</th>
                    <th className="text-left py-3 px-5 text-xs font-semibold text-[#94A3B8] uppercase tracking-wide">Entité</th>
                    <th className="text-left py-3 px-5 text-xs font-semibold text-[#94A3B8] uppercase tracking-wide">Niveau</th>
                    <th className="text-left py-3 px-5 text-xs font-semibold text-[#94A3B8] uppercase tracking-wide">Statut</th>
                    <th className="text-left py-3 px-5 text-xs font-semibold text-[#94A3B8] uppercase tracking-wide">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {workflows?.map((wf, i) => (
                    <tr
                      key={wf.workflow_id}
                      className={`border-b border-white/5 transition-colors hover:bg-white dark:bg-[#0b1e30]/3 ${i % 2 === 0 ? "" : "bg-white dark:bg-[#0b1e30]/[0.02]"}`}
                    >
                      <td className="py-3.5 px-5 text-sm font-mono text-[#94A3B8]">{wf.workflow_id}</td>
                      <td className="py-3.5 px-5 text-sm text-[#E2E8F0] capitalize">{wf.type_entite}</td>
                      <td className="py-3.5 px-5 text-sm text-[#E2E8F0]">{wf.entite_id}</td>
                      <td className="py-3.5 px-5">
                        <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-[#3B82F6]/15 text-[#3B82F6] text-xs font-bold">
                          {wf.niveau_requis}
                        </span>
                      </td>
                      <td className="py-3.5 px-5">{getStatutBadge(wf.statut)}</td>
                      <td className="py-3.5 px-5">
                        {wf.statut === "en_attente" && (
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleApprove(wf.workflow_id)}
                              className="h-8 px-3 flex items-center gap-1.5 rounded-[8px] bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium hover:bg-emerald-500/20 transition-colors"
                            >
                              <CheckCircle size={14} />
                              Approuver
                            </button>
                            <button
                              onClick={() => handleReject(wf.workflow_id)}
                              className="h-8 px-3 flex items-center gap-1.5 rounded-[8px] bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium hover:bg-red-500/20 transition-colors"
                            >
                              <XCircle size={14} />
                              Rejeter
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {(!workflows || workflows.length === 0) && (
                <div className="flex flex-col items-center justify-center py-16 text-[#94A3B8]">
                  <FileCheck size={40} className="mb-3 opacity-30" />
                  <p className="text-sm">Aucun workflow trouvé</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Onglet Signatures */}
      {activeTab === "signatures" && (
        <Card className="bg-[#1E293B] border border-white/8 rounded-[14px] shadow-none">
          <CardHeader className="border-b border-white/8 pb-4">
            <CardTitle className="text-[#E2E8F0] text-base font-semibold">Signatures électroniques</CardTitle>
            <p className="text-[#94A3B8] text-sm">Gestion des signatures électroniques sur les documents</p>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-16 text-[#94A3B8]">
              <div className="w-16 h-16 rounded-[14px] bg-[#8B5CF6]/10 border border-[#8B5CF6]/20 flex items-center justify-center mb-4">
                <Shield size={28} className="text-[#8B5CF6]" />
              </div>
              <p className="text-sm font-medium text-[#E2E8F0]">Module en cours de développement</p>
              <p className="text-xs text-[#94A3B8] mt-1">Les signatures électroniques seront disponibles prochainement</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Onglet Audit Logs */}
      {activeTab === "audit" && (
        <Card className="bg-[#1E293B] border border-white/8 rounded-[14px] shadow-none">
          <CardHeader className="border-b border-white/8 pb-4">
            <CardTitle className="text-[#E2E8F0] text-base font-semibold">Logs d'audit</CardTitle>
            <p className="text-[#94A3B8] text-sm">Historique des actions et modifications</p>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/8">
                    <th className="text-left py-3 px-5 text-xs font-semibold text-[#94A3B8] uppercase tracking-wide">Action</th>
                    <th className="text-left py-3 px-5 text-xs font-semibold text-[#94A3B8] uppercase tracking-wide">Entité</th>
                    <th className="text-left py-3 px-5 text-xs font-semibold text-[#94A3B8] uppercase tracking-wide">ID</th>
                    <th className="text-left py-3 px-5 text-xs font-semibold text-[#94A3B8] uppercase tracking-wide">Utilisateur</th>
                    <th className="text-left py-3 px-5 text-xs font-semibold text-[#94A3B8] uppercase tracking-wide">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs?.map((log, i) => (
                    <tr
                      key={log.log_id}
                      className={`border-b border-white/5 transition-colors hover:bg-white dark:bg-[#0b1e30]/3 ${i % 2 === 0 ? "" : "bg-white dark:bg-[#0b1e30]/[0.02]"}`}
                    >
                      <td className="py-3.5 px-5">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[#3B82F6]/15 text-[#3B82F6] border border-[#3B82F6]/20">
                          {log.action}
                        </span>
                      </td>
                      <td className="py-3.5 px-5 text-sm text-[#E2E8F0] capitalize">{log.entite_type}</td>
                      <td className="py-3.5 px-5 text-sm font-mono text-[#94A3B8]">{log.entite_id}</td>
                      <td className="py-3.5 px-5 text-sm text-[#E2E8F0]">{log.user_id}</td>
                      <td className="py-3.5 px-5 text-sm text-[#94A3B8]">
                        {new Date(log.date_action).toLocaleString("fr-FR")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {(!auditLogs || auditLogs.length === 0) && (
                <div className="flex flex-col items-center justify-center py-16 text-[#94A3B8]">
                  <History size={40} className="mb-3 opacity-30" />
                  <p className="text-sm">Aucun log d'audit disponible</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default WorkflowApprovals;
