import { useEffect, useState } from "react";
import { Plus, Calendar, Check, X, Clock } from "lucide-react";
import { listConges, createConge, approuverCongeSup, approuverCongeDirection, approuverCongeRH } from "../services/rhApi";
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

export default function Conges() {
  const [conges, setConges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    employe_id: "",
    type_conge: "conge_annuel",
    date_debut: "",
    date_fin: "",
    nombre_jours: "",
    motif: "",
  });

  useEffect(() => {
    loadConges();
  }, []);

  const loadConges = async () => {
    try {
      setLoading(true);
      const data = await listConges({ actif: true });
      setConges(data);
    } catch (error) {
      console.error("Error loading conges:", error);
      toast.error("Erreur lors du chargement des congés");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        nombre_jours: parseInt(formData.nombre_jours),
      };
      await createConge(payload);
      toast.success("Demande de congé créée avec succès");
      setIsDialogOpen(false);
      setFormData({ employe_id: "", type_conge: "conge_annuel", date_debut: "", date_fin: "", nombre_jours: "", motif: "" });
      loadConges();
    } catch (error) {
      console.error("Error saving conge:", error);
      toast.error("Erreur lors de la création de la demande de congé");
    }
  };

  const handleApprouverSup = async (congeId) => {
    const commentaire = prompt("Commentaire (optionnel):");
    try {
      await approuverCongeSup(congeId, { commentaire });
      toast.success("Congé approuvé par supérieur");
      loadConges();
    } catch (error) {
      console.error("Error approving conge:", error);
      toast.error("Erreur lors de l'approbation");
    }
  };

  const handleApprouverDirection = async (congeId) => {
    const commentaire = prompt("Commentaire (optionnel):");
    try {
      await approuverCongeDirection(congeId, { commentaire });
      toast.success("Congé approuvé par direction");
      loadConges();
    } catch (error) {
      console.error("Error approving conge:", error);
      toast.error("Erreur lors de l'approbation");
    }
  };

  const handleApprouverRH = async (congeId) => {
    const commentaire = prompt("Commentaire (optionnel):");
    try {
      await approuverCongeRH(congeId, { commentaire });
      toast.success("Congé approuvé par RH - Employé mis en congé");
      loadConges();
    } catch (error) {
      console.error("Error approving conge:", error);
      toast.error("Erreur lors de l'approbation");
    }
  };

  const getStatutBadge = (statut) => {
    const badges = {
      en_attente: "bg-yellow-100 text-yellow-800",
      approuve_sup: "bg-blue-100 text-blue-800",
      approuve_direction: "bg-purple-100 text-purple-800",
      approuve_rh: "bg-green-100 text-green-800",
      refuse: "bg-red-100 text-red-800",
      annule: "bg-gray-100 dark:bg-white/10 text-gray-800 dark:text-white",
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
    <div className="space-y-6" data-testid="conges-page">
      <PageHeader
        icon={Calendar}
        title="Congés"
        description="Gestion des demandes de congé"
        favoriteKey="conges"
        actions={
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-[#FF6200] hover:bg-[#E65800]" data-testid="btn-new-conge" onClick={() => { setFormData({ employe_id: "", type_conge: "conge_annuel", date_debut: "", date_fin: "", nombre_jours: "", motif: "" }); }}>
              <Plus className="w-4 h-4 mr-2" />
              Nouvelle Demande
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Nouvelle Demande de Congé</DialogTitle>
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
                <label className="text-sm font-medium">Type de Congé</label>
                <Select value={formData.type_conge} onValueChange={(v) => setFormData({ ...formData, type_conge: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="conge_annuel">Congé Annuel</SelectItem>
                    <SelectItem value="conge_maladie">Congé Maladie</SelectItem>
                    <SelectItem value="conge_maternite">Congé Maternité</SelectItem>
                    <SelectItem value="permission">Permission</SelectItem>
                    <SelectItem value="conge_exceptionnel">Congé Exceptionnel</SelectItem>
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
                <label className="text-sm font-medium">Date de Fin</label>
                <Input
                  type="date"
                  value={formData.date_fin}
                  onChange={(e) => setFormData({ ...formData, date_fin: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-sm font-medium">Nombre de Jours</label>
                <Input
                  type="number"
                  value={formData.nombre_jours}
                  onChange={(e) => setFormData({ ...formData, nombre_jours: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-sm font-medium">Motif</label>
                <Textarea
                  value={formData.motif}
                  onChange={(e) => setFormData({ ...formData, motif: e.target.value })}
                  rows={3}
                  required
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                  Annuler
                </Button>
                <Button type="submit" className="bg-[#FF6200] hover:bg-[#E65800]" data-testid="btn-submit-conge">Soumettre</Button>
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
              <TableHead>Date Début</TableHead>
              <TableHead>Date Fin</TableHead>
              <TableHead>Jours</TableHead>
              <TableHead>Motif</TableHead>
              <TableHead>Statut</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {conges.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center py-8 text-gray-500 dark:text-white/50">
                  Aucune demande de congé trouvée
                </TableCell>
              </TableRow>
            ) : (
              conges.map((conge) => (
                <TableRow key={conge.conge_id}>
                  <TableCell className="font-medium flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-gray-400" />
                    {conge.employe_nom || "-"}
                  </TableCell>
                  <TableCell>{conge.type_conge}</TableCell>
                  <TableCell>{conge.date_debut}</TableCell>
                  <TableCell>{conge.date_fin}</TableCell>
                  <TableCell>{conge.nombre_jours}</TableCell>
                  <TableCell className="max-w-xs truncate">{conge.motif}</TableCell>
                  <TableCell>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatutBadge(conge.statut)}`}>
                      {conge.statut}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      {conge.statut === "en_attente" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleApprouverSup(conge.conge_id)}
                          title="Approuver par supérieur"
                        >
                          <Check className="w-4 h-4 text-green-500" />
                        </Button>
                      )}
                      {conge.statut === "approuve_sup" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleApprouverDirection(conge.conge_id)}
                          title="Approuver par direction"
                        >
                          <Check className="w-4 h-4 text-blue-500" />
                        </Button>
                      )}
                      {conge.statut === "approuve_direction" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleApprouverRH(conge.conge_id)}
                          title="Approuver par RH"
                        >
                          <Check className="w-4 h-4 text-purple-500" />
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
    </div>
    </DashboardLayout>
  );
}
