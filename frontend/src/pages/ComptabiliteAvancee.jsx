import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { Plus, Search, BookOpen, FileText, Calculator, CheckCircle, RefreshCw } from "lucide-react";
import { listPlanComptable, listJournaux, listEcritures, createEcriture, generateEcritureFacture } from "@/services/comptabiliteAvanceeService";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/layout/PageHeader";

const ComptabiliteAvancee = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("ecritures"); // ecritures, plan, journaux
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [formData, setFormData] = useState({
    journal_id: "",
    date_ecriture: "",
    libelle: "",
    lignes: [{ compte_id: "", debit: 0, credit: 0 }],
  });

  const { data: ecritures, isLoading: loadingEcritures } = useQuery(
    ["ecritures", search],
    () => listEcritures({ q: search }),
    { enabled: !!user && activeTab === "ecritures" }
  );

  const { data: planComptable, isLoading: loadingPlan } = useQuery(
    ["plan-comptable"],
    () => listPlanComptable(),
    { enabled: !!user && activeTab === "plan" }
  );

  const { data: journaux, isLoading: loadingJournaux } = useQuery(
    ["journaux"],
    () => listJournaux(),
    { enabled: !!user && activeTab === "journaux" }
  );

  const createMutation = useMutation(createEcriture, {
    onSuccess: () => {
      queryClient.invalidateQueries(["ecritures"]);
      toast.success("Écriture créée avec succès");
      setShowCreate(false);
      setFormData({
        journal_id: "",
        date_ecriture: "",
        libelle: "",
        lignes: [{ compte_id: "", debit: 0, credit: 0 }],
      });
    },
    onError: () => {
      toast.error("Erreur lors de la création");
    },
  });

  const generateMutation = useMutation(generateEcritureFacture, {
    onSuccess: () => {
      queryClient.invalidateQueries(["ecritures"]);
      toast.success("Écriture générée automatiquement");
    },
    onError: () => {
      toast.error("Erreur lors de la génération");
    },
  });

  const handleCreate = (e) => {
    e.preventDefault();
    createMutation.mutate(formData);
  };

  const handleGenerateAuto = (factureId) => {
    generateMutation.mutate(factureId);
  };

  const addLigne = () => {
    setFormData({
      ...formData,
      lignes: [...formData.lignes, { compte_id: "", debit: 0, credit: 0 }],
    });
  };

  const updateLigne = (index, field, value) => {
    const newLignes = [...formData.lignes];
    newLignes[index][field] = value;
    setFormData({ ...formData, lignes: newLignes });
  };

  if (loadingEcritures || loadingPlan || loadingJournaux) return <DashboardLayout><div>Chargement...</div></DashboardLayout>;

  return (
    <DashboardLayout>
    <div data-testid="compta-avancee-page">
      <PageHeader
        icon={Calculator}
        title="Comptabilité Avancée"
        description="Plan comptable, journaux et écritures"
        favoriteKey="comptabilite-avancee"
        actions={
          <div className="flex gap-2">
            <Button
              variant={activeTab === "ecritures" ? "default" : "outline"}
              onClick={() => setActiveTab("ecritures")}
              className={activeTab === "ecritures" ? "bg-[#FF6200] hover:bg-[#E65800]" : ""}
              data-testid="tab-ecritures"
            >
              <FileText className="w-4 h-4 mr-2" />
              Écritures
            </Button>
            <Button
              variant={activeTab === "plan" ? "default" : "outline"}
              onClick={() => setActiveTab("plan")}
              className={activeTab === "plan" ? "bg-[#FF6200] hover:bg-[#E65800]" : ""}
              data-testid="tab-plan"
            >
              <BookOpen className="w-4 h-4 mr-2" />
              Plan Comptable
            </Button>
            <Button
              variant={activeTab === "journaux" ? "default" : "outline"}
              onClick={() => setActiveTab("journaux")}
              className={activeTab === "journaux" ? "bg-[#FF6200] hover:bg-[#E65800]" : ""}
              data-testid="tab-journaux"
            >
              <Calculator className="w-4 h-4 mr-2" />
              Journaux
            </Button>
          </div>
        }
      />

      {activeTab === "ecritures" && (
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div className="flex gap-4 flex-1">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input
                    placeholder="Rechercher une écriture..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              <Dialog open={showCreate} onOpenChange={setShowCreate}>
                <DialogTrigger asChild>
                  <Button className="bg-[#0A2540] hover:bg-[#0A2540]/90">
                    <Plus className="w-4 h-4 mr-2" />
                    Nouvelle Écriture
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl">
                  <DialogHeader>
                    <DialogTitle>Créer une Écriture Comptable</DialogTitle>
                    <DialogDescription>
                      Saisissez les détails de l'écriture comptable
                    </DialogDescription>
                  </DialogHeader>
                  <form onSubmit={handleCreate} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Journal</Label>
                        <select
                          value={formData.journal_id}
                          onChange={(e) => setFormData({ ...formData, journal_id: e.target.value })}
                          className="w-full px-3 py-2 border rounded-md"
                          required
                        >
                          <option value="">Sélectionner</option>
                          {journaux?.map((j) => (
                            <option key={j.journal_id} value={j.journal_id}>
                              {j.code} - {j.intitule}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <Label>Date</Label>
                        <Input
                          type="date"
                          value={formData.date_ecriture}
                          onChange={(e) => setFormData({ ...formData, date_ecriture: e.target.value })}
                          required
                        />
                      </div>
                    </div>
                    <div>
                      <Label>Libellé</Label>
                      <Input
                        value={formData.libelle}
                        onChange={(e) => setFormData({ ...formData, libelle: e.target.value })}
                        required
                      />
                    </div>
                    <div>
                      <Label>Lignes</Label>
                      <div className="space-y-2 mt-2">
                        {formData.lignes.map((ligne, idx) => (
                          <div key={idx} className="grid grid-cols-3 gap-2">
                            <select
                              value={ligne.compte_id}
                              onChange={(e) => updateLigne(idx, "compte_id", e.target.value)}
                              className="px-3 py-2 border rounded-md"
                              required
                            >
                              <option value="">Compte</option>
                              {planComptable?.map((c) => (
                                <option key={c.compte_id} value={c.compte_id}>
                                  {c.numero} - {c.intitule}
                                </option>
                              ))}
                            </select>
                            <Input
                              type="number"
                              placeholder="Débit"
                              value={ligne.debit}
                              onChange={(e) => updateLigne(idx, "debit", parseFloat(e.target.value) || 0)}
                            />
                            <Input
                              type="number"
                              placeholder="Crédit"
                              value={ligne.credit}
                              onChange={(e) => updateLigne(idx, "credit", parseFloat(e.target.value) || 0)}
                            />
                          </div>
                        ))}
                        <Button type="button" variant="outline" onClick={addLigne} className="w-full">
                          <Plus className="w-4 h-4 mr-2" />
                          Ajouter une ligne
                        </Button>
                      </div>
                    </div>
                    <Button type="submit" className="w-full bg-[#0A2540] hover:bg-[#0A2540]/90">
                      Créer l'Écriture
                    </Button>
                  </form>
                </DialogContent>
              </Dialog>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Référence</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Date</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Libellé</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Débit</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Crédit</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {ecritures?.map((ecriture) => (
                    <tr key={ecriture.ecriture_id} className="border-b hover:bg-gray-50 dark:hover:bg-[#040f1a]/50">
                      <td className="py-3 px-4 font-medium">{ecriture.reference}</td>
                      <td className="py-3 px-4">{ecriture.date_ecriture}</td>
                      <td className="py-3 px-4">{ecriture.libelle}</td>
                      <td className="py-3 px-4">{ecriture.montant_total_debit} FCFA</td>
                      <td className="py-3 px-4">{ecriture.montant_total_credit} FCFA</td>
                      <td className="py-3 px-4">
                        {ecriture.type_source === "facture" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleGenerateAuto(ecriture.reference_source)}
                          >
                            <RefreshCw className="w-4 h-4" />
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {ecritures?.length === 0 && (
                <div className="text-center py-8 text-gray-500 dark:text-white/50">
                  Aucune écriture trouvée
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === "plan" && (
        <Card>
          <CardHeader>
            <CardTitle>Plan Comptable SYSCOHADA</CardTitle>
            <CardDescription>Structure hiérarchique des comptes</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Numéro</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Intitulé</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Type</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Classe</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Solde Débit</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Solde Crédit</th>
                  </tr>
                </thead>
                <tbody>
                  {planComptable?.map((compte) => (
                    <tr key={compte.compte_id} className="border-b hover:bg-gray-50 dark:hover:bg-[#040f1a]/50">
                      <td className="py-3 px-4 font-mono">{compte.numero}</td>
                      <td className="py-3 px-4">{compte.intitule}</td>
                      <td className="py-3 px-4">
                        <Badge variant={compte.type === "actif" || compte.type === "charge" ? "default" : "secondary"}>
                          {compte.type}
                        </Badge>
                      </td>
                      <td className="py-3 px-4">{compte.classe}</td>
                      <td className="py-3 px-4">{compte.solde_debit} FCFA</td>
                      <td className="py-3 px-4">{compte.solde_credit} FCFA</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === "journaux" && (
        <Card>
          <CardHeader>
            <CardTitle>Journaux Comptables</CardTitle>
            <CardDescription>Liste des journaux de l'entreprise</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {journaux?.map((journal) => (
                <div key={journal.journal_id} className="p-4 border rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Calculator className="w-5 h-5 text-[#FF6200]" />
                    <h3 className="font-semibold">{journal.code}</h3>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{journal.intitule}</p>
                  <Badge variant={journal.actif ? "default" : "secondary"} className="mt-2">
                    {journal.actif ? "Actif" : "Inactif"}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
    </DashboardLayout>
  );
};

export default ComptabiliteAvancee;
