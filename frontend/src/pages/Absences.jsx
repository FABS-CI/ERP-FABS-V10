import { useEffect, useState } from "react";
import { Plus, Clock, X } from "lucide-react";
import { listAbsences, createAbsence } from "../services/rhApi";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
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

export default function Absences() {
  const [absences, setAbsences] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    employe_id: "",
    type_absence: "absence_justifiee",
    date: "",
    heure_debut: "",
    heure_fin: "",
    duree_minutes: "",
    motif: "",
    justifie: false,
  });

  useEffect(() => {
    loadAbsences();
  }, []);

  const loadAbsences = async () => {
    try {
      setLoading(true);
      const data = await listAbsences({ actif: true });
      setAbsences(data);
    } catch (error) {
      console.error("Error loading absences:", error);
      toast.error("Erreur lors du chargement des absences");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        duree_minutes: parseInt(formData.duree_minutes) || 0,
        justifie: formData.justifie,
      };
      await createAbsence(payload);
      toast.success("Absence enregistrée avec succès");
      setIsDialogOpen(false);
      setFormData({
        employe_id: "",
        type_absence: "absence_justifiee",
        date: "",
        heure_debut: "",
        heure_fin: "",
        duree_minutes: "",
        motif: "",
        justifie: false,
      });
      loadAbsences();
    } catch (error) {
      console.error("Error saving absence:", error);
      toast.error("Erreur lors de l'enregistrement de l'absence");
    }
  };

  const getTypeBadge = (type) => {
    const badges = {
      retard: "bg-yellow-100 text-yellow-800",
      absence_justifiee: "bg-blue-100 text-blue-800",
      absence_non_justifiee: "bg-red-100 text-red-800",
      sortie_autorisee: "bg-purple-100 text-purple-800",
    };
    return badges[type] || "bg-gray-100 dark:bg-white/10 text-gray-800 dark:text-white";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-sm text-gray-500 dark:text-white/50">Chargement...</div>
      </div>
    );
  }

  return (
    <DashboardLayout>
    <div className="space-y-6" data-testid="absences-page">
      <PageHeader
        icon={Clock}
        title="Absences"
        description="Gestion des absences et retards"
        favoriteKey="absences"
        actions={
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-[#FF6200] hover:bg-[#E65800]" data-testid="btn-new-absence" onClick={() => { setFormData({ employe_id: "", type_absence: "absence_justifiee", date: "", heure_debut: "", heure_fin: "", duree_minutes: "", motif: "", justifie: false }); }}>
              <Plus className="w-4 h-4 mr-2" />
              Enregistrer Absence
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Enregistrer une Absence</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-sm font-medium">Employé ID</label>
                <Input
                  value={formData.employe_id}
                  onChange={(e) => setFormData({ ...formData, employe_id: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-sm font-medium">Type d'Absence</label>
                <Select value={formData.type_absence} onValueChange={(v) => setFormData({ ...formData, type_absence: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="retard">Retard</SelectItem>
                    <SelectItem value="absence_justifiee">Absence Justifiée</SelectItem>
                    <SelectItem value="absence_non_justifiee">Absence Non Justifiée</SelectItem>
                    <SelectItem value="sortie_autorisee">Sortie Autorisée</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Date</label>
                <Input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Heure Début</label>
                  <Input
                    type="time"
                    value={formData.heure_debut}
                    onChange={(e) => setFormData({ ...formData, heure_debut: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Heure Fin</label>
                  <Input
                    type="time"
                    value={formData.heure_fin}
                    onChange={(e) => setFormData({ ...formData, heure_fin: e.target.value })}
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium">Durée (minutes)</label>
                <Input
                  type="number"
                  value={formData.duree_minutes}
                  onChange={(e) => setFormData({ ...formData, duree_minutes: e.target.value })}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Motif</label>
                <Textarea
                  value={formData.motif}
                  onChange={(e) => setFormData({ ...formData, motif: e.target.value })}
                  rows={2}
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="justifie"
                  checked={formData.justifie}
                  onChange={(e) => setFormData({ ...formData, justifie: e.target.checked })}
                />
                <label htmlFor="justifie" className="text-sm">Justifiée</label>
              </div>
              <div className="flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                  Annuler
                </Button>
                <Button type="submit" className="bg-[#FF6200] hover:bg-[#E65800]" data-testid="btn-submit-absence">Enregistrer</Button>
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
              <TableHead>Employé</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Date</TableHead>
              <TableHead>Heure Début</TableHead>
              <TableHead>Heure Fin</TableHead>
              <TableHead>Durée (min)</TableHead>
              <TableHead>Motif</TableHead>
              <TableHead>Justifié</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {absences.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center py-8 text-gray-500 dark:text-white/50">
                  Aucune absence trouvée
                </TableCell>
              </TableRow>
            ) : (
              absences.map((absence) => (
                <TableRow key={absence.absence_id}>
                  <TableCell className="font-medium flex items-center gap-2">
                    <Clock className="w-4 h-4 text-gray-400" />
                    {absence.employe_nom || "-"}
                  </TableCell>
                  <TableCell>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTypeBadge(absence.type_absence)}`}>
                      {absence.type_absence}
                    </span>
                  </TableCell>
                  <TableCell>{absence.date}</TableCell>
                  <TableCell>{absence.heure_debut || "-"}</TableCell>
                  <TableCell>{absence.heure_fin || "-"}</TableCell>
                  <TableCell>{absence.duree_minutes || "-"}</TableCell>
                  <TableCell className="max-w-xs truncate">{absence.motif || "-"}</TableCell>
                  <TableCell>
                    {absence.justifie ? (
                      <span className="text-green-600">Oui</span>
                    ) : (
                      <span className="text-red-600">Non</span>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
    </DashboardLayout>
  );
}
