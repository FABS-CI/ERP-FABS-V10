import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Save, AlertCircle } from "lucide-react";
import { createEmploye, updateEmploye, getEmploye, listDepartements, listFonctions, listCategoriesPro } from "../services/rhApi";
import { useAuth } from "../hooks/useAuth";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";

export default function EmployeForm() {
  const { role } = useAuth();
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = !!id;

  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [departements, setDepartements] = useState([]);
  const [fonctions, setFonctions] = useState([]);
  const [categoriesPro, setCategoriesPro] = useState([]);
  const [error, setError] = useState(null);

  const [form, setForm] = useState({
    nom: "",
    prenoms: "",
    matricule: "",
    departement_id: "",
    fonction_id: "",
    categorie_pro_id: "",
    email: "",
    telephone: "",
    date_embauche: "",
    statut: "actif",
    date_naissance: "",
    lieu_naissance: "",
    nationalite: "",
    adresse: "",
    ville: "",
    numero_cni: "",
    numero_securite_sociale: "",
    banque: "",
    compte_bancaire: "",
    beneficiaire_urgence: "",
    telephone_urgence: "",
    notes: "",
  });

  useEffect(() => {
    loadFilters();
    if (isEdit) {
      loadEmploye();
    } else {
      setLoading(false);
    }
  }, [id]);

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
      toast.error("Erreur lors du chargement des données de référence");
    }
  };

  const loadEmploye = async () => {
    try {
      setLoading(true);
      const data = await getEmploye(id);
      setForm(data);
    } catch (error) {
      console.error("Error loading employe:", error);
      setError("Erreur lors du chargement de l'employé");
      toast.error("Impossible de charger l'employé");
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field, value) => {
    setForm((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation basique
    if (!form.nom || !form.prenoms || !form.matricule || !form.departement_id || !form.fonction_id) {
      toast.error("Veuillez remplir tous les champs obligatoires");
      return;
    }

    try {
      setSaving(true);
      if (isEdit) {
        await updateEmploye(id, form);
        toast.success("Employé mis à jour avec succès");
      } else {
        await createEmploye(form);
        toast.success("Employé créé avec succès");
      }
      navigate("/rh/employes");
    } catch (error) {
      console.error("Error saving employe:", error);
      const message = error.response?.data?.detail || "Erreur lors de l'enregistrement";
      toast.error(message);
      setError(message);
    } finally {
      setSaving(false);
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
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/rh/employes")}
            className="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              {isEdit ? "Modifier l'employé" : "Nouvel Employé"}
            </h1>
            <p className="text-sm text-gray-500 dark:text-white/50">
              {isEdit ? "Mise à jour des informations" : "Création d'une nouvelle fiche employé"}
            </p>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-medium text-red-900 dark:text-red-300">Erreur</h3>
              <p className="text-sm text-red-800 dark:text-red-400 mt-1">{error}</p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Informations personnelles */}
          <div className="bg-white dark:bg-[#0b1e30] rounded-xl p-6 border border-gray-200 dark:border-white/10">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Informations Personnelles</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">
                  Nom *
                </label>
                <Input
                  value={form.nom}
                  onChange={(e) => handleChange("nom", e.target.value)}
                  placeholder="DADJE"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">
                  Prénoms *
                </label>
                <Input
                  value={form.prenoms}
                  onChange={(e) => handleChange("prenoms", e.target.value)}
                  placeholder="Larissa"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">
                  Matricule *
                </label>
                <Input
                  value={form.matricule}
                  onChange={(e) => handleChange("matricule", e.target.value)}
                  placeholder="MAT-001"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">
                  Date de Naissance
                </label>
                <Input
                  type="date"
                  value={form.date_naissance}
                  onChange={(e) => handleChange("date_naissance", e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">
                  Lieu de Naissance
                </label>
                <Input
                  value={form.lieu_naissance}
                  onChange={(e) => handleChange("lieu_naissance", e.target.value)}
                  placeholder="Abidjan"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">
                  Nationalité
                </label>
                <Input
                  value={form.nationalite}
                  onChange={(e) => handleChange("nationalite", e.target.value)}
                  placeholder="Ivoirienne"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">
                  N° CNI
                </label>
                <Input
                  value={form.numero_cni}
                  onChange={(e) => handleChange("numero_cni", e.target.value)}
                  placeholder="XXXXXXXXXX"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">
                  Email
                </label>
                <Input
                  type="email"
                  value={form.email}
                  onChange={(e) => handleChange("email", e.target.value)}
                  placeholder="email@example.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">
                  Téléphone
                </label>
                <Input
                  value={form.telephone}
                  onChange={(e) => handleChange("telephone", e.target.value)}
                  placeholder="+225 XX XX XX XX"
                />
              </div>
            </div>
          </div>

          {/* Informations professionnelles */}
          <div className="bg-white dark:bg-[#0b1e30] rounded-xl p-6 border border-gray-200 dark:border-white/10">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Informations Professionnelles</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">
                  Département *
                </label>
                <Select value={form.departement_id} onValueChange={(value) => handleChange("departement_id", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Sélectionner" />
                  </SelectTrigger>
                  <SelectContent>
                    {departements.map((dept) => (
                      <SelectItem key={dept.departement_id} value={dept.departement_id}>
                        {dept.nom}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">
                  Fonction *
                </label>
                <Select value={form.fonction_id} onValueChange={(value) => handleChange("fonction_id", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Sélectionner" />
                  </SelectTrigger>
                  <SelectContent>
                    {fonctions.map((fct) => (
                      <SelectItem key={fct.fonction_id} value={fct.fonction_id}>
                        {fct.nom}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">
                  Catégorie Professionnelle
                </label>
                <Select value={form.categorie_pro_id} onValueChange={(value) => handleChange("categorie_pro_id", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Sélectionner" />
                  </SelectTrigger>
                  <SelectContent>
                    {categoriesPro.map((cat) => (
                      <SelectItem key={cat.categorie_pro_id} value={cat.categorie_pro_id}>
                        {cat.nom}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">
                  Date d'Embauche
                </label>
                <Input
                  type="date"
                  value={form.date_embauche}
                  onChange={(e) => handleChange("date_embauche", e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">
                  Statut
                </label>
                <Select value={form.statut} onValueChange={(value) => handleChange("statut", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Sélectionner" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="actif">Actif</SelectItem>
                    <SelectItem value="inactif">Inactif</SelectItem>
                    <SelectItem value="conge">En congé</SelectItem>
                    <SelectItem value="suspendu">Suspendu</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Informations bancaires */}
          <div className="bg-white dark:bg-[#0b1e30] rounded-xl p-6 border border-gray-200 dark:border-white/10">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Informations Bancaires</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">
                  Banque
                </label>
                <Input
                  value={form.banque}
                  onChange={(e) => handleChange("banque", e.target.value)}
                  placeholder="Bank"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">
                  Compte Bancaire
                </label>
                <Input
                  value={form.compte_bancaire}
                  onChange={(e) => handleChange("compte_bancaire", e.target.value)}
                  placeholder="IBAN"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">
                  N° Sécurité Sociale
                </label>
                <Input
                  value={form.numero_securite_sociale}
                  onChange={(e) => handleChange("numero_securite_sociale", e.target.value)}
                  placeholder="XXXXXXXXXX"
                />
              </div>
            </div>
          </div>

          {/* Adresse */}
          <div className="bg-white dark:bg-[#0b1e30] rounded-xl p-6 border border-gray-200 dark:border-white/10">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Adresse</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">
                  Adresse
                </label>
                <Input
                  value={form.adresse}
                  onChange={(e) => handleChange("adresse", e.target.value)}
                  placeholder="Adresse complète"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">
                  Ville
                </label>
                <Input
                  value={form.ville}
                  onChange={(e) => handleChange("ville", e.target.value)}
                  placeholder="Abidjan"
                />
              </div>
            </div>
          </div>

          {/* Contact d'urgence */}
          <div className="bg-white dark:bg-[#0b1e30] rounded-xl p-6 border border-gray-200 dark:border-white/10">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Contact d'Urgence</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">
                  Bénéficiaire
                </label>
                <Input
                  value={form.beneficiaire_urgence}
                  onChange={(e) => handleChange("beneficiaire_urgence", e.target.value)}
                  placeholder="Nom du bénéficiaire"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">
                  Téléphone
                </label>
                <Input
                  value={form.telephone_urgence}
                  onChange={(e) => handleChange("telephone_urgence", e.target.value)}
                  placeholder="+225 XX XX XX XX"
                />
              </div>
            </div>
          </div>

          {/* Notes */}
          <div className="bg-white dark:bg-[#0b1e30] rounded-xl p-6 border border-gray-200 dark:border-white/10">
            <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-2">
              Notes
            </label>
            <textarea
              value={form.notes}
              onChange={(e) => handleChange("notes", e.target.value)}
              placeholder="Informations supplémentaires..."
              rows="4"
              className="w-full px-3 py-2 border border-gray-300 dark:border-white/20 rounded-lg bg-white dark:bg-[#0b1e30] text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3">
            <Button
              type="submit"
              disabled={saving}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              <Save className="w-4 h-4 mr-2" />
              {saving ? "Enregistrement..." : "Enregistrer"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate("/rh/employes")}
              disabled={saving}
            >
              Annuler
            </Button>
          </div>
        </form>
      </div>
    </DashboardLayout>
  );
}
