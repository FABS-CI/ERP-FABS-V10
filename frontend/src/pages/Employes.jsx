import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Search, Filter, Eye, Edit, Trash2, UserPlus } from "lucide-react";
import { listEmployes, disableEmploye, listDepartements, listFonctions, listCategoriesPro } from "../services/rhApi";
import { useAuth } from "../hooks/useAuth";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
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

export default function Employes() {
  const { role } = useAuth();
  const navigate = useNavigate();
  const [employes, setEmployes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedEmploye, setSelectedEmploye] = useState(null);
  const [filterDepartement, setFilterDepartement] = useState("");
  const [filterFonction, setFilterFonction] = useState("");
  const [filterCategoriePro, setFilterCategoriePro] = useState("");
  const [filterStatut, setFilterStatut] = useState("");
  const [departements, setDepartements] = useState([]);
  const [fonctions, setFonctions] = useState([]);
  const [categoriesPro, setCategoriesPro] = useState([]);
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    loadEmployes();
    loadFilters();
  }, []);

  const loadFilters = async () => {
    try {
      const [depts, fcts, cats] = await Promise.all([
        listDepartements({ actif: true }),
        listFonctions({ actif: true }),
        listCategoriesPro({ actif: true }),
      ]);
      setDepartements(depts);
      setFonctions(fcts);
      setCategoriesPro(cats);
    } catch (error) {
      console.error("Error loading filters:", error);
    }
  };

  const loadEmployes = async () => {
    try {
      setLoading(true);
      const params = { limit: 100 };
      if (filterDepartement) params.departement_id = filterDepartement;
      if (filterFonction) params.fonction_id = filterFonction;
      if (filterCategoriePro) params.categorie_pro_id = filterCategoriePro;
      if (filterStatut) params.statut = filterStatut;
      const data = await listEmployes(params);
      setEmployes(data);
    } catch (error) {
      console.error("Error loading employes:", error);
      toast.error("Erreur lors du chargement des employés");
    } finally {
      setLoading(false);
    }
  };

  const filteredEmployes = employes.filter((emp) =>
    emp.nom.toLowerCase().includes(searchTerm.toLowerCase()) ||
    emp.prenoms.toLowerCase().includes(searchTerm.toLowerCase()) ||
    emp.matricule.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleDisable = async (employeId) => {
    if (!confirm("Êtes-vous sûr de vouloir désactiver cet employé ?")) return;
    
    try {
      await disableEmploye(employeId);
      toast.success("Employé désactivé avec succès");
      loadEmployes();
    } catch (error) {
      console.error("Error disabling employe:", error);
      toast.error("Erreur lors de la désactivation de l'employé");
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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Employés</h1>
          <p className="text-sm text-gray-500 dark:text-white/50">Gestion des employés</p>
        </div>
        <Button onClick={() => navigate("/rh/employes/new")}>
          <Plus className="w-4 h-4 mr-2" />
          Nouvel Employé
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            placeholder="Rechercher par nom, prénom ou matricule..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button variant="outline" onClick={() => setShowFilters(!showFilters)}>
          <Filter className="w-4 h-4 mr-2" />
          Filtres
        </Button>
      </div>

      {/* Advanced Filters */}
      {showFilters && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-gray-50 dark:bg-white/5 rounded-lg">
          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-white/90 mb-1 block">Département</label>
            <Select value={filterDepartement} onValueChange={(value) => { setFilterDepartement(value); loadEmployes(); }}>
              <SelectTrigger>
                <SelectValue placeholder="Tous" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Tous</SelectItem>
                {departements.map((dept) => (
                  <SelectItem key={dept.departement_id} value={dept.departement_id}>
                    {dept.nom}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-white/90 mb-1 block">Fonction</label>
            <Select value={filterFonction} onValueChange={(value) => { setFilterFonction(value); loadEmployes(); }}>
              <SelectTrigger>
                <SelectValue placeholder="Toutes" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Toutes</SelectItem>
                {fonctions.map((fct) => (
                  <SelectItem key={fct.fonction_id} value={fct.fonction_id}>
                    {fct.nom}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-white/90 mb-1 block">Catégorie Pro</label>
            <Select value={filterCategoriePro} onValueChange={(value) => { setFilterCategoriePro(value); loadEmployes(); }}>
              <SelectTrigger>
                <SelectValue placeholder="Toutes" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Toutes</SelectItem>
                {categoriesPro.map((cat) => (
                  <SelectItem key={cat.categorie_pro_id} value={cat.categorie_pro_id}>
                    {cat.nom}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-white/90 mb-1 block">Statut</label>
            <Select value={filterStatut} onValueChange={(value) => { setFilterStatut(value); loadEmployes(); }}>
              <SelectTrigger>
                <SelectValue placeholder="Tous" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Tous</SelectItem>
                <SelectItem value="Actif">Actif</SelectItem>
                <SelectItem value="En conge">En congé</SelectItem>
                <SelectItem value="Suspendu">Suspendu</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="bg-white dark:bg-[#0b1e30] rounded-lg shadow-sm overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Matricule</TableHead>
              <TableHead>Nom & Prénoms</TableHead>
              <TableHead>Fonction</TableHead>
              <TableHead>Département</TableHead>
              <TableHead>Statut</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredEmployes.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-gray-500 dark:text-white/50">
                  Aucun employé trouvé
                </TableCell>
              </TableRow>
            ) : (
              filteredEmployes.map((emp) => (
                <TableRow key={emp.employe_id}>
                  <TableCell className="font-medium">{emp.matricule}</TableCell>
                  <TableCell>
                    <div>
                      <div className="font-medium">{emp.nom}</div>
                      <div className="text-sm text-gray-500 dark:text-white/50">{emp.prenoms}</div>
                    </div>
                  </TableCell>
                  <TableCell>{emp.fonction_nom || "-"}</TableCell>
                  <TableCell>{emp.departement_nom || "-"}</TableCell>
                  <TableCell>
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${
                        emp.statut === "Actif"
                          ? "bg-green-100 text-green-800"
                          : emp.statut === "En conge"
                          ? "bg-orange-100 text-orange-800"
                          : "bg-gray-100 dark:bg-white/10 text-gray-800 dark:text-white"
                      }`}
                    >
                      {emp.statut}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setSelectedEmploye(emp)}
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                          <DialogHeader>
                            <DialogTitle>Détails de l'Employé</DialogTitle>
                          </DialogHeader>
                          {selectedEmploye && (
                            <div className="space-y-4">
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <p className="text-sm font-medium text-gray-500 dark:text-white/50">Matricule</p>
                                  <p className="font-medium">{selectedEmploye.matricule}</p>
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-gray-500 dark:text-white/50">Nom</p>
                                  <p className="font-medium">{selectedEmploye.nom}</p>
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-gray-500 dark:text-white/50">Prénoms</p>
                                  <p className="font-medium">{selectedEmploye.prenoms}</p>
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-gray-500 dark:text-white/50">Sexe</p>
                                  <p className="font-medium">{selectedEmploye.sexe}</p>
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-gray-500 dark:text-white/50">Date de Naissance</p>
                                  <p className="font-medium">{selectedEmploye.date_naissance}</p>
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-gray-500 dark:text-white/50">Nationalité</p>
                                  <p className="font-medium">{selectedEmploye.nationalite}</p>
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-gray-500 dark:text-white/50">Téléphone</p>
                                  <p className="font-medium">{selectedEmploye.telephone_principal}</p>
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-gray-500 dark:text-white/50">Email</p>
                                  <p className="font-medium">{selectedEmploye.email || "-"}</p>
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-gray-500 dark:text-white/50">Fonction</p>
                                  <p className="font-medium">{selectedEmploye.fonction_nom || "-"}</p>
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-gray-500 dark:text-white/50">Département</p>
                                  <p className="font-medium">{selectedEmploye.departement_nom || "-"}</p>
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-gray-500 dark:text-white/50">Date d'Embauche</p>
                                  <p className="font-medium">{selectedEmploye.date_embauche}</p>
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-gray-500 dark:text-white/50">Statut</p>
                                  <p className="font-medium">{selectedEmploye.statut}</p>
                                </div>
                              </div>
                              <div className="flex gap-2 pt-4">
                                <Button
                                  onClick={() => navigate(`/rh/employes/${selectedEmploye.employe_id}/edit`)}
                                >
                                  <Edit className="w-4 h-4 mr-2" />
                                  Modifier
                                </Button>
                              </div>
                            </div>
                          )}
                        </DialogContent>
                      </Dialog>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/rh/employes/${emp.employe_id}/edit`)}
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDisable(emp.employe_id)}
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
