import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import {
  Truck, Search, Plus, CheckCircle, AlertTriangle,
  MapPin, RefreshCw, Package, RotateCcw, Phone, X
} from "lucide-react";
import {
  listExpeditionsColisage, createExpeditionColisage, updateExpeditionColisageStatut,
  receptionnerExpedition, recupererExpedition, signalerIncidentExpedition
} from "@/services/colisageService";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/hooks/useAuth";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { toast } from "sonner";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/layout/PageHeader";

const STATUT_CONFIG = {
  en_preparation: { label: "Préparation", color: "bg-yellow-100 text-yellow-800" },
  expedie: { label: "Expédié", color: "bg-indigo-100 text-indigo-800" },
  en_transit: { label: "En transit", color: "bg-blue-100 text-blue-800" },
  arrive_destination: { label: "Arrivé dest.", color: "bg-purple-100 text-purple-800" },
  receptionne: { label: "Réceptionné", color: "bg-green-100 text-green-800" },
  recuperation: { label: "Récupération", color: "bg-orange-100 text-orange-800" },
  recupere: { label: "Récupéré", color: "bg-gray-100 dark:bg-white/10 text-gray-800 dark:text-white" },
  incident: { label: "Incident", color: "bg-red-100 text-red-800" },
  cloture: { label: "Clôturé", color: "bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-white/90" },
};

const STATUT_TRANSITIONS = {
  en_preparation: ["expedie", "cloture"],
  expedie: ["en_transit", "arrive_destination", "incident"],
  en_transit: ["arrive_destination", "incident"],
  arrive_destination: ["receptionne", "recuperation", "incident"],
  recuperation: ["recupere"],
};

const TRANSPORTEURS = [
  "CTI (Compagnie de Transport Ivoirien)", "STS", "SETV",
  "SOTRA Fret", "Transit Express CI", "FedEx CI", "DHL CI", "Autre"
];

const VILLES_CI = [
  "Bouaké", "Daloa", "Korhogo", "Man", "San-Pédro", "Yamoussoukro",
  "Divo", "Gagnoa", "Abengourou", "Bondoukou", "Odienné", "Touba",
  "Ferkessédougou", "Katiola", "Séguéla", "Grand-Bassam", "Jacqueville"
];

const StatutBadge = ({ statut }) => {
  const cfg = STATUT_CONFIG[statut] || { label: statut, color: "bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-white/90" };
  return <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.color}`}>{cfg.label}</span>;
};

export default function Expeditions({ hubMode = false } = {}) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [statutFilter, setStatutFilter] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [showStatut, setShowStatut] = useState(null);
  const [showReception, setShowReception] = useState(null);
  const [showRecuperation, setShowRecuperation] = useState(null);
  const [showIncident, setShowIncident] = useState(null);
  const [newStatut, setNewStatut] = useState("");
  const [statutNotes, setStatutNotes] = useState("");
  const debouncedSearch = useDebouncedValue(search, 350);

  const [formData, setFormData] = useState({
    ordre_colisage_id: "",
    transporteur: "",
    numero_tracking: "",
    ville_destination: "",
    adresse_destination: { nom: "", adresse: "", telephone: "" },
    date_expedition_prevue: "",
    date_livraison_prevue: "",
    frais_transport: "",
    notes: "",
  });

  const [receptionData, setReceptionData] = useState({ signature: "", commentaire: "" });
  const [recupData, setRecupData] = useState({ motif: "", responsable: "" });
  const [incidentData, setIncidentData] = useState({ type_incident: "retard", description: "" });

  const { data: expeditionsList, isLoading } = useQuery(
    ["expeditions-colisage", debouncedSearch, statutFilter],
    () => listExpeditionsColisage({ q: debouncedSearch, statut: statutFilter, limit: 50 }),
    { enabled: !!user }
  );

  const createMutation = useMutation(createExpeditionColisage, {
    onSuccess: (data) => {
      queryClient.invalidateQueries(["expeditions-colisage"]);
      toast.success(`Expédition ${data.reference} créée`);
      setShowCreate(false);
      setFormData({
        ordre_colisage_id: "", transporteur: "", numero_tracking: "", ville_destination: "",
        adresse_destination: { nom: "", adresse: "", telephone: "" },
        date_expedition_prevue: "", date_livraison_prevue: "", frais_transport: "", notes: "",
      });
    },
    onError: (err) => toast.error(err?.response?.data?.detail || "Erreur"),
  });

  const statutMutation = useMutation(
    ({ id, statut, notes }) => updateExpeditionColisageStatut(id, statut, notes),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(["expeditions-colisage"]);
        toast.success("Statut mis à jour");
        setShowStatut(null);
      },
      onError: (err) => toast.error(err?.response?.data?.detail || "Erreur"),
    }
  );

  const receptionMutation = useMutation(
    ({ id, data }) => receptionnerExpedition(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(["expeditions-colisage"]);
        toast.success("Réception enregistrée");
        setShowReception(null);
      },
      onError: (err) => toast.error(err?.response?.data?.detail || "Erreur"),
    }
  );

  const recupMutation = useMutation(
    ({ id, data }) => recupererExpedition(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(["expeditions-colisage"]);
        toast.success("Récupération enregistrée");
        setShowRecuperation(null);
      },
      onError: (err) => toast.error(err?.response?.data?.detail || "Erreur"),
    }
  );

  const incidentMutation = useMutation(
    ({ id, data }) => signalerIncidentExpedition(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(["expeditions-colisage"]);
        toast.success("Incident signalé");
        setShowIncident(null);
      },
      onError: (err) => toast.error(err?.response?.data?.detail || "Erreur"),
    }
  );

  const expeditions = expeditionsList?.items || expeditionsList || [];

  const stats = {
    en_cours: expeditions.filter((e) => ["expedie", "en_transit"].includes(e.statut)).length,
    arrives: expeditions.filter((e) => e.statut === "arrive_destination").length,
    receptionnes: expeditions.filter((e) => e.statut === "receptionne").length,
    incidents: expeditions.filter((e) => e.statut === "incident").length,
  };

  const Wrapper = hubMode ? React.Fragment : DashboardLayout;
  return (
    <Wrapper>
      <div className="space-y-6">
        <PageHeader
          title="Expéditions"
          description="Transport vers villes distantes — suivi, réception et récupération"
          icon={Truck}
          accentColor="#6366F1"
          favoriteKey="expeditions"
          actions={
            <Button onClick={() => setShowCreate(true)} className="gap-2">
              <Plus className="w-4 h-4" /> Nouvelle expédition
            </Button>
          }
        />

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: "En cours", val: stats.en_cours, color: "text-indigo-600", icon: Truck },
            { label: "À destination", val: stats.arrives, color: "text-purple-600", icon: MapPin },
            { label: "Réceptionnés", val: stats.receptionnes, color: "text-green-600", icon: CheckCircle },
            { label: "Incidents", val: stats.incidents, color: "text-red-600", icon: AlertTriangle },
          ].map(({ label, val, color, icon: Icon }) => (
            <Card key={label}>
              <CardContent className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-500 dark:text-white/50">{label}</p>
                  <p className={`text-xl font-bold ${color}`}>{val}</p>
                </div>
                <Icon className="w-5 h-5 text-gray-300" />
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Filtres */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Référence, transporteur, ville..."
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
          <Button variant="outline" size="icon" onClick={() => queryClient.invalidateQueries(["expeditions-colisage"])}>
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>

        {/* Tableau */}
        <Card>
          <CardContent className="p-0">
            {isLoading ? (
              <div className="flex items-center justify-center h-32 text-gray-400">
                <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Chargement...
              </div>
            ) : expeditions.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-32 text-gray-400">
                <Truck className="w-8 h-8 mb-2" />
                <p className="text-sm">Aucune expédition</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-white/70">
                      <th className="text-left px-4 py-3 font-medium">Référence</th>
                      <th className="text-left px-4 py-3 font-medium">Destination</th>
                      <th className="text-left px-4 py-3 font-medium">Transporteur</th>
                      <th className="text-left px-4 py-3 font-medium">Tracking</th>
                      <th className="text-left px-4 py-3 font-medium">Date prévue</th>
                      <th className="text-left px-4 py-3 font-medium">Statut</th>
                      <th className="text-right px-4 py-3 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {expeditions.map((exp) => {
                      const transitions = STATUT_TRANSITIONS[exp.statut] || [];
                      return (
                        <tr key={exp._id || exp.expedition_id} className="border-b hover:bg-gray-50 dark:bg-white/5">
                          <td className="px-4 py-3 font-mono text-xs font-medium text-indigo-700">{exp.reference}</td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1">
                              <MapPin className="w-3 h-3 text-gray-400" />
                              <span>{exp.ville_destination || exp.adresse_destination?.nom || "—"}</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-xs">{exp.transporteur || "—"}</td>
                          <td className="px-4 py-3 text-xs font-mono text-gray-600 dark:text-white/70">{exp.numero_tracking || "—"}</td>
                          <td className="px-4 py-3 text-xs text-gray-500 dark:text-white/50">
                            {exp.date_livraison_prevue
                              ? new Date(exp.date_livraison_prevue).toLocaleDateString("fr-CI")
                              : "—"}
                          </td>
                          <td className="px-4 py-3"><StatutBadge statut={exp.statut} /></td>
                          <td className="px-4 py-3">
                            <div className="flex items-center justify-end gap-1">
                              {transitions.length > 0 && (
                                <Button size="sm" variant="outline" className="h-7 px-2 text-xs"
                                  onClick={() => { setShowStatut(exp); setNewStatut(transitions[0]); }}>
                                  Avancer
                                </Button>
                              )}
                              {exp.statut === "arrive_destination" && (
                                <Button size="sm" variant="outline"
                                  className="h-7 px-2 text-xs text-green-700 border-green-300"
                                  onClick={() => setShowReception(exp)}>
                                  <CheckCircle className="w-3 h-3 mr-1" /> Réceptionner
                                </Button>
                              )}
                              {exp.statut === "arrive_destination" && (
                                <Button size="sm" variant="outline"
                                  className="h-7 px-2 text-xs text-orange-700 border-orange-300"
                                  onClick={() => setShowRecuperation(exp)}>
                                  <RotateCcw className="w-3 h-3 mr-1" /> Récupération
                                </Button>
                              )}
                              {["expedie", "en_transit", "arrive_destination"].includes(exp.statut) && (
                                <Button size="sm" variant="ghost"
                                  className="h-7 px-2 text-xs text-red-600"
                                  onClick={() => setShowIncident(exp)}>
                                  <AlertTriangle className="w-3 h-3" />
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

        {/* Dialog créer */}
        <Dialog open={showCreate} onOpenChange={setShowCreate}>
          <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Nouvelle Expédition</DialogTitle>
              <DialogDescription>Villes hors Abidjan</DialogDescription>
            </DialogHeader>
            <div className="space-y-3">
              <div>
                <Label>ID Ordre de colisage *</Label>
                <Input
                  placeholder="oc_xxxxx"
                  value={formData.ordre_colisage_id}
                  onChange={(e) => setFormData({ ...formData, ordre_colisage_id: e.target.value })}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label>Transporteur *</Label>
                  <select
                    className="w-full border rounded-md px-3 py-2 text-sm mt-1"
                    value={formData.transporteur}
                    onChange={(e) => setFormData({ ...formData, transporteur: e.target.value })}
                  >
                    <option value="">Sélectionner</option>
                    {TRANSPORTEURS.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div>
                  <Label>N° Tracking</Label>
                  <Input
                    value={formData.numero_tracking}
                    onChange={(e) => setFormData({ ...formData, numero_tracking: e.target.value })}
                  />
                </div>
              </div>
              <div>
                <Label>Ville destination *</Label>
                <select
                  className="w-full border rounded-md px-3 py-2 text-sm mt-1"
                  value={formData.ville_destination}
                  onChange={(e) => setFormData({ ...formData, ville_destination: e.target.value })}
                >
                  <option value="">Sélectionner</option>
                  {VILLES_CI.map((v) => <option key={v} value={v}>{v}</option>)}
                  <option value="autre">Autre</option>
                </select>
              </div>
              <hr />
              <p className="text-sm font-medium">Destinataire</p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label>Nom</Label>
                  <Input
                    value={formData.adresse_destination.nom}
                    onChange={(e) => setFormData({
                      ...formData,
                      adresse_destination: { ...formData.adresse_destination, nom: e.target.value }
                    })}
                  />
                </div>
                <div>
                  <Label>Téléphone</Label>
                  <Input
                    value={formData.adresse_destination.telephone}
                    onChange={(e) => setFormData({
                      ...formData,
                      adresse_destination: { ...formData.adresse_destination, telephone: e.target.value }
                    })}
                  />
                </div>
              </div>
              <div>
                <Label>Adresse</Label>
                <Input
                  value={formData.adresse_destination.adresse}
                  onChange={(e) => setFormData({
                    ...formData,
                    adresse_destination: { ...formData.adresse_destination, adresse: e.target.value }
                  })}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label>Date expédition</Label>
                  <Input type="date" value={formData.date_expedition_prevue}
                    onChange={(e) => setFormData({ ...formData, date_expedition_prevue: e.target.value })} />
                </div>
                <div>
                  <Label>Date livraison prévue</Label>
                  <Input type="date" value={formData.date_livraison_prevue}
                    onChange={(e) => setFormData({ ...formData, date_livraison_prevue: e.target.value })} />
                </div>
              </div>
              <div>
                <Label>Frais de transport (FCFA)</Label>
                <Input
                  type="number"
                  value={formData.frais_transport}
                  onChange={(e) => setFormData({ ...formData, frais_transport: e.target.value })}
                />
              </div>
              <div>
                <Label>Notes</Label>
                <Textarea value={formData.notes} onChange={(e) => setFormData({ ...formData, notes: e.target.value })} rows={2} />
              </div>
              <div className="flex gap-2 justify-end pt-2">
                <Button variant="outline" onClick={() => setShowCreate(false)}>Annuler</Button>
                <Button
                  onClick={() => createMutation.mutate({
                    ...formData,
                    frais_transport: formData.frais_transport ? parseFloat(formData.frais_transport) : null,
                  })}
                  disabled={!formData.ordre_colisage_id || !formData.transporteur || !formData.ville_destination || createMutation.isLoading}
                >
                  {createMutation.isLoading ? "Création..." : "Créer"}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Dialog statut */}
        <Dialog open={!!showStatut} onOpenChange={(open) => !open && setShowStatut(null)}>
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle>Changer statut</DialogTitle>
              <DialogDescription>{showStatut?.reference}</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Nouveau statut</Label>
                <select className="w-full border rounded-md px-3 py-2 text-sm mt-1"
                  value={newStatut} onChange={(e) => setNewStatut(e.target.value)}>
                  {(STATUT_TRANSITIONS[showStatut?.statut] || []).map((s) => (
                    <option key={s} value={s}>{STATUT_CONFIG[s]?.label || s}</option>
                  ))}
                </select>
              </div>
              <div>
                <Label>Notes</Label>
                <Textarea value={statutNotes} onChange={(e) => setStatutNotes(e.target.value)} rows={2} />
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setShowStatut(null)}>Annuler</Button>
                <Button
                  onClick={() => statutMutation.mutate({
                    id: showStatut._id || showStatut.expedition_id,
                    statut: newStatut, notes: statutNotes || null,
                  })}
                  disabled={statutMutation.isLoading}
                >Confirmer</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Dialog réception */}
        <Dialog open={!!showReception} onOpenChange={(open) => !open && setShowReception(null)}>
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle>Réceptionner l'expédition</DialogTitle>
              <DialogDescription>{showReception?.reference}</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Signature / réceptionnaire</Label>
                <Input value={receptionData.signature}
                  onChange={(e) => setReceptionData({ ...receptionData, signature: e.target.value })} />
              </div>
              <div>
                <Label>Commentaire</Label>
                <Textarea value={receptionData.commentaire}
                  onChange={(e) => setReceptionData({ ...receptionData, commentaire: e.target.value })} rows={2} />
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setShowReception(null)}>Annuler</Button>
                <Button className="bg-green-600 hover:bg-green-700"
                  onClick={() => receptionMutation.mutate({
                    id: showReception._id || showReception.expedition_id,
                    data: receptionData,
                  })}
                  disabled={receptionMutation.isLoading}>
                  <CheckCircle className="w-4 h-4 mr-1" /> Confirmer
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Dialog récupération */}
        <Dialog open={!!showRecuperation} onOpenChange={(open) => !open && setShowRecuperation(null)}>
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle>Récupération marchandise</DialogTitle>
              <DialogDescription>{showRecuperation?.reference}</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Motif *</Label>
                <Textarea value={recupData.motif}
                  onChange={(e) => setRecupData({ ...recupData, motif: e.target.value })} rows={2} />
              </div>
              <div>
                <Label>Responsable</Label>
                <Input value={recupData.responsable}
                  onChange={(e) => setRecupData({ ...recupData, responsable: e.target.value })} />
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setShowRecuperation(null)}>Annuler</Button>
                <Button variant="outline" className="border-orange-300 text-orange-700"
                  onClick={() => recupMutation.mutate({
                    id: showRecuperation._id || showRecuperation.expedition_id,
                    data: recupData,
                  })}
                  disabled={!recupData.motif || recupMutation.isLoading}>
                  <RotateCcw className="w-4 h-4 mr-1" /> Récupérer
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Dialog incident */}
        <Dialog open={!!showIncident} onOpenChange={(open) => !open && setShowIncident(null)}>
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle>Signaler un incident</DialogTitle>
              <DialogDescription>{showIncident?.reference}</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Type</Label>
                <select className="w-full border rounded-md px-3 py-2 text-sm mt-1"
                  value={incidentData.type_incident}
                  onChange={(e) => setIncidentData({ ...incidentData, type_incident: e.target.value })}>
                  <option value="retard">Retard</option>
                  <option value="colis_endommage">Colis endommagé</option>
                  <option value="perte">Perte / vol</option>
                  <option value="mauvaise_adresse">Mauvaise adresse</option>
                  <option value="refus">Refus réception</option>
                  <option value="autre">Autre</option>
                </select>
              </div>
              <div>
                <Label>Description *</Label>
                <Textarea value={incidentData.description}
                  onChange={(e) => setIncidentData({ ...incidentData, description: e.target.value })} rows={3} />
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setShowIncident(null)}>Annuler</Button>
                <Button variant="destructive"
                  onClick={() => incidentMutation.mutate({
                    id: showIncident._id || showIncident.expedition_id,
                    data: incidentData,
                  })}
                  disabled={!incidentData.description || incidentMutation.isLoading}>
                  <AlertTriangle className="w-4 h-4 mr-1" /> Signaler
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </Wrapper>
  );
}
