import { useEffect, useState } from "react";
import { Plus, MapPin, Check, X, Briefcase } from "lucide-react";
import { listMissions, createMission, cloturerMission } from "../services/rhApi";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Label } from "../components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/layout/PageHeader";

export default function Missions() {
  const [missions, setMissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isClotureDialogOpen, setIsClotureDialogOpen] = useState(false);
  const [selectedMission, setSelectedMission] = useState(null);
  const [formData, setFormData] = useState({
    employe_id: "",
    type_mission: "mission_commerciale",
    ville: "",
    date_depart: "",
    date_retour: "",
    objet: "",
    budget: "",
  });
  const [clotureData, setClotureData] = useState({ compte_rendu: "" });

  useEffect(() => {
    loadMissions();
  }, []);

  const loadMissions = async () => {
    try {
      setLoading(true);
      const data = await listMissions({ actif: true });
      setMissions(data);
    } catch (error) {
      console.error("Error loading missions:", error);
      toast.error("Erreur lors du chargement des missions");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        budget: formData.budget ? parseFloat(formData.budget) : undefined,
      };
      await createMission(payload);
      toast.success("Mission créée avec succès");
      setIsDialogOpen(false);
      setFormData({
        employe_id: "",
        type_mission: "mission_commerciale",
        ville: "",
        date_depart: "",
        date_retour: "",
        objet: "",
        budget: "",
      });
      loadMissions();
    } catch (error) {
      console.error("Error saving mission:", error);
      toast.error("Erreur lors de la création de la mission");
    }
  };

  const handleCloture = async () => {
    try {
      await cloturerMission(selectedMission.mission_id, clotureData);
      toast.success("Mission clôturée avec succès");
      setIsClotureDialogOpen(false);
      setSelectedMission(null);
      setClotureData({ compte_rendu: "" });
      loadMissions();
    } catch (error) {
      console.error("Error closing mission:", error);
      toast.error("Erreur lors de la clôture de la mission");
    }
  };

  const getStatutBadge = (statut) => {
    const badges = {
      planifiee: "bg-blue-100 text-blue-800",
      en_cours: "bg-orange-100 text-orange-800",
      terminee: "bg-green-100 text-green-800",
      annulee: "bg-red-100 text-red-800",
    };
    return badges[statut] || "bg-gray-100 dark:bg-white/10 text-gray-800 dark:text-white";
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-sm text-gray-500 dark:text-white/50">Chargement...</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
    <div data-testid="missions-page" className="space-y-6">
      <PageHeader
        icon={Briefcase}
        title="Missions"
        description="Gestion des missions professionnelles"
        favoriteKey="missions"
        actions={
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button
                className="bg-[#FF6200] hover:bg-[#E65800]"
                data-testid="btn-new-mission"
                onClick={() => { setFormData({ employe_id: "", type_mission: "mission_commerciale", ville: "", date_depart: "", date_retour: "", objet: "", budget: "" }); }}
              >
                <Plus className="w-4 h-4 mr-2" />
                Nouvelle Mission
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Nouvelle Mission</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="mis-employe">Employé ID *</Label>
                    <Input
                      id="mis-employe"
                      value={formData.employe_id}
                      onChange={(e) => setFormData({ ...formData, employe_id: e.target.value })}
                      required
                      data-testid="input-employe-id"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="mis-type">Type de Mission *</Label>
                    <Select value={formData.type_mission} onValueChange={(v) => setFormData({ ...formData, type_mission: v })}>
                      <SelectTrigger id="mis-type"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="mission_commerciale">Mission Commerciale</SelectItem>
                        <SelectItem value="mission_logistique">Mission Logistique</SelectItem>
                        <SelectItem value="mission_administrative">Mission Administrative</SelectItem>
                        <SelectItem value="mission_inventaire">Mission Inventaire</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="mis-ville">Ville *</Label>
                  <Input
                    id="mis-ville"
                    value={formData.ville}
                    onChange={(e) => setFormData({ ...formData, ville: e.target.value })}
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="mis-dep">Date de Départ *</Label>
                    <Input
                      id="mis-dep"
                      type="date"
                      value={formData.date_depart}
                      onChange={(e) => setFormData({ ...formData, date_depart: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="mis-ret">Date de Retour *</Label>
                    <Input
                      id="mis-ret"
                      type="date"
                      value={formData.date_retour}
                      onChange={(e) => setFormData({ ...formData, date_retour: e.target.value })}
                      required
                    />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="mis-objet">Objet *</Label>
                  <Textarea
                    id="mis-objet"
                    value={formData.objet}
                    onChange={(e) => setFormData({ ...formData, objet: e.target.value })}
                    rows={3}
                    required
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="mis-budget">Budget (FCFA, optionnel)</Label>
                  <Input
                    id="mis-budget"
                    type="number"
                    value={formData.budget}
                    onChange={(e) => setFormData({ ...formData, budget: e.target.value })}
                  />
                </div>
                <div className="flex gap-2 justify-end">
                  <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                    Annuler
                  </Button>
                  <Button type="submit" className="bg-[#FF6200] hover:bg-[#E65800]" data-testid="btn-submit-mission">Créer</Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        }
      />

      <div className="bg-white dark:bg-[#0b1e30] rounded-lg shadow-sm overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Référence</TableHead>
              <TableHead>Employé</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Ville</TableHead>
              <TableHead>Date Départ</TableHead>
              <TableHead>Date Retour</TableHead>
              <TableHead>Objet</TableHead>
              <TableHead>Statut</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {missions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} className="text-center py-8 text-gray-500 dark:text-white/50">
                  Aucune mission trouvée
                </TableCell>
              </TableRow>
            ) : (
              missions.map((mission) => (
                <TableRow key={mission.mission_id}>
                  <TableCell className="font-medium">{mission.reference}</TableCell>
                  <TableCell>{mission.employe_nom || "-"}</TableCell>
                  <TableCell>{mission.type_mission}</TableCell>
                  <TableCell className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-gray-400" />
                    {mission.ville}
                  </TableCell>
                  <TableCell>{mission.date_depart}</TableCell>
                  <TableCell>{mission.date_retour}</TableCell>
                  <TableCell className="max-w-xs truncate">{mission.objet}</TableCell>
                  <TableCell>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatutBadge(mission.statut)}`}>
                      {mission.statut}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      {mission.statut === "en_cours" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => { setSelectedMission(mission); setIsClotureDialogOpen(true); }}
                          title="Clôturer la mission"
                        >
                          <Check className="w-4 h-4 text-green-500" />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      <Dialog open={isClotureDialogOpen} onOpenChange={setIsClotureDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Clôturer la Mission</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Compte Rendu</label>
              <Textarea
                value={clotureData.compte_rendu}
                onChange={(e) => setClotureData({ compte_rendu: e.target.value })}
                rows={4}
                placeholder="Décrivez le résultat de la mission..."
              />
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setIsClotureDialogOpen(false)}>
                Annuler
              </Button>
              <Button onClick={handleCloture}>Clôturer</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
    </DashboardLayout>
  );
}
