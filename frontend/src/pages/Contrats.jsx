import { useEffect, useState } from "react";
import { Plus, FileText, Edit, Trash2, AlertTriangle } from "lucide-react";
import { listContrats, createContrat, updateContrat, disableContrat } from "../services/rhApi";
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
import PageHeader from "../components/PageHeader";

export default function Contrats() {
  const [contrats, setContrats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingContrat, setEditingContrat] = useState(null);
  const [formData, setFormData] = useState({
    employe_id: "",
    type_contrat: "CDI",
    date_debut: "",
    date_fin: "",
    salaire_base: "",
  });

  useEffect(() => {
    loadContrats();
  }, []);

  const loadContrats = async () => {
    try {
      setLoading(true);
      const data = await listContrats({ actif: true });
      setContrats(data);
    } catch (error) {
      console.error("Error loading contrats:", error);
      toast.error("Erreur lors du chargement des contrats");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        salaire_base: parseFloat(formData.salaire_base),
      };
      if (editingContrat) {
        await updateContrat(editingContrat.contrat_id, payload);
        toast.success("Contrat modifié avec succès");
      } else {
        await createContrat(payload);
        toast.success("Contrat créé avec succès");
      }
      setIsDialogOpen(false);
      setEditingContrat(null);
      setFormData({ employe_id: "", type_contrat: "CDI", date_debut: "", date_fin: "", salaire_base: "" });
      loadContrats();
    } catch (error) {
      console.error("Error saving contrat:", error);
      toast.error("Erreur lors de l'enregistrement du contrat");
    }
  };

  const handleEdit = (contrat) => {
    setEditingContrat(contrat);
    setFormData({
      employe_id: contrat.employe_id,
      type_contrat: contrat.type_contrat,
      date_debut: contrat.date_debut,
      date_fin: contrat.date_fin || "",
      salaire_base: contrat.salaire_base.toString(),
    });
    setIsDialogOpen(true);
  };

  const handleDisable = async (contratId) => {
    if (!confirm("Êtes-vous sûr de vouloir désactiver ce contrat ?")) return;
    try {
      await disableContrat(contratId);
      toast.success("Contrat désactivé avec succès");
      loadContrats();
    } catch (error) {
      console.error("Error disabling contrat:", error);
      toast.error("Erreur lors de la désactivation du contrat");
    }
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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Contrats</h1>
          <p className="text-sm text-gray-500 dark:text-white/50">Gestion des contrats de travail</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => { setEditingContrat(null); setFormData({ employe_id: "", type_contrat: "CDI", date_debut: "", date_fin: "", salaire_base: "" }); }}>
              <Plus className="w-4 h-4 mr-2" />
              Nouveau Contrat
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {editingContrat ? "Modifier le Contrat" : "Nouveau Contrat"}
              </DialogTitle>
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
                <label className="text-sm font-medium">Type de Contrat</label>
                <Select value={formData.type_contrat} onValueChange={(v) => setFormData({ ...formData, type_contrat: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="CDI">CDI</SelectItem>
                    <SelectItem value="CDD">CDD</SelectItem>
                    <SelectItem value="Stage">Stage</SelectItem>
                    <SelectItem value="Consultant">Consultant</SelectItem>
                    <SelectItem value="Prestataire">Prestataire</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Date de Début</label>
                <Input
                  type="date"
                  value={formData.date_debut}
                  onChange={(e) => setFormData({ ...formData, date_debut: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-sm font-medium">Date de Fin (optionnel pour CDI)</label>
                <Input
                  type="date"
                  value={formData.date_fin}
                  onChange={(e) => setFormData({ ...formData, date_fin: e.target.value })}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Salaire Base (FCFA)</label>
                <Input
                  type="number"
                  value={formData.salaire_base}
                  onChange={(e) => setFormData({ ...formData, salaire_base: e.target.value })}
                  required
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                  Annuler
                </Button>
                <Button type="submit">Enregistrer</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="bg-white dark:bg-[#0b1e30] rounded-lg shadow-sm overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Référence</TableHead>
              <TableHead>Employé</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Date Début</TableHead>
              <TableHead>Date Fin</TableHead>
              <TableHead>Salaire</TableHead>
              <TableHead>Statut</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {contrats.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center py-8 text-gray-500 dark:text-white/50">
                  Aucun contrat trouvé
                </TableCell>
              </TableRow>
            ) : (
              contrats.map((contrat) => (
                <TableRow key={contrat.contrat_id}>
                  <TableCell className="font-medium flex items-center gap-2">
                    <FileText className="w-4 h-4 text-gray-400" />
                    {contrat.reference}
                  </TableCell>
                  <TableCell>{contrat.employe_nom || "-"}</TableCell>
                  <TableCell>{contrat.type_contrat}</TableCell>
                  <TableCell>{contrat.date_debut}</TableCell>
                  <TableCell>{contrat.date_fin || "-"}</TableCell>
                  <TableCell>{contrat.salaire_base.toLocaleString()} FCFA</TableCell>
                  <TableCell>
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${
                        contrat.statut === "Actif"
                          ? "bg-green-100 text-green-800"
                          : contrat.statut === "Expiré"
                          ? "bg-red-100 text-red-800"
                          : "bg-gray-100 dark:bg-white/10 text-gray-800 dark:text-white"
                      }`}
                    >
                      {contrat.statut}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(contrat)}
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDisable(contrat.contrat_id)}
                      >
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </Button>
                    </div>
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
