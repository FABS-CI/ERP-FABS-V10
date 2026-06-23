import { useEffect, useState } from "react";
import { Plus, Star, FileText } from "lucide-react";
import { listEvaluations, createEvaluation } from "../services/rhApi";
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

export default function Evaluations() {
  const [evaluations, setEvaluations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    employe_id: "",
    type_evaluation: "commercial",
    periode_debut: "",
    periode_fin: "",
    criteres: {},
    note_globale: "",
    commentaire: "",
    evaluateur_id: "",
  });

  useEffect(() => {
    loadEvaluations();
  }, []);

  const loadEvaluations = async () => {
    try {
      setLoading(true);
      const data = await listEvaluations({ actif: true });
      setEvaluations(data);
    } catch (error) {
      console.error("Error loading evaluations:", error);
      toast.error("Erreur lors du chargement des évaluations");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        note_globale: formData.note_globale ? parseFloat(formData.note_globale) : undefined,
        criteres: {},
      };
      await createEvaluation(payload);
      toast.success("Évaluation créée avec succès");
      setIsDialogOpen(false);
      setFormData({
        employe_id: "",
        type_evaluation: "commercial",
        periode_debut: "",
        periode_fin: "",
        criteres: {},
        note_globale: "",
        commentaire: "",
        evaluateur_id: "",
      });
      loadEvaluations();
    } catch (error) {
      console.error("Error saving evaluation:", error);
      toast.error("Erreur lors de la création de l'évaluation");
    }
  };

  const getStatutBadge = (statut) => {
    const badges = {
      brouillon: "bg-gray-100 dark:bg-white/10 text-gray-800 dark:text-white",
      soumis: "bg-blue-100 text-blue-800",
      approuve: "bg-green-100 text-green-800",
      refuse: "bg-red-100 text-red-800",
    };
    return badges[statut] || "bg-gray-100 dark:bg-white/10 text-gray-800 dark:text-white";
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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Évaluations</h1>
          <p className="text-sm text-gray-500 dark:text-white/50">Évaluations des employés</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => { setFormData({ employe_id: "", type_evaluation: "commercial", periode_debut: "", periode_fin: "", criteres: {}, note_globale: "", commentaire: "", evaluateur_id: "" }); }}>
              <Plus className="w-4 h-4 mr-2" />
              Nouvelle Évaluation
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Nouvelle Évaluation</DialogTitle>
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
                <label className="text-sm font-medium">Type d'Évaluation</label>
                <Select value={formData.type_evaluation} onValueChange={(v) => setFormData({ ...formData, type_evaluation: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="commercial">Commercial</SelectItem>
                    <SelectItem value="magasinier">Magasinier</SelectItem>
                    <SelectItem value="gestionnaire_stock">Gestionnaire Stock</SelectItem>
                    <SelectItem value="administratif">Administratif</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Période Début</label>
                  <Input
                    type="date"
                    value={formData.periode_debut}
                    onChange={(e) => setFormData({ ...formData, periode_debut: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Période Fin</label>
                  <Input
                    type="date"
                    value={formData.periode_fin}
                    onChange={(e) => setFormData({ ...formData, periode_fin: e.target.value })}
                    required
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium">Note Globale (/100)</label>
                <Input
                  type="number"
                  min="0"
                  max="100"
                  value={formData.note_globale}
                  onChange={(e) => setFormData({ ...formData, note_globale: e.target.value })}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Commentaire</label>
                <Textarea
                  value={formData.commentaire}
                  onChange={(e) => setFormData({ ...formData, commentaire: e.target.value })}
                  rows={3}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Évaluateur ID</label>
                <Input
                  value={formData.evaluateur_id}
                  onChange={(e) => setFormData({ ...formData, evaluateur_id: e.target.value })}
                  required
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                  Annuler
                </Button>
                <Button type="submit">Créer</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="bg-white dark:bg-[#0b1e30] rounded-lg shadow-sm overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Employé</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Période Début</TableHead>
              <TableHead>Période Fin</TableHead>
              <TableHead>Note Globale</TableHead>
              <TableHead>Évaluateur</TableHead>
              <TableHead>Statut</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {evaluations.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8 text-gray-500 dark:text-white/50">
                  Aucune évaluation trouvée
                </TableCell>
              </TableRow>
            ) : (
              evaluations.map((evalu) => (
                <TableRow key={evalu.evaluation_id}>
                  <TableCell className="font-medium flex items-center gap-2">
                    <Star className="w-4 h-4 text-gray-400" />
                    {evalu.employe_nom || "-"}
                  </TableCell>
                  <TableCell>{evalu.type_evaluation}</TableCell>
                  <TableCell>{evalu.periode_debut}</TableCell>
                  <TableCell>{evalu.periode_fin}</TableCell>
                  <TableCell>
                    {evalu.note_globale !== null ? (
                      <span className="font-medium">{evalu.note_globale}/100</span>
                    ) : "-"}
                  </TableCell>
                  <TableCell>{evalu.evaluateur_nom || "-"}</TableCell>
                  <TableCell>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatutBadge(evalu.statut)}`}>
                      {evalu.statut}
                    </span>
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
