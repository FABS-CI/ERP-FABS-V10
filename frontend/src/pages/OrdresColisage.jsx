import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { useNavigate } from "react-router-dom";
import {
  Package, Search, Plus, Eye, CheckCircle, Clock, AlertCircle,
  BarChart3, Truck, Box, RefreshCw
} from "lucide-react";
import {
  listOrdresColisage, getDashboardColisage, createOrdreColisage, updateOrdreColisageStatut
} from "@/services/colisageService";
import { getFactures } from "@/services/facturesApi";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/hooks/useAuth";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { toast } from "sonner";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/layout/PageHeader";

const STATUT_CONFIG = {
  a_coliser: { label: "À coliser", color: "bg-yellow-100 text-yellow-800", icon: Clock },
  en_preparation: { label: "En préparation", color: "bg-blue-100 text-blue-800", icon: Package },
  colisage_termine: { label: "Colisage terminé", color: "bg-purple-100 text-purple-800", icon: CheckCircle },
  livre: { label: "Livré", color: "bg-green-100 text-green-800", icon: Truck },
  expedie: { label: "Expédié", color: "bg-indigo-100 text-indigo-800", icon: Truck },
  cloture: { label: "Clôturé", color: "bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-white/90", icon: CheckCircle },
  annule: { label: "Annulé", color: "bg-red-100 text-red-800", icon: AlertCircle },
};

const STATUT_TRANSITIONS = {
  a_coliser: ["en_preparation", "annule"],
  en_preparation: ["colisage_termine", "a_coliser", "annule"],
  colisage_termine: ["livre", "expedie", "cloture"],
  livre: ["cloture"],
  expedie: ["cloture"],
};

const StatutBadge = ({ statut }) => {
  const cfg = STATUT_CONFIG[statut] || { label: statut, color: "bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-white/90" };
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.color}`}>
      {cfg.label}
    </span>
  );
};

const KPICard = ({ title, value, subtitle, color, Icon }) => (
  <Card>
    <CardContent className="p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500 dark:text-white/50">{title}</p>
          <p className={`text-2xl font-bold ${color}`}>{value ?? "—"}</p>
          {subtitle && <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>}
        </div>
        <div className={`p-2 rounded-lg bg-gray-50 dark:bg-white/5`}>
          <Icon className="w-5 h-5 text-gray-400" />
        </div>
      </div>
    </CardContent>
  </Card>
);

export default function OrdresColisage({ hubMode = false } = {}) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [statutFilter, setStatutFilter] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [facturesEmises, setFacturesEmises] = useState([]);

  useEffect(() => {
    if (showCreate) {
      getFactures({ statut: "emise", limit: 100 })
        .then((data) => setFacturesEmises(Array.isArray(data) ? data : data?.items || []))
        .catch(() => setFacturesEmises([]));
    }
  }, [showCreate]);
  const [showTransition, setShowTransition] = useState(null);
  const [transitionStatut, setTransitionStatut] = useState("");
  const [transitionNotes, setTransitionNotes] = useState("");
  const debouncedSearch = useDebouncedValue(search, 350);

  const [formData, setFormData] = useState({
    facture_id: "",
    notes: "",
    priorite: "normale",
    mode_expedition_prevu: "livraison_directe",
  });

  const { data: dashboard } = useQuery(
    ["colisage-dashboard"],
    getDashboardColisage,
    { enabled: !!user, staleTime: 30000 }
  );

  const { data: ordresList, isLoading } = useQuery(
    ["ordres-colisage", debouncedSearch, statutFilter],
    () => listOrdresColisage({ q: debouncedSearch, statut: statutFilter, limit: 50 }),
    { enabled: !!user }
  );

  const createMutation = useMutation(createOrdreColisage, {
    onSuccess: (data) => {
      queryClient.invalidateQueries(["ordres-colisage"]);
      queryClient.invalidateQueries(["colisage-dashboard"]);
      toast.success(`Ordre ${data.reference} créé`);
      setShowCreate(false);
      setFormData({ facture_id: "", notes: "", priorite: "normale", mode_expedition_prevu: "livraison_directe" });
    },
    onError: (err) => {
      toast.error(err?.response?.data?.detail || "Erreur lors de la création");
    },
  });

  const statutMutation = useMutation(
    ({ ordreId, statut, notes }) => updateOrdreColisageStatut(ordreId, statut, notes),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(["ordres-colisage"]);
        queryClient.invalidateQueries(["colisage-dashboard"]);
        toast.success("Statut mis à jour");
        setShowTransition(null);
        setTransitionStatut("");
        setTransitionNotes("");
      },
      onError: (err) => {
        toast.error(err?.response?.data?.detail || "Erreur");
      },
    }
  );

  const ordres = ordresList?.items || ordresList || [];
  const dash = dashboard || {};

  const Wrapper = hubMode ? React.Fragment : DashboardLayout;
  return (
    <Wrapper>
      <div className="space-y-6">
        <PageHeader
          title="Ordres de Colisage"
          description="Gestion du conditionnement et préparation des expéditions"
          icon={Package}
          accentColor="#F97316"
          favoriteKey="ordres_colisage"
          actions={
            <Button onClick={() => setShowCreate(true)} className="gap-2">
              <Plus className="w-4 h-4" /> Nouvel ordre
            </Button>
          }
        />

        {/* KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPICard
            title="À coliser"
            value={dash.a_coliser ?? 0}
            color="text-yellow-600"
            Icon={Clock}
          />
          <KPICard
            title="En préparation"
            value={dash.en_preparation ?? 0}
            color="text-blue-600"
            Icon={Package}
          />
          <KPICard
            title="Terminés"
            value={dash.colisage_termine ?? 0}
            color="text-purple-600"
            Icon={CheckCircle}
          />
          <KPICard
            title="Livrés/Expédiés"
            value={(dash.livre ?? 0) + (dash.expedie ?? 0)}
            color="text-green-600"
            Icon={Truck}
          />
        </div>

        {/* Filtres */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Rechercher par référence, facture, client..."
              className="pl-9"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select
            className="border rounded-md px-3 py-2 text-sm bg-white dark:bg-[#0b1e30]"
            value={statutFilter}
            onChange={(e) => setStatutFilter(e.target.value)}
          >
            <option value="">Tous les statuts</option>
            {Object.entries(STATUT_CONFIG).map(([k, v]) => (
              <option key={k} value={k}>{v.label}</option>
            ))}
          </select>
          <Button variant="outline" size="icon" onClick={() => queryClient.invalidateQueries(["ordres-colisage"])}>
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>

        {/* Liste */}
        <Card>
          <CardContent className="p-0">
            {isLoading ? (
              <div className="flex items-center justify-center h-32 text-gray-400">
                <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Chargement...
              </div>
            ) : ordres.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-32 text-gray-400">
                <Box className="w-8 h-8 mb-2" />
                <p className="text-sm">Aucun ordre de colisage</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-white/70">
                      <th className="text-left px-4 py-3 font-medium">Référence</th>
                      <th className="text-left px-4 py-3 font-medium">Facture</th>
                      <th className="text-left px-4 py-3 font-medium">Client</th>
                      <th className="text-left px-4 py-3 font-medium">Mode</th>
                      <th className="text-left px-4 py-3 font-medium">Cartons</th>
                      <th className="text-left px-4 py-3 font-medium">Statut</th>
                      <th className="text-left px-4 py-3 font-medium">Créé le</th>
                      <th className="text-right px-4 py-3 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ordres.map((ordre) => {
                      const transitions = STATUT_TRANSITIONS[ordre.statut] || [];
                      return (
                        <tr key={ordre._id || ordre.ordre_id} className="border-b hover:bg-gray-50 dark:bg-white/5 transition-colors">
                          <td className="px-4 py-3 font-mono text-xs font-medium text-orange-700">
                            {ordre.reference}
                          </td>
                          <td className="px-4 py-3 text-xs text-gray-600 dark:text-white/70">{ordre.facture_reference || ordre.facture_id}</td>
                          <td className="px-4 py-3 text-sm">{ordre.client_nom || "—"}</td>
                          <td className="px-4 py-3 text-xs text-gray-500 dark:text-white/50 capitalize">
                            {ordre.mode_expedition_prevu?.replace("_", " ") || "—"}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className="inline-flex items-center gap-1 text-sm">
                              <Box className="w-3.5 h-3.5 text-gray-400" />
                              {ordre.nb_cartons ?? 0}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <StatutBadge statut={ordre.statut} />
                          </td>
                          <td className="px-4 py-3 text-xs text-gray-500 dark:text-white/50">
                            {ordre.date_creation
                              ? new Date(ordre.date_creation).toLocaleDateString("fr-CI")
                              : "—"}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-7 px-2 gap-1 text-xs"
                                onClick={() => navigate(`/ordres-colisage/${ordre._id || ordre.ordre_id}`)}
                              >
                                <Eye className="w-3 h-3" /> Détail
                              </Button>
                              {transitions.length > 0 && (
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  className="h-7 px-2 text-xs"
                                  onClick={() => {
                                    setShowTransition(ordre);
                                    setTransitionStatut(transitions[0]);
                                  }}
                                >
                                  Avancer
                                </Button>
                              )}
                            </div>
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

        {/* Dialog création manuelle */}
        <Dialog open={showCreate} onOpenChange={setShowCreate}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Nouvel Ordre de Colisage</DialogTitle>
              <DialogDescription>
                Créer manuellement un ordre (les OC sont aussi créés automatiquement à l'émission de facture)
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="facture_id">Facture *</Label>
                <Select
                  value={formData.facture_id}
                  onValueChange={(v) => setFormData({ ...formData, facture_id: v })}
                >
                  <SelectTrigger id="facture_id">
                    <SelectValue placeholder={facturesEmises.length ? "Sélectionner une facture…" : "Chargement…"} />
                  </SelectTrigger>
                  <SelectContent>
                    {facturesEmises.map((f) => (
                      <SelectItem key={f.facture_id} value={f.facture_id}>
                        {f.reference || f.facture_id} — {f.client_nom || f.client_id}
                      </SelectItem>
                    ))}
                    {facturesEmises.length === 0 && (
                      <SelectItem value="__none__" disabled>Aucune facture émise</SelectItem>
                    )}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Mode d'expédition</Label>
                <select
                  className="w-full border rounded-md px-3 py-2 text-sm mt-1"
                  value={formData.mode_expedition_prevu}
                  onChange={(e) => setFormData({ ...formData, mode_expedition_prevu: e.target.value })}
                >
                  <option value="livraison_directe">Livraison directe (Abidjan)</option>
                  <option value="expedition">Expédition (ville distante)</option>
                </select>
              </div>
              <div>
                <Label>Priorité</Label>
                <select
                  className="w-full border rounded-md px-3 py-2 text-sm mt-1"
                  value={formData.priorite}
                  onChange={(e) => setFormData({ ...formData, priorite: e.target.value })}
                >
                  <option value="basse">Basse</option>
                  <option value="normale">Normale</option>
                  <option value="haute">Haute</option>
                  <option value="urgente">Urgente</option>
                </select>
              </div>
              <div>
                <Label>Notes</Label>
                <Textarea
                  placeholder="Instructions particulières..."
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows={2}
                />
              </div>
              <div className="flex gap-2 justify-end pt-2">
                <Button variant="outline" onClick={() => setShowCreate(false)}>Annuler</Button>
                <Button
                  onClick={() => createMutation.mutate(formData)}
                  disabled={!formData.facture_id || createMutation.isLoading}
                >
                  {createMutation.isLoading ? "Création..." : "Créer"}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Dialog transition statut */}
        <Dialog open={!!showTransition} onOpenChange={(open) => !open && setShowTransition(null)}>
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle>Changer le statut</DialogTitle>
              <DialogDescription>Ordre: {showTransition?.reference}</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Nouveau statut</Label>
                <select
                  className="w-full border rounded-md px-3 py-2 text-sm mt-1"
                  value={transitionStatut}
                  onChange={(e) => setTransitionStatut(e.target.value)}
                >
                  {(STATUT_TRANSITIONS[showTransition?.statut] || []).map((s) => (
                    <option key={s} value={s}>{STATUT_CONFIG[s]?.label || s}</option>
                  ))}
                </select>
              </div>
              <div>
                <Label>Notes (optionnel)</Label>
                <Textarea
                  value={transitionNotes}
                  onChange={(e) => setTransitionNotes(e.target.value)}
                  rows={2}
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setShowTransition(null)}>Annuler</Button>
                <Button
                  onClick={() =>
                    statutMutation.mutate({
                      ordreId: showTransition._id || showTransition.ordre_id,
                      statut: transitionStatut,
                      notes: transitionNotes || null,
                    })
                  }
                  disabled={!transitionStatut || statutMutation.isLoading}
                >
                  Confirmer
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </Wrapper>
  );
}
