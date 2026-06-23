import { useEffect, useState } from "react";
import { Plus, Briefcase, Edit, Trash2 } from "lucide-react";
import { listFonctions, createFonction, updateFonction, disableFonction } from "../services/rhApi";
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
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";

export default function Fonctions() {
  const [fonctions, setFonctions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingFonction, setEditingFonction] = useState(null);
  const [formData, setFormData] = useState({ nom: "", description: "" });

  useEffect(() => {
    loadFonctions();
  }, []);

  const loadFonctions = async () => {
    try {
      setLoading(true);
      const data = await listFonctions({ actif: true });
      setFonctions(data);
    } catch (error) {
      console.error("Error loading fonctions:", error);
      toast.error("Erreur lors du chargement des fonctions");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingFonction) {
        await updateFonction(editingFonction.fonction_id, formData);
        toast.success("Fonction modifiée avec succès");
      } else {
        await createFonction(formData);
        toast.success("Fonction créée avec succès");
      }
      setIsDialogOpen(false);
      setEditingFonction(null);
      setFormData({ nom: "", description: "" });
      loadFonctions();
    } catch (error) {
      console.error("Error saving fonction:", error);
      toast.error("Erreur lors de l'enregistrement de la fonction");
    }
  };

  const handleEdit = (fonction) => {
    setEditingFonction(fonction);
    setFormData({ nom: fonction.nom, description: fonction.description || "" });
    setIsDialogOpen(true);
  };

  const handleDisable = async (fonctionId) => {
    if (!confirm("Êtes-vous sûr de vouloir désactiver cette fonction ?")) return;
    try {
      await disableFonction(fonctionId);
      toast.success("Fonction désactivée avec succès");
      loadFonctions();
    } catch (error) {
      console.error("Error disabling fonction:", error);
      toast.error("Erreur lors de la désactivation de la fonction");
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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Fonctions</h1>
          <p className="text-sm text-gray-500 dark:text-white/50">Gestion des fonctions/postes</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => { setEditingFonction(null); setFormData({ nom: "", description: "" }); }}>
              <Plus className="w-4 h-4 mr-2" />
              Nouvelle Fonction
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {editingFonction ? "Modifier la Fonction" : "Nouvelle Fonction"}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-sm font-medium">Nom</label>
                <Input
                  value={formData.nom}
                  onChange={(e) => setFormData({ ...formData, nom: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-sm font-medium">Description</label>
                <Textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
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
              <TableHead>Nom</TableHead>
              <TableHead>Description</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {fonctions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={3} className="text-center py-8 text-gray-500 dark:text-white/50">
                  Aucune fonction trouvée
                </TableCell>
              </TableRow>
            ) : (
              fonctions.map((fonc) => (
                <TableRow key={fonc.fonction_id}>
                  <TableCell className="font-medium flex items-center gap-2">
                    <Briefcase className="w-4 h-4 text-gray-400" />
                    {fonc.nom}
                  </TableCell>
                  <TableCell className="text-gray-600 dark:text-white/70">{fonc.description || "-"}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(fonc)}
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDisable(fonc.fonction_id)}
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
