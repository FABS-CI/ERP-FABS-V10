import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import {
  Truck, Search, Plus, Eye, CheckCircle, AlertTriangle,
  MapPin, Phone, RefreshCw, Package, Clock, X
} from "lucide-react";
import {
  listLivraisons, createLivraison, updateLivraisonStatut,
  receptionnerLivraison, signalerIncidentLivraison, listCartons
} from "@/services/colisageService";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  chargement: { label: "Chargement", color: "bg-blue-100 text-blue-800" },
  en_route: { label: "En route", color: "bg-indigo-100 text-indigo-800" },
  arrive: { label: "Arrivé", color: "bg-purple-100 text-purple-800" },
  receptionne: { label: "Réceptionné", color: "bg-green-100 text-green-800" },
  incident: { label: "Incident", color: "bg-red-100 text-red-800" },
  cloture: { label: "Clôturé", color: "bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-white/90" },
};

const STATUT_TRANSITIONS = {
  en_preparation: ["chargement", "cloture"],
  chargement: ["en_route", "en_preparation"],
  en_route: ["arrive", "incident"],
  arrive: ["receptionne", "incident"],
  incident: ["en_route", "cloture"],
};

const StatutBadge = ({ statut }) => {
  const cfg = STATUT_CONFIG[statut] || { label: statut, color: "bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-white/90" };
  return <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.color}`}>{cfg.label}</span>;
};

const ZONES_ABIDJAN = [
  "Cocody", "Plateau", "Yopougon", "Treichville", "Adjamé", "Abobo",
  "Marcory", "Koumassi", "Port-Bouët", "Attécoubé", "Bingerville", "Anyama"
];

export default function LivraisonsDirectes({ hubMode = false } = {}) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [statutFilter, setStatutFilter] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [showDetail, setShowDetail] = useState(null);
  const [showStatut, setShowStatut] = useState(null);
  const [showReception, setShowReception] = useState(null);
  const [showIncident, setShowIncident] = useState(null);
  const [newStatut, setNewStatut] = useState("");
  const [statutNotes, setStatutNotes] = useState("");
  const debouncedSearch = useDebouncedValue(search, 350);

  const [formData, setFormData] = useState({
    ordre_colisage_id: "",
    livreur_nom: "",
    livreur_telephone: "",
    vehicule: "",
    adresse_livraison: { nom: "", adresse: "", zone: "", telephone: "" },
    date_livraison_prevue: "",
    notes: "",
  });

  const [receptionData, setReceptionData] = useState({
    signature_client: "",
    commentaire: "",
    cartons_recus: [],
  });

  const [incidentData, setIncidentData] = useState({
    type_incident: "retard",
    description: "",
  });

  const { data: livraisonsList, isLoading } = useQuery(
    ["livraisons-directes", debouncedSearch, statutFilter],
    () => listLivraisons({ q: debouncedSearch, statut: statutFilter, limit: 50 }),
    { enabled: !!user }
  );

  const createMutation = useMutation(createLivraison, {
    onSuccess: (data) => {
      queryClient.invalidateQueries(["livraisons-directes"]);
      toast.success(`Livraison ${data.reference} créée`);
      setShowCreate(false);
      setFormData({
        ordre_colisage_id: "", livreur_nom: "", livreur_telephone: "", vehicule: "",
        adresse_livraison: { nom: "", adresse: "", zone: "", telephone: "" },
        date_livraison_prevue: "", notes: "",
      });
    },
    onError: (err) => toast.error(err?.response?.data?.detail || "Erreur"),
  });

  const statutMutation = useMutation(
    ({ id, statut, notes }) => updateLivraisonStatut(id, statut, notes),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(["livraisons-directes"]);
        toast.success("Statut mis à jour");
        setShowStatut(null);
      },
      onError: (err) => toast.error(err?.response?.data?.detail || "Erreur"),
    }
  );

  const receptionMutation = useMutation(
    ({ id, data }) => receptionnerLivraison(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(["livraisons-directes"]);
        toast.success("Réception enregistrée");
        setShowReception(null);
      },
      onError: (err) => toast.error(err?.response?.data?.detail || "Erreur"),
    }
  );

  const incidentMutation = useMutation(
    ({ id, data }) => signalerIncidentLivraison(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(["livraisons-directes"]);
        toast.success("Incident signalé");
        setShowIncident(null);
      },
      onError: (err) => toast.error(err?.response?.data?.detail || "Erreur"),
    }
  );

  const livraisons = livraisonsList?.items || livraisonsList || [];

  // Stats rapides
  const stats = {
    en_preparation: livraisons.filter((l) => l.statut === "en_preparation").length,
    en_route: livraisons.filter((l) => l.statut === "en_route").length,
    receptionne: livraisons.filter((l) => l.statut === "receptionne").length,
    incident: livraisons.filter((l) => l.statut === "incident").length,
  };

  const Wrapper = hubMode ? React.Fragment : DashboardLayout;
  return (
    <Wrapper>
      <div className="space-y-6">
        <PageHeader
          title="Livraisons Directes"
          description="Livraisons zone Abidjan — suivi et réception"
          icon={Truck}
          accentColor="#10B981"
          favoriteKey="livraisons_directes"
          actions={
            <Button onClick={() => setShowCreate(true)} className="gap-2">
              <Plus className="w-4 h-4" /> Nouvelle livraison
            </Button>
          }
        />

        {/* Mini KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: "En préparation", val: stats.en_preparation, color: "text-yellow-600", icon: Package },
            { label: "En route", val: stats.en_route, color: "text-indigo-600", icon: Truck },
            { label: "Réceptionnés", val: stats.receptionne, color: "text-green-600", icon: CheckCircle },
            { label: "Incidents", val: stats.incident, color: "text-red-600", icon: AlertTriangle },
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
              placeholder="Rechercher livraison, client, zone..."
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
          <Button variant="outline" size="icon" onClick={() => queryClient.invalidateQueries(["livraisons-directes"])}>
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
            ) : livraisons.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-32 text-gray-400">
                <Truck className="w-8 h-8 mb-2" />
                <p className="text-sm">Aucune livraison</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-white/70">
                      <th className="text-left px-4 py-3 font-medium">Référence</th>
                      <th className="text-left px-4 py-3 font-medium">Destinataire</th>
                      <th className="text-left px-4 py-3 font-medium">Zone</th>
                      <th className="text-left px-4 py-3 font-medium">Livreur</th>
                      <th className="text-left px-4 py-3 font-medium">Date prévue</th>
                      <th className="text-left px-4 py-3 font-medium">Statut</th>
                      <th className="text-right px-4 py-3 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {livraisons.map((liv) => {
                      const transitions = STATUT_TRANSITIONS[liv.statut] || [];
                      return (
                        <tr key={liv._id || liv.livraison_id} className="border-b hover:bg-gray-50 dark:bg-white/5">
                          <td className="px-4 py-3 font-mono text-xs font-medium text-green-700">{liv.reference}</td>
                          <td className="px-4 py-3">
                            <div>{liv.adresse_livraison?.nom || "—"}</div>
                            {liv.adresse_livraison?.telephone && (
                              <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-white/50">
                                <Phone className="w-3 h-3" /> {liv.adresse_livraison.telephone}
                              </div>
                            )}
                          </td>
                          <td className="px-4 py-3 text-xs">
                            <div className="flex items-center gap-1">
                              <MapPin className="w-3 h-3 text-gray-400" />
                              {liv.adresse_livraison?.zone || liv.adresse_livraison?.adresse || "—"}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-sm">{liv.livreur_nom || "—"}</td>
                          <td className="px-4 py-3 text-xs text-gray-500 dark:text-white/50">
                            {liv.date_livraison_prevue
                              ? new Date(liv.date_livraison_prevue).toLocaleDateString("fr-CI")
                              : "—"}
                          </td>
                          <td className="px-4 py-3"><StatutBadge statut={liv.statut} /></td>
                          <td className="px-4 py-3">
                            <div className="flex items-center justify-end gap-1">
                              {transitions.length > 0 && (
                                <Button
                                  size="sm" variant="outline"
                                  className="h-7 px-2 text-xs"
                                  onClick={() => {
                                    setShowStatut(liv);
                                    setNewStatut(transitions[0]);
                                  }}
                                >
                                  Avancer
                                </Button>
                              )}
                              {(liv.statut === "arrive") && (
                                <Button
                                  size="sm" variant="outline"
                                  className="h-7 px-2 text-xs text-green-700 border-green-300"
                                  onClick={() => setShowReception(liv)}
                                >
                                  <CheckCircle className="w-3 h-3 mr-1" /> Réceptionner
                                </Button>
                              )}
                              {(liv.statut === "en_route" || liv.statut === "arrive") && (
                                <Button
                                  size="sm" variant="ghost"
                                  className="h-7 px-2 text-xs text-red-600"
                                  onClick={() => setShowIncident(liv)}
                                >
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

        {/* Dialog créer livraison */}
        <Dialog open={showCreate} onOpenChange={setShowCreate}>
          <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Nouvelle Livraison Directe</DialogTitle>
              <DialogDescription>Zone Abidjan uniquement</DialogDescription>
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
                  <Label>Livreur *</Label>
                  <Input
                    placeholder="Nom du livreur"
                    value={formData.livreur_nom}
                    onChange={(e) => setFormData({ ...formData, livreur_nom: e.target.value })}
                  />
                </div>
                <div>
                  <Label>Tél livreur</Label>
                  <Input
                    placeholder="+225 07 ..."
                    value={formData.livreur_telephone}
                    onChange={(e) => setFormData({ ...formData, livreur_telephone: e.target.value })}
                  />
                </div>
              </div>
              <div>
                <Label>Véhicule</Label>
                <Input
                  placeholder="Immatriculation / description"
                  value={formData.vehicule}
                  onChange={(e) => setFormData({ ...formData, vehicule: e.target.value })}
                />
              </div>
              <hr />
              <p className="text-sm font-medium text-gray-700 dark:text-white/90">Adresse de livraison</p>
              <div>
                <Label>Nom destinataire *</Label>
                <Input
                  value={formData.adresse_livraison.nom}
                  onChange={(e) =>
                    setFormData({ ...formData, adresse_livraison: { ...formData.adresse_livraison, nom: e.target.value } })
                  }
                />
              </div>
              <div>
                <Label>Adresse complète</Label>
                <Input
                  value={formData.adresse_livraison.adresse}
                  onChange={(e) =>
                    setFormData({ ...formData, adresse_livraison: { ...formData.adresse_livraison, adresse: e.target.value } })
                  }
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label>Zone Abidjan</Label>
                  <select
                    className="w-full border rounded-md px-3 py-2 text-sm mt-1"
                    value={formData.adresse_livraison.zone}
                    onChange={(e) =>
                      setFormData({ ...formData, adresse_livraison: { ...formData.adresse_livraison, zone: e.target.value } })
                    }
                  >
                    <option value="">Sélectionner</option>
                    {ZONES_ABIDJAN.map((z) => <option key={z} value={z}>{z}</option>)}
                  </select>
                </div>
                <div>
                  <Label>Tél destinataire</Label>
                  <Input
                    value={formData.adresse_livraison.telephone}
                    onChange={(e) =>
                      setFormData({ ...formData, adresse_livraison: { ...formData.adresse_livraison, telephone: e.target.value } })
                    }
                  />
                </div>
              </div>
              <div>
                <Label>Date livraison prévue</Label>
                <Input
                  type="date"
                  value={formData.date_livraison_prevue}
                  onChange={(e) => setFormData({ ...formData, date_livraison_prevue: e.target.value })}
                />
              </div>
              <div>
                <Label>Notes</Label>
                <Textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows={2}
                />
              </div>
              <div className="flex gap-2 justify-end pt-2">
                <Button variant="outline" onClick={() => setShowCreate(false)}>Annuler</Button>
                <Button
                  onClick={() => createMutation.mutate(formData)}
                  disabled={!formData.ordre_colisage_id || !formData.livreur_nom || !formData.adresse_livraison.nom || createMutation.isLoading}
                >
                  {createMutation.isLoading ? "Création..." : "Créer"}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Dialog transition statut */}
        <Dialog open={!!showStatut} onOpenChange={(open) => !open && setShowStatut(null)}>
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle>Changer statut</DialogTitle>
              <DialogDescription>{showStatut?.reference}</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Nouveau statut</Label>
                <select
                  className="w-full border rounded-md px-3 py-2 text-sm mt-1"
                  value={newStatut}
                  onChange={(e) => setNewStatut(e.target.value)}
                >
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
                    id: showStatut._id || showStatut.livraison_id,
                    statut: newStatut,
                    notes: statutNotes || null,
                  })}
                  disabled={statutMutation.isLoading}
                >
                  Confirmer
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Dialog réception */}
        <Dialog open={!!showReception} onOpenChange={(open) => !open && setShowReception(null)}>
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle>Réceptionner la livraison</DialogTitle>
              <DialogDescription>{showReception?.reference}</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Signature / nom du réceptionnaire</Label>
                <Input
                  value={receptionData.signature_client}
                  onChange={(e) => setReceptionData({ ...receptionData, signature_client: e.target.value })}
                />
              </div>
              <div>
                <Label>Commentaire</Label>
                <Textarea
                  value={receptionData.commentaire}
                  onChange={(e) => setReceptionData({ ...receptionData, commentaire: e.target.value })}
                  rows={2}
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setShowReception(null)}>Annuler</Button>
                <Button
                  className="bg-green-600 hover:bg-green-700"
                  onClick={() => receptionMutation.mutate({
                    id: showReception._id || showReception.livraison_id,
                    data: receptionData,
                  })}
                  disabled={receptionMutation.isLoading}
                >
                  <CheckCircle className="w-4 h-4 mr-1" /> Confirmer réception
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
                <Label>Type d'incident</Label>
                <select
                  className="w-full border rounded-md px-3 py-2 text-sm mt-1"
                  value={incidentData.type_incident}
                  onChange={(e) => setIncidentData({ ...incidentData, type_incident: e.target.value })}
                >
                  <option value="retard">Retard</option>
                  <option value="colis_endommage">Colis endommagé</option>
                  <option value="adresse_incorrecte">Adresse incorrecte</option>
                  <option value="client_absent">Client absent</option>
                  <option value="refus_livraison">Refus de livraison</option>
                  <option value="autre">Autre</option>
                </select>
              </div>
              <div>
                <Label>Description *</Label>
                <Textarea
                  value={incidentData.description}
                  onChange={(e) => setIncidentData({ ...incidentData, description: e.target.value })}
                  rows={3}
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setShowIncident(null)}>Annuler</Button>
                <Button
                  variant="destructive"
                  onClick={() => incidentMutation.mutate({
                    id: showIncident._id || showIncident.livraison_id,
                    data: incidentData,
                  })}
                  disabled={!incidentData.description || incidentMutation.isLoading}
                >
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
