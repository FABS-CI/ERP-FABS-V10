import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import {
  AlertTriangle, Search, RefreshCw, Truck, Package,
  Calendar, User, MapPin, FileText, CheckCircle2,
} from "lucide-react";
import { listIncidents, updateIncidentResolution } from "@/services/colisageService";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/layout/PageHeader";

const SOURCE_CONFIG = {
  livraison:  { label: "Livraison",   color: "bg-blue-100 text-blue-800",   icon: Truck },
  expedition: { label: "Expédition",  color: "bg-purple-100 text-purple-800", icon: Package },
};

const TYPE_CONFIG = {
  retard:          { label: "Retard",           color: "bg-yellow-100 text-yellow-800" },
  avarie:          { label: "Avarie",           color: "bg-red-100 text-red-800" },
  manquant:        { label: "Manquant",         color: "bg-orange-100 text-orange-800" },
  erreur_adresse:  { label: "Erreur adresse",   color: "bg-pink-100 text-pink-800" },
  client_absent:   { label: "Client absent",    color: "bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-white/90" },
  refus:           { label: "Refus",            color: "bg-red-100 text-red-800" },
  autre:           { label: "Autre",            color: "bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-white/90" },
};

const SourceBadge = ({ source }) => {
  const cfg = SOURCE_CONFIG[source] || { label: source, color: "bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-white/90", icon: AlertTriangle };
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.color}`}>
      <Icon className="w-3 h-3" />
      {cfg.label}
    </span>
  );
};

const TypeBadge = ({ type }) => {
  const cfg = TYPE_CONFIG[type] || { label: type || "—", color: "bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-white/90" };
  return (
    <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.color}`}>
      {cfg.label}
    </span>
  );
};

const RESOLUTION_CONFIG = {
  ouvert:      { label: "Ouvert",      color: "bg-red-100 text-red-800" },
  en_cours:    { label: "En cours",    color: "bg-yellow-100 text-yellow-800" },
  resolu:      { label: "Résolu",      color: "bg-green-100 text-green-800" },
  clos:        { label: "Clos",        color: "bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-white/70" },
};

const ResolutionBadge = ({ statut }) => {
  const cfg = RESOLUTION_CONFIG[statut] || { label: statut || "—", color: "bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-white/70" };
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${cfg.color}`}>
      {cfg.label}
    </span>
  );
};

export default function Incidents({ hubMode = false } = {}) {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [resolveTarget, setResolveTarget] = useState(null); // { inc, document_id, source }
  const [resolveForm, setResolveForm] = useState({ statut_resolution: "en_cours", commentaire: "" });

  const resolveMutation = useMutation(updateIncidentResolution, {
    onSuccess: () => {
      toast.success("Incident mis à jour");
      setResolveTarget(null);
      queryClient.invalidateQueries(["incidents"]);
    },
    onError: (err) => toast.error(err?.response?.data?.detail || "Erreur mise à jour"),
  });

  const { data: incidents = [], isLoading, refetch } = useQuery(
    ["incidents", sourceFilter, typeFilter],
    () => listIncidents({
      ...(sourceFilter ? { source: sourceFilter } : {}),
      ...(typeFilter ? { type_incident: typeFilter } : {}),
      limit: 300,
    }),
    { staleTime: 30000 }
  );

  const filtered = incidents.filter((inc) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      (inc.document_reference || "").toLowerCase().includes(q) ||
      (inc.client_nom || "").toLowerCase().includes(q) ||
      (inc.ville || "").toLowerCase().includes(q) ||
      (inc.description || "").toLowerCase().includes(q) ||
      (inc.declare_par || "").toLowerCase().includes(q)
    );
  });

  // Stats rapides
  const stats = {
    total: incidents.length,
    livraisons: incidents.filter((i) => i.source === "livraison").length,
    expeditions: incidents.filter((i) => i.source === "expedition").length,
    types: [...new Set(incidents.map((i) => i.type_incident).filter(Boolean))],
  };

  const typeOptions = [
    { value: "", label: "Tous les types" },
    ...Object.entries(TYPE_CONFIG).map(([k, v]) => ({ value: k, label: v.label })),
  ];

  const Wrapper = hubMode ? React.Fragment : DashboardLayout;
  return (
    <Wrapper>
      <PageHeader
        title="Incidents logistiques"
        description="Vue consolidée de tous les incidents déclarés"
        icon={AlertTriangle}
      />

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="pt-4">
            <div className="text-2xl font-bold text-red-600">{stats.total}</div>
            <div className="text-sm text-gray-500 dark:text-white/50">Total incidents</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-2xl font-bold text-blue-600">{stats.livraisons}</div>
            <div className="text-sm text-gray-500 dark:text-white/50">Livraisons</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-2xl font-bold text-purple-600">{stats.expeditions}</div>
            <div className="text-sm text-gray-500 dark:text-white/50">Expéditions</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-2xl font-bold text-orange-600">{stats.types.length}</div>
            <div className="text-sm text-gray-500 dark:text-white/50">Types distincts</div>
          </CardContent>
        </Card>
      </div>

      {/* Filtres */}
      <Card className="mb-6">
        <CardContent className="pt-4">
          <div className="flex flex-wrap gap-3 items-center">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                className="pl-9"
                placeholder="Rechercher ref, client, ville, description..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <select
              className="border rounded-md px-3 py-2 text-sm"
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
            >
              <option value="">Toutes les sources</option>
              <option value="livraison">Livraisons</option>
              <option value="expedition">Expéditions</option>
            </select>
            <select
              className="border rounded-md px-3 py-2 text-sm"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              {typeOptions.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
            <Button variant="outline" size="icon" onClick={refetch} title="Actualiser">
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Liste */}
      {isLoading ? (
        <div className="flex items-center justify-center h-48 text-gray-500 dark:text-white/50">
          <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Chargement...
        </div>
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center h-48 text-gray-500 dark:text-white/50">
            <AlertTriangle className="w-8 h-8 mb-2 text-gray-300" />
            <p>Aucun incident trouvé</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filtered.map((inc, idx) => (
            <Card key={idx} className="border-l-4 border-l-red-400">
              <CardContent className="pt-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  {/* Infos principale */}
                  <div className="flex-1 min-w-[200px]">
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <SourceBadge source={inc.source} />
                      <TypeBadge type={inc.type_incident} />
                      <span className="text-sm font-semibold text-gray-800 dark:text-white">
                        {inc.document_reference || inc.document_id}
                      </span>
                    </div>
                    {inc.description && (
                      <p className="text-sm text-gray-700 dark:text-white/90 mb-2 flex items-start gap-1">
                        <FileText className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-400" />
                        {inc.description}
                      </p>
                    )}
                    <div className="flex flex-wrap gap-4 text-xs text-gray-500 dark:text-white/50">
                      {inc.client_nom && (
                        <span className="flex items-center gap-1">
                          <User className="w-3 h-3" /> {inc.client_nom}
                        </span>
                      )}
                      {inc.ville && (
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3 h-3" /> {inc.ville}
                        </span>
                      )}
                      {inc.declare_par && (
                        <span className="flex items-center gap-1">
                          <User className="w-3 h-3" /> Déclaré par : {inc.declare_par}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Date + statut + actions */}
                  <div className="flex flex-col items-end gap-2 text-right">
                    {inc.date && (
                      <span className="flex items-center gap-1 text-xs text-gray-500 dark:text-white/50">
                        <Calendar className="w-3 h-3" />
                        {new Date(inc.date).toLocaleDateString("fr-FR", {
                          day: "2-digit", month: "short", year: "numeric",
                          hour: "2-digit", minute: "2-digit",
                        })}
                      </span>
                    )}
                    <ResolutionBadge statut={inc.statut_resolution || "ouvert"} />
                    {inc.statut_document && (
                      <span className="text-xs text-gray-400 italic">
                        Statut doc : {inc.statut_document}
                      </span>
                    )}
                    {inc.incident_id && inc.statut_resolution !== "clos" && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-xs h-7 px-2"
                        onClick={() => {
                          setResolveTarget({ inc, document_id: inc.document_id, source: inc.source });
                          setResolveForm({ statut_resolution: inc.statut_resolution === "ouvert" ? "en_cours" : "resolu", commentaire: "" });
                        }}
                      >
                        <CheckCircle2 className="w-3 h-3 mr-1" /> Résoudre
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {filtered.length > 0 && (
        <p className="text-xs text-gray-400 mt-4 text-center">
          {filtered.length} incident{filtered.length > 1 ? "s" : ""} affiché{filtered.length > 1 ? "s" : ""}
          {search || sourceFilter || typeFilter ? " (filtré)" : ""}
        </p>
      )}

      {/* Dialog résolution incident */}
      <Dialog open={!!resolveTarget} onOpenChange={(open) => !open && setResolveTarget(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Résoudre l'incident</DialogTitle>
          </DialogHeader>
          {resolveTarget && (
            <div className="space-y-4 py-2">
              <div className="text-sm text-gray-600 dark:text-white/70 bg-gray-50 dark:bg-white/5 rounded p-3">
                <span className="font-medium">{resolveTarget.inc.document_reference || resolveTarget.inc.document_id}</span>
                {" — "}{resolveTarget.inc.type_incident}
                {resolveTarget.inc.description && <p className="text-xs mt-1 text-gray-500 dark:text-white/50">{resolveTarget.inc.description}</p>}
              </div>
              <div>
                <Label>Statut de résolution</Label>
                <select
                  className="w-full border rounded-md px-3 py-2 text-sm mt-1"
                  value={resolveForm.statut_resolution}
                  onChange={(e) => setResolveForm({ ...resolveForm, statut_resolution: e.target.value })}
                >
                  <option value="en_cours">En cours</option>
                  <option value="resolu">Résolu</option>
                  <option value="clos">Clos</option>
                </select>
              </div>
              <div>
                <Label>Commentaire</Label>
                <Textarea
                  placeholder="Actions effectuées, notes de suivi..."
                  value={resolveForm.commentaire}
                  onChange={(e) => setResolveForm({ ...resolveForm, commentaire: e.target.value })}
                  rows={3}
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setResolveTarget(null)}>Annuler</Button>
            <Button
              onClick={() => resolveMutation.mutate({
                source: resolveTarget.source,
                document_id: resolveTarget.document_id,
                incident_id: resolveTarget.inc.incident_id,
                statut_resolution: resolveForm.statut_resolution,
                commentaire: resolveForm.commentaire,
              })}
              disabled={resolveMutation.isLoading}
            >
              {resolveMutation.isLoading ? "Enregistrement..." : "Enregistrer"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Wrapper>
  );
}
