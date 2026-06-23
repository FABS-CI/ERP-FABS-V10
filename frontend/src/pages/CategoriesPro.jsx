import { useEffect, useState } from "react";
import { Plus, Layers, Edit, Trash2 } from "lucide-react";
import { listCategoriesPro, createCategoriePro, updateCategoriePro, disableCategoriePro } from "../services/rhApi";
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

export default function CategoriesPro() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingCategorie, setEditingCategorie] = useState(null);
  const [formData, setFormData] = useState({ nom: "", description: "" });

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      setLoading(true);
      const data = await listCategoriesPro({ actif: true });
      setCategories(data);
    } catch (error) {
      console.error("Error loading categories:", error);
      toast.error("Erreur lors du chargement des catégories");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingCategorie) {
        await updateCategoriePro(editingCategorie.categorie_pro_id, formData);
        toast.success("Catégorie modifiée avec succès");
      } else {
        await createCategoriePro(formData);
        toast.success("Catégorie créée avec succès");
      }
      setIsDialogOpen(false);
      setEditingCategorie(null);
      setFormData({ nom: "", description: "" });
      loadCategories();
    } catch (error) {
      console.error("Error saving categorie:", error);
      toast.error("Erreur lors de l'enregistrement de la catégorie");
    }
  };

  const handleEdit = (categorie) => {
    setEditingCategorie(categorie);
    setFormData({ nom: categorie.nom, description: categorie.description || "" });
    setIsDialogOpen(true);
  };

  const handleDisable = async (categorieId) => {
    if (!confirm("Êtes-vous sûr de vouloir désactiver cette catégorie ?")) return;
    try {
      await disableCategoriePro(categorieId);
      toast.success("Catégorie désactivée avec succès");
      loadCategories();
    } catch (error) {
      console.error("Error disabling categorie:", error);
      toast.error("Erreur lors de la désactivation de la catégorie");
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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Catégories Professionnelles</h1>
          <p className="text-sm text-gray-500 dark:text-white/50">Gestion des catégories professionnelles</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => { setEditingCategorie(null); setFormData({ nom: "", description: "" }); }}>
              <Plus className="w-4 h-4 mr-2" />
              Nouvelle Catégorie
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {editingCategorie ? "Modifier la Catégorie" : "Nouvelle Catégorie"}
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
            {categories.length === 0 ? (
              <TableRow>
                <TableCell colSpan={3} className="text-center py-8 text-gray-500 dark:text-white/50">
                  Aucune catégorie trouvée
                </TableCell>
              </TableRow>
            ) : (
              categories.map((cat) => (
                <TableRow key={cat.categorie_pro_id}>
                  <TableCell className="font-medium flex items-center gap-2">
                    <Layers className="w-4 h-4 text-gray-400" />
                    {cat.nom}
                  </TableCell>
                  <TableCell className="text-gray-600 dark:text-white/70">{cat.description || "-"}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(cat)}
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDisable(cat.categorie_pro_id)}
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
