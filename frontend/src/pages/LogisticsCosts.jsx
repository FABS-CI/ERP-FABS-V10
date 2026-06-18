import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { Plus, Search, DollarSign, TrendingUp, TrendingDown, BarChart3, Calendar } from "lucide-react";
import { listCoutsMissions, createCoutMission, listRentabilite, getRapportCouts, getRentabiliteParVehicule } from "@/services/logisticsCostsService";
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

const LogisticsCosts = ({ hubMode = false } = {}) => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("couts"); // couts, rentabilite, rapports, vehicules
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [formData, setFormData] = useState({
    mission_id: "",
    cout_carburant: "",
    cout_chauffeur: "",
    cout_peage: "",
    cout_manutention: "",
    cout_gare: "",
    cout_chargement: "",
    cout_divers: "",
    notes: "",
  });

  const { data: couts, isLoading: loadingCouts } = useQuery(
    ["couts-missions", search],
    () => listCoutsMissions({ q: search }),
    { enabled: !!user && activeTab === "couts" }
  );

  const { data: rentabilite, isLoading: loadingRentabilite } = useQuery(
    ["rentabilite"],
    () => listRentabilite(),
    { enabled: !!user && activeTab === "rentabilite" }
  );

  const { data: rentabiliteVehicules, isLoading: loadingVehicules } = useQuery(
    ["rentabilite-vehicules"],
    () => getRentabiliteParVehicule(),
    { enabled: !!user && activeTab === "vehicules" }
  );

  const createMutation = useMutation(createCoutMission, {
    onSuccess: () => {
      queryClient.invalidateQueries(["couts-missions"]);
      toast.success("Coûts enregistrés avec succès");
      setShowCreate(false);
      setFormData({
        mission_id: "",
        cout_carburant: "",
        cout_chauffeur: "",
        cout_peage: "",
        cout_manutention: "",
        cout_gare: "",
        cout_chargement: "",
        cout_divers: "",
        notes: "",
      });
    },
    onError: () => {
      toast.error("Erreur lors de l'enregistrement");
    },
  });

  const handleCreate = (e) => {
    e.preventDefault();
    createMutation.mutate({
      ...formData,
      cout_carburant: parseFloat(formData.cout_carburant) || 0,
      cout_chauffeur: parseFloat(formData.cout_chauffeur) || 0,
      cout_peage: parseFloat(formData.cout_peage) || 0,
      cout_manutention: parseFloat(formData.cout_manutention) || 0,
      cout_gare: parseFloat(formData.cout_gare) || 0,
      cout_chargement: parseFloat(formData.cout_chargement) || 0,
      cout_divers: parseFloat(formData.cout_divers) || 0,
    });
  };

  if (loadingCouts || loadingRentabilite || loadingVehicules) return hubMode ? <><div>Chargement...</div></> : <DashboardLayout><div>Chargement...</div></DashboardLayout>;

  const Wrapper = hubMode ? React.Fragment : DashboardLayout;
  return (
    <Wrapper>
    <div data-testid="logistics-costs-page">
      <PageHeader
        icon={DollarSign}
        title="Coûts Logistiques"
        description="Gestion des coûts et rentabilité du transport"
        favoriteKey="logistics-costs"
        actions={
          <div className="flex gap-2 flex-wrap">
            <Button
              variant={activeTab === "couts" ? "default" : "outline"}
              onClick={() => setActiveTab("couts")}
              className={activeTab === "couts" ? "bg-[#FF6200] hover:bg-[#E65800]" : ""}
              data-testid="tab-couts"
            >
              <DollarSign className="w-4 h-4 mr-2" />
              Coûts
            </Button>
            <Button
              variant={activeTab === "rentabilite" ? "default" : "outline"}
              onClick={() => setActiveTab("rentabilite")}
              className={activeTab === "rentabilite" ? "bg-[#FF6200] hover:bg-[#E65800]" : ""}
              data-testid="tab-rentabilite"
            >
              <TrendingUp className="w-4 h-4 mr-2" />
              Rentabilité
            </Button>
            <Button
              variant={activeTab === "vehicules" ? "default" : "outline"}
              onClick={() => setActiveTab("vehicules")}
              className={activeTab === "vehicules" ? "bg-[#FF6200] hover:bg-[#E65800]" : ""}
              data-testid="tab-vehicules"
            >
              <BarChart3 className="w-4 h-4 mr-2" />
              Par Véhicule
            </Button>
            <Button
              variant={activeTab === "rapports" ? "default" : "outline"}
              onClick={() => setActiveTab("rapports")}
              className={activeTab === "rapports" ? "bg-[#FF6200] hover:bg-[#E65800]" : ""}
              data-testid="tab-rapports"
            >
              <Calendar className="w-4 h-4 mr-2" />
              Rapports
            </Button>
          </div>
        }
      />

      {activeTab === "couts" && (
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div className="flex gap-4 flex-1">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input
                    placeholder="Rechercher des coûts..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              <Dialog open={showCreate} onOpenChange={setShowCreate}>
                <DialogTrigger asChild>
                  <Button className="bg-[#FF6200] hover:bg-[#E65800]" data-testid="btn-new-cout">
                    <Plus className="w-4 h-4 mr-2" />
                    Nouveaux Coûts
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl">
                  <DialogHeader>
                    <DialogTitle>Enregistrer les Coûts d'une Mission</DialogTitle>
                    <DialogDescription>
                      Saisissez les différents coûts de la mission
                    </DialogDescription>
                  </DialogHeader>
                  <form onSubmit={handleCreate} className="space-y-4">
                    <div>
                      <Label>ID Mission</Label>
                      <Input
                        value={formData.mission_id}
                        onChange={(e) => setFormData({ ...formData, mission_id: e.target.value })}
                        required
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Carburant (FCFA)</Label>
                        <Input
                          type="number"
                          value={formData.cout_carburant}
                          onChange={(e) => setFormData({ ...formData, cout_carburant: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label>Chauffeur (FCFA)</Label>
                        <Input
                          type="number"
                          value={formData.cout_chauffeur}
                          onChange={(e) => setFormData({ ...formData, cout_chauffeur: e.target.value })}
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Péage (FCFA)</Label>
                        <Input
                          type="number"
                          value={formData.cout_peage}
                          onChange={(e) => setFormData({ ...formData, cout_peage: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label>Manutention (FCFA)</Label>
                        <Input
                          type="number"
                          value={formData.cout_manutention}
                          onChange={(e) => setFormData({ ...formData, cout_manutention: e.target.value })}
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Gare (FCFA)</Label>
                        <Input
                          type="number"
                          value={formData.cout_gare}
                          onChange={(e) => setFormData({ ...formData, cout_gare: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label>Chargement (FCFA)</Label>
                        <Input
                          type="number"
                          value={formData.cout_chargement}
                          onChange={(e) => setFormData({ ...formData, cout_chargement: e.target.value })}
                        />
                      </div>
                    </div>
                    <div>
                      <Label>Divers (FCFA)</Label>
                      <Input
                        type="number"
                        value={formData.cout_divers}
                        onChange={(e) => setFormData({ ...formData, cout_divers: e.target.value })}
                      />
                    </div>
                    <div>
                      <Label>Notes</Label>
                      <Input
                        value={formData.notes}
                        onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                      />
                    </div>
                    <Button type="submit" className="w-full bg-[#FF6200] hover:bg-[#E65800]" data-testid="btn-submit-cout">
                      Enregistrer les Coûts
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
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Mission</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Carburant</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Chauffeur</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Péage</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Manutention</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Gare</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {couts?.map((cout) => (
                    <tr key={cout.cout_id} className="border-b hover:bg-gray-50 dark:hover:bg-[#040f1a]/50">
                      <td className="py-3 px-4 font-medium">{cout.mission_id}</td>
                      <td className="py-3 px-4">{cout.cout_carburant} FCFA</td>
                      <td className="py-3 px-4">{cout.cout_chauffeur} FCFA</td>
                      <td className="py-3 px-4">{cout.cout_peage} FCFA</td>
                      <td className="py-3 px-4">{cout.cout_manutention} FCFA</td>
                      <td className="py-3 px-4">{cout.cout_gare} FCFA</td>
                      <td className="py-3 px-4 font-bold">{cout.cout_total} FCFA</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {couts?.length === 0 && (
                <div className="text-center py-8 text-gray-500 dark:text-white/50">
                  Aucun coût enregistré
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === "rentabilite" && (
        <Card>
          <CardHeader>
            <CardTitle>Rentabilité des Missions</CardTitle>
            <CardDescription>Analyse de la rentabilité par mission</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Mission</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Distance</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Revenu</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Coût Total</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Marge</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Taux</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Coût/Km</th>
                  </tr>
                </thead>
                <tbody>
                  {rentabilite?.map((rent) => (
                    <tr key={rent.mission_id} className="border-b hover:bg-gray-50 dark:hover:bg-[#040f1a]/50">
                      <td className="py-3 px-4 font-medium">{rent.mission_id}</td>
                      <td className="py-3 px-4">{rent.distance_km} km</td>
                      <td className="py-3 px-4">{rent.revenu} FCFA</td>
                      <td className="py-3 px-4">{rent.cout_total} FCFA</td>
                      <td className={`py-3 px-4 font-bold ${rent.marge >= 0 ? "text-green-600" : "text-red-600"}`}>
                        {rent.marge} FCFA
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant={rent.taux_rentabilite >= 0 ? "success" : "destructive"}>
                          {rent.taux_rentabilite.toFixed(2)}%
                        </Badge>
                      </td>
                      <td className="py-3 px-4">{rent.cout_par_km.toFixed(2)} FCFA/km</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {rentabilite?.length === 0 && (
                <div className="text-center py-8 text-gray-500 dark:text-white/50">
                  Aucune donnée de rentabilité disponible
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === "vehicules" && (
        <Card>
          <CardHeader>
            <CardTitle>Rentabilité par Véhicule</CardTitle>
            <CardDescription>Analyse de la rentabilité par véhicule</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Véhicule</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Immatriculation</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Missions</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Revenu</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Coût</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Marge</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Taux</th>
                  </tr>
                </thead>
                <tbody>
                  {rentabiliteVehicules?.map((veh) => (
                    <tr key={veh.vehicule_id} className="border-b hover:bg-gray-50 dark:hover:bg-[#040f1a]/50">
                      <td className="py-3 px-4 font-medium">{veh.reference}</td>
                      <td className="py-3 px-4 font-mono">{veh.immatriculation}</td>
                      <td className="py-3 px-4">{veh.nombre_missions}</td>
                      <td className="py-3 px-4">{veh.total_revenu} FCFA</td>
                      <td className="py-3 px-4">{veh.total_cout} FCFA</td>
                      <td className={`py-3 px-4 font-bold ${veh.marge >= 0 ? "text-green-600" : "text-red-600"}`}>
                        {veh.marge} FCFA
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant={veh.taux_rentabilite >= 0 ? "success" : "destructive"}>
                          {veh.taux_rentabilite.toFixed(2)}%
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {rentabiliteVehicules?.length === 0 && (
                <div className="text-center py-8 text-gray-500 dark:text-white/50">
                  Aucune donnée de rentabilité par véhicule disponible
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === "rapports" && (
        <Card>
          <CardHeader>
            <CardTitle>Rapports de Coûts</CardTitle>
            <CardDescription>Générer des rapports sur une période</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 text-gray-500 dark:text-white/50">
              <Calendar className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>Sélectionnez une période pour générer un rapport</p>
              <div className="flex gap-4 justify-center mt-4">
                <Input type="date" className="w-48" />
                <Input type="date" className="w-48" />
                <Button className="bg-[#FF6200] hover:bg-[#E65800]">Générer</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
    </Wrapper>
  );
};

export default LogisticsCosts;
