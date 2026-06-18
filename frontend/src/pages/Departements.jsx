import { useEffect, useState } from "react";
import { Plus, Building2, Edit, Trash2 } from "lucide-react";
import { listDepartements, createDepartement, updateDepartement, disableDepartement } from "../services/rhApi";
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
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/layout/PageHeader";

export default function Departements() {
  const [departements, setDepartements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingDepartement, setEditingDepartement] = useState(null);
  const [formData, setFormData] = useState({ nom: "", description: "" });

  useEffect(() => {
    loadDepartements();
  }, []);

  const loadDepartements = async () => {
    try {
      setLoading(true);
      const data = await listDepartements({ actif: true });
      setDepartements(data);
    } catch (error) {
      console.error("Error loading departements:", error);
      toast.error("Erreur lors du chargement des départements");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingDepartement) {
        await updateDepartement(editingDepartement.departement_id, formData);
        toast.success("Département modifié avec succès");
      } else {
        await createDepartement(formData);
        toast.success("Département créé avec succès");
      }
      setIsDialogOpen(false);
      setEditingDepartement(null);
      setFormData({ nom: "", description: "" });
      loadDepartements();
    } catch (error) {
      console.error("Error saving departement:", error);
      toast.error("Erreur lors de l'enregistrement du département");
    }
  };

  const handleEdit = (departement) => {
    setEditingDepartement(departement);
    setFormData({ nom: departement.nom, description: departement.description || "" });
    setIsDialogOpen(true);
  };

  const handleDisable = async (departementId) => {
    if (!confirm("Êtes-vous sûr de vouloir désactiver ce département ?")) return;
    try {
      await disableDepartement(departementId);
      toast.success("Département désactivé avec succès");
      loadDepartements();
    } catch (error) {
      console.error("Error disabling departement:", error);
      toast.error("Erreur lors de la désactivation du département");
    }
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
    <div className="space-y-6" data-testid="departements-page">
      <PageHeader
        icon={Building2}
        title="Départements"
        description="Gestion des départements de l'entreprise"
        favoriteKey="departements"
        actions={
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button
              className="bg-[#FF6200] hover:bg-[#E65800]"
              data-testid="btn-new-departement"
              onClick={() => { setEditingDepartement(null); setFormData({ nom: "", description: "" }); }}
            >
              <Plus className="w-4 h-4 mr-2" />
              Nouveau Département
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {editingDepartement ? "Modifier le Département" : "Nouveau Département"}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="dep-nom">Nom *</Label>
                <Input
                  id="dep-nom"
                  value={formData.nom}
                  onChange={(e) => setFormData({ ...formData, nom: e.target.value })}
                  required
                  data-testid="input-dep-nom"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="dep-desc">Description</Label>
                <Textarea
                  id="dep-desc"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                  Annuler
                </Button>
                <Button type="submit" className="bg-[#FF6200] hover:bg-[#E65800]" data-testid="btn-submit-departement">
                  Enregistrer
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
        }
      />

      <div className="bg-white dark:bg-[#0b1e30] rounded-lg shadow-sm overflow-hidden" data-testid="departements-table">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nom</TableHead>
              <TableHead>Description</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {departements.length === 0 ? (
              <TableRow>
                <TableCell colSpan={3} className="text-center py-8 text-gray-500 dark:text-white/50">
                  Aucun département trouvé
                </TableCell>
              </TableRow>
            ) : (
              departements.map((dept) => (
                <TableRow key={dept.departement_id}>
                  <TableCell className="font-medium flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-gray-400" />
                    {dept.nom}
                  </TableCell>
                  <TableCell className="text-gray-600 dark:text-white/70">{dept.description || "-"}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(dept)}
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDisable(dept.departement_id)}
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
