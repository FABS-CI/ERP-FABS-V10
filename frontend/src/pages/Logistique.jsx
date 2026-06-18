import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { Plus, Search, MapPin, Truck, Calendar, DollarSign, CheckCircle, PlayCircle, StopCircle } from "lucide-react";
import { listMissions, createMission, updateMissionStatut } from "@/services/logistiqueService";
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

const Logistique = ({ hubMode = false } = {}) => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [statutFilter, setStatutFilter] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [formData, setFormData] = useState({
    expedition_ids: [],
    chauffeur_id: "",
    vehicule_id: "",
    date_mission: "",
    notes: "",
  });

  const { data: missions, isLoading } = useQuery(
    ["missions", search, statutFilter],
    () => listMissions({ q: search, statut: statutFilter }),
    { enabled: !!user }
  );

  const createMutation = useMutation(createMission, {
    onSuccess: () => {
      queryClient.invalidateQueries(["missions"]);
      toast.success("Mission créée avec succès");
      setShowCreate(false);
      setFormData({
        expedition_ids: [],
        chauffeur_id: "",
        vehicule_id: "",
        date_mission: "",
        notes: "",
      });
    },
    onError: () => {
      toast.error("Erreur lors de la création");
    },
  });

  const updateStatutMutation = useMutation(
    ({ missionId, statut }) => updateMissionStatut(missionId, statut),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(["missions"]);
        toast.success("Statut mis à jour");
      },
      onError: () => {
        toast.error("Erreur lors de la mise à jour du statut");
      },
    }
  );

  const handleCreate = (e) => {
    e.preventDefault();
    createMutation.mutate(formData);
  };

  const handleStatutChange = (missionId, newStatut) => {
    updateStatutMutation.mutate({ missionId, statut: newStatut });
  };

  const getStatutBadge = (statut) => {
    const variants = {
      planifie: "secondary",
      en_cours: "default",
      termine: "success",
      annule: "destructive",
    };
    const labels = {
      planifie: "Planifié",
      en_cours: "En cours",
      termine: "Terminé",
      annule: "Annulé",
    };
    return (
      <Badge variant={variants[statut] || "secondary"}>
        {labels[statut] || statut}
      </Badge>
    );
  };

  if (isLoading) return hubMode ? <><div>Chargement...</div></> : <DashboardLayout><div>Chargement...</div></DashboardLayout>;

  const Wrapper = hubMode ? React.Fragment : DashboardLayout;
  return (
    <Wrapper>
    <div data-testid="missions-logistiques-page">
      <PageHeader
        icon={Truck}
        title="Missions Logistiques"
        description="Gestion des missions de livraison"
        favoriteKey="missions-logistiques"
        actions={
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
          <DialogTrigger asChild>
            <Button className="bg-[#FF6200] hover:bg-[#E65800]" data-testid="btn-new-mission-log">
              <Plus className="w-4 h-4 mr-2" />
              Nouvelle Mission
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Créer une Mission Logistique</DialogTitle>
              <DialogDescription>
                Sélectionnez les expéditions et assignez un chauffeur/véhicule
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="ml-exp">Expéditions IDs (séparés par virgule) *</Label>
                <Input
                  id="ml-exp"
                  value={formData.expedition_ids.join(", ")}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      expedition_ids: e.target.value.split(",").map((s) => s.trim()),
                    })
                  }
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="ml-chf">Chauffeur ID</Label>
                  <Input
                    id="ml-chf"
                    value={formData.chauffeur_id}
                    onChange={(e) => setFormData({ ...formData, chauffeur_id: e.target.value })}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="ml-veh">Véhicule ID</Label>
                  <Input
                    id="ml-veh"
                    value={formData.vehicule_id}
                    onChange={(e) => setFormData({ ...formData, vehicule_id: e.target.value })}
                  />
                </div>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="ml-date">Date de mission *</Label>
                <Input
                  id="ml-date"
                  type="date"
                  value={formData.date_mission}
                  onChange={(e) => setFormData({ ...formData, date_mission: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="ml-notes">Notes</Label>
                <Input
                  id="ml-notes"
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setShowCreate(false)}>Annuler</Button>
                <Button type="submit" className="bg-[#FF6200] hover:bg-[#E65800]" data-testid="btn-submit-mission-log">
                  Créer la Mission
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Rechercher une mission..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            <select
              value={statutFilter}
              onChange={(e) => setStatutFilter(e.target.value)}
              className="px-4 py-2 border rounded-md bg-white dark:bg-[#040f1a] dark:border-gray-700"
            >
              <option value="">Tous les statuts</option>
              <option value="planifie">Planifié</option>
              <option value="en_cours">En cours</option>
              <option value="termine">Terminé</option>
              <option value="annule">Annulé</option>
            </select>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Référence</th>
                  <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Expéditions</th>
                  <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Date</th>
                  <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Distance</th>
                  <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Coût</th>
                  <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Statut</th>
                  <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Actions</th>
                </tr>
              </thead>
              <tbody>
                {missions?.map((mission) => (
                  <tr key={mission.mission_id} className="border-b hover:bg-gray-50 dark:hover:bg-[#040f1a]/50">
                    <td className="py-3 px-4 font-medium">{mission.reference}</td>
                    <td className="py-3 px-4">{mission.expedition_ids.length} expéditions</td>
                    <td className="py-3 px-4">{mission.date_mission}</td>
                    <td className="py-3 px-4">{mission.distance_totale_km} km</td>
                    <td className="py-3 px-4">{mission.cout_transport} FCFA</td>
                    <td className="py-3 px-4">{getStatutBadge(mission.statut)}</td>
                    <td className="py-3 px-4">
                      <div className="flex gap-2">
                        {mission.statut === "planifie" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleStatutChange(mission.mission_id, "en_cours")}
                          >
                            <PlayCircle className="w-4 h-4" />
                          </Button>
                        )}
                        {mission.statut === "en_cours" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleStatutChange(mission.mission_id, "termine")}
                          >
                            <CheckCircle className="w-4 h-4" />
                          </Button>
                        )}
                        {mission.statut !== "annule" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleStatutChange(mission.mission_id, "annule")}
                          >
                            <StopCircle className="w-4 h-4 text-red-500" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {missions?.length === 0 && (
              <div className="text-center py-8 text-gray-500 dark:text-white/50">
                Aucune mission trouvée
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
    </Wrapper>
  );
};

export default Logistique;
