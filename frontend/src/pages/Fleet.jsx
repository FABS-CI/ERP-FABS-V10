import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { Plus, Search, Car, Shield, Wrench, UserCheck, AlertTriangle, CheckCircle, XCircle } from "lucide-react";
import { listVehicules, createVehicule, updateVehiculeStatut, checkVehiculeEligibilite } from "@/services/fleetService";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/layout/PageHeader";

const Fleet = ({ hubMode = false } = {}) => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("vehicules"); // vehicules, assurances, visites, maintenances, affectations
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [formData, setFormData] = useState({
    reference: "",
    marque: "",
    modele: "",
    annee: "",
    immatriculation: "",
    type: "fourgonnette",
    capacite_kg: "",
    capacite_m3: "",
    kilometrage: "",
    statut: "disponible",
    chauffeur_id: "",
  });

  const { data: vehiculesRaw, isLoading } = useQuery(
    ["vehicules", search],
    () => listVehicules({ q: search }),
    { enabled: !!user && activeTab === "vehicules" }
  );
  // Déduplication par vehicule_id pour éviter les doublons d'affichage
  const vehicules = vehiculesRaw
    ? [...new Map(vehiculesRaw.map((v) => [v.vehicule_id, v])).values()]
    : vehiculesRaw;

  const createMutation = useMutation(createVehicule, {
    onSuccess: () => {
      queryClient.invalidateQueries(["vehicules"]);
      toast.success("Véhicule créé avec succès");
      setShowCreate(false);
      setFormData({
        reference: "",
        marque: "",
        modele: "",
        annee: "",
        immatriculation: "",
        type: "fourgonnette",
        capacite_kg: "",
        capacite_m3: "",
        kilometrage: "",
        statut: "disponible",
        chauffeur_id: "",
      });
    },
    onError: () => {
      toast.error("Erreur lors de la création");
    },
  });

  const updateStatutMutation = useMutation(
    ({ vehiculeId, statut }) => updateVehiculeStatut(vehiculeId, statut),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(["vehicules"]);
        toast.success("Statut mis à jour");
      },
      onError: () => {
        toast.error("Erreur lors de la mise à jour du statut");
      },
    }
  );

  const checkEligibiliteMutation = useMutation(checkVehiculeEligibilite, {
    onSuccess: (data) => {
      if (data.eligible) {
        toast.success("Véhicule éligible pour sortie");
      } else {
        toast.error(`Non éligible: ${data.raison}`);
      }
    },
  });

  const handleCreate = (e) => {
    e.preventDefault();
    createMutation.mutate({
      ...formData,
      annee: parseInt(formData.annee),
      capacite_kg: parseFloat(formData.capacite_kg),
      capacite_m3: parseFloat(formData.capacite_m3),
      kilometrage: parseFloat(formData.kilometrage),
    });
  };

  const handleStatutChange = (vehiculeId, newStatut) => {
    updateStatutMutation.mutate({ vehiculeId, statut: newStatut });
  };

  const handleCheckEligibilite = (vehiculeId) => {
    checkEligibiliteMutation.mutate(vehiculeId);
  };

  const getStatutBadge = (statut) => {
    const variants = {
      disponible: "success",
      en_mission: "default",
      maintenance: "secondary",
      hors_service: "destructive",
    };
    const labels = {
      disponible: "Disponible",
      en_mission: "En mission",
      maintenance: "Maintenance",
      hors_service: "Hors service",
    };
    return (
      <Badge variant={variants[statut] || "secondary"}>
        {labels[statut] || statut}
      </Badge>
    );
  };

  const getTypeBadge = (type) => {
    const labels = {
      camion: "Camion",
      fourgonnette: "Fourgonnette",
      voiture: "Voiture",
      moto: "Moto",
    };
    return labels[type] || type;
  };

  if (isLoading) return hubMode ? <><div>Chargement...</div></> : <DashboardLayout><div>Chargement...</div></DashboardLayout>;

  const Wrapper = hubMode ? React.Fragment : DashboardLayout;
  return (
    <Wrapper>
    <div data-testid="fleet-page">
      <PageHeader
        icon={Car}
        title="Gestion de Flotte"
        description="Véhicules, assurances, visites techniques et maintenance"
        favoriteKey="flotte"
        actions={
          <div className="flex gap-2 flex-wrap">
            <Button
              variant={activeTab === "vehicules" ? "default" : "outline"}
              onClick={() => setActiveTab("vehicules")}
              className={activeTab === "vehicules" ? "bg-[#FF6200] hover:bg-[#E65800]" : ""}
              data-testid="tab-vehicules"
            >
              <Car className="w-4 h-4 mr-2" />
              Véhicules
            </Button>
            <Button
              variant={activeTab === "assurances" ? "default" : "outline"}
              onClick={() => setActiveTab("assurances")}
              className={activeTab === "assurances" ? "bg-[#FF6200] hover:bg-[#E65800]" : ""}
              data-testid="tab-assurances"
            >
              <Shield className="w-4 h-4 mr-2" />
              Assurances
            </Button>
            <Button
              variant={activeTab === "visites" ? "default" : "outline"}
              onClick={() => setActiveTab("visites")}
              className={activeTab === "visites" ? "bg-[#FF6200] hover:bg-[#E65800]" : ""}
              data-testid="tab-visites"
            >
              <CheckCircle className="w-4 h-4 mr-2" />
              Visites
            </Button>
            <Button
              variant={activeTab === "maintenances" ? "default" : "outline"}
              onClick={() => setActiveTab("maintenances")}
              className={activeTab === "maintenances" ? "bg-[#FF6200] hover:bg-[#E65800]" : ""}
              data-testid="tab-maintenances"
            >
              <Wrench className="w-4 h-4 mr-2" />
              Maintenances
            </Button>
            <Button
              variant={activeTab === "affectations" ? "default" : "outline"}
              onClick={() => setActiveTab("affectations")}
              className={activeTab === "affectations" ? "bg-[#FF6200] hover:bg-[#E65800]" : ""}
              data-testid="tab-affectations"
            >
              <UserCheck className="w-4 h-4 mr-2" />
              Affectations
            </Button>
          </div>
        }
      />

      {activeTab === "vehicules" && (
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div className="flex gap-4 flex-1">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input
                    placeholder="Rechercher un véhicule..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              <Dialog open={showCreate} onOpenChange={setShowCreate}>
                <DialogTrigger asChild>
                  <Button className="bg-[#FF6200] hover:bg-[#E65800]" data-testid="btn-new-vehicule">
                    <Plus className="w-4 h-4 mr-2" />
                    Nouveau Véhicule
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl">
                  <DialogHeader>
                    <DialogTitle>Créer un Véhicule</DialogTitle>
                    <DialogDescription>
                      Enregistrer un nouveau véhicule dans la flotte
                    </DialogDescription>
                  </DialogHeader>
                  <form onSubmit={handleCreate} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Référence *</Label>
                        <Input
                          value={formData.reference}
                          onChange={(e) => setFormData({ ...formData, reference: e.target.value })}
                          required
                        />
                      </div>
                      <div>
                        <Label>Immatriculation *</Label>
                        <Input
                          value={formData.immatriculation}
                          onChange={(e) => setFormData({ ...formData, immatriculation: e.target.value })}
                          required
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Marque *</Label>
                        <Input
                          value={formData.marque}
                          onChange={(e) => setFormData({ ...formData, marque: e.target.value })}
                          required
                        />
                      </div>
                      <div>
                        <Label>Modèle *</Label>
                        <Input
                          value={formData.modele}
                          onChange={(e) => setFormData({ ...formData, modele: e.target.value })}
                          required
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <Label>Année *</Label>
                        <Input
                          type="number"
                          value={formData.annee}
                          onChange={(e) => setFormData({ ...formData, annee: e.target.value })}
                          required
                        />
                      </div>
                      <div>
                        <Label>Type *</Label>
                        <select
                          value={formData.type}
                          onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                          className="w-full px-3 py-2 border rounded-md"
                          required
                        >
                          <option value="camion">Camion</option>
                          <option value="fourgonnette">Fourgonnette</option>
                          <option value="voiture">Voiture</option>
                          <option value="moto">Moto</option>
                        </select>
                      </div>
                      <div>
                        <Label>Statut *</Label>
                        <select
                          value={formData.statut}
                          onChange={(e) => setFormData({ ...formData, statut: e.target.value })}
                          className="w-full px-3 py-2 border rounded-md"
                          required
                        >
                          <option value="disponible">Disponible</option>
                          <option value="en_mission">En mission</option>
                          <option value="maintenance">Maintenance</option>
                          <option value="hors_service">Hors service</option>
                        </select>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <Label>Capacité (kg) *</Label>
                        <Input
                          type="number"
                          value={formData.capacite_kg}
                          onChange={(e) => setFormData({ ...formData, capacite_kg: e.target.value })}
                          required
                        />
                      </div>
                      <div>
                        <Label>Capacité (m³)</Label>
                        <Input
                          type="number"
                          value={formData.capacite_m3}
                          onChange={(e) => setFormData({ ...formData, capacite_m3: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label>Kilométrage *</Label>
                        <Input
                          type="number"
                          value={formData.kilometrage}
                          onChange={(e) => setFormData({ ...formData, kilometrage: e.target.value })}
                          required
                        />
                      </div>
                    </div>
                    <div>
                      <Label>Chauffeur ID</Label>
                      <Input
                        value={formData.chauffeur_id}
                        onChange={(e) => setFormData({ ...formData, chauffeur_id: e.target.value })}
                      />
                    </div>
                    <Button type="submit" className="w-full bg-[#FF6200] hover:bg-[#E65800]" data-testid="btn-submit-vehicule">
                      Créer le Véhicule
                    </Button>
                  </form>
                </DialogContent>
              </Dialog>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Référence</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Véhicule</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Immatriculation</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Type</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Capacité</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Km</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Statut</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {vehicules?.map((vehicule) => (
                    <tr key={vehicule.vehicule_id} className="border-b hover:bg-gray-50 dark:hover:bg-[#040f1a]/50">
                      <td className="py-3 px-4 font-medium">{vehicule.reference}</td>
                      <td className="py-3 px-4">{vehicule.marque} {vehicule.modele} ({vehicule.annee})</td>
                      <td className="py-3 px-4 font-mono">{vehicule.immatriculation}</td>
                      <td className="py-3 px-4">{getTypeBadge(vehicule.type)}</td>
                      <td className="py-3 px-4">{vehicule.capacite_kg} kg / {vehicule.capacite_m3} m³</td>
                      <td className="py-3 px-4">{vehicule.kilometrage} km</td>
                      <td className="py-3 px-4">{getStatutBadge(vehicule.statut)}</td>
                      <td className="py-3 px-4">
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleCheckEligibilite(vehicule.vehicule_id)}
                          >
                            <CheckCircle className="w-4 h-4" />
                          </Button>
                          {vehicule.statut === "disponible" && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleStatutChange(vehicule.vehicule_id, "en_mission")}
                            >
                              <UserCheck className="w-4 h-4" />
                            </Button>
                          )}
                          {vehicule.statut === "en_mission" && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleStatutChange(vehicule.vehicule_id, "disponible")}
                            >
                              <XCircle className="w-4 h-4" />
                            </Button>
                          )}
                          {vehicule.statut !== "maintenance" && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleStatutChange(vehicule.vehicule_id, "maintenance")}
                            >
                              <Wrench className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {vehicules?.length === 0 && (
                <div className="text-center py-8 text-gray-500 dark:text-white/50">
                  Aucun véhicule trouvé
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab !== "vehicules" && (
        <Card>
          <CardHeader>
            <CardTitle>{activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}</CardTitle>
            <CardDescription>
              Module en cours de développement
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 text-gray-500 dark:text-white/50">
              <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-yellow-500" />
              <p>Cette fonctionnalité sera disponible dans le prochain sprint</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
    </Wrapper>
  );
};

export default Fleet;
