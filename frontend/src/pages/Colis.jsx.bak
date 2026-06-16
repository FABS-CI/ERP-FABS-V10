import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { Plus, Search, Package, Truck, Eye, Edit, Trash2, CheckCircle, Clock } from "lucide-react";
import { listColis, deleteColis, updateColisStatut } from "@/services/colisageService";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";
import DashboardLayout from "../components/layout/DashboardLayout";

const Colis = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [statutFilter, setStatutFilter] = useState("");
  const [selectedColis, setSelectedColis] = useState(null);
  const [showDetail, setShowDetail] = useState(false);

  const { data: colisList, isLoading } = useQuery(
    ["colis", search, statutFilter],
    () => listColis({ q: search, statut: statutFilter }),
    { enabled: !!user }
  );

  const deleteMutation = useMutation(deleteColis, {
    onSuccess: () => {
      queryClient.invalidateQueries(["colis"]);
      toast.success("Colis supprimé avec succès");
    },
    onError: () => {
      toast.error("Erreur lors de la suppression");
    },
  });

  const updateStatutMutation = useMutation(
    ({ colisId, statut }) => updateColisStatut(colisId, statut),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(["colis"]);
        toast.success("Statut mis à jour");
      },
      onError: () => {
        toast.error("Erreur lors de la mise à jour du statut");
      },
    }
  );

  const handleDelete = (colisId) => {
    if (window.confirm("Êtes-vous sûr de vouloir supprimer ce colis ?")) {
      deleteMutation.mutate(colisId);
    }
  };

  const handleStatutChange = (colisId, newStatut) => {
    updateStatutMutation.mutate({ colisId, statut: newStatut });
  };

  const getStatutBadge = (statut) => {
    const variants = {
      en_preparation: "secondary",
      pret: "default",
      expedie: "success",
    };
    const labels = {
      en_preparation: "En préparation",
      pret: "Prêt",
      expedie: "Expédié",
    };
    return (
      <Badge variant={variants[statut] || "secondary"}>
        {labels[statut] || statut}
      </Badge>
    );
  };

  if (isLoading) return <div className="p-8">Chargement...</div>;

  return (
    <DashboardLayout>
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-[#0A2540] dark:text-white">Gestion des Colis</h1>
          <p className="text-[#0A2540]/60 dark:text-white/60 mt-1">Liste des colis et expéditions</p>
        </div>
        <Button className="bg-[#0A2540] hover:bg-[#0A2540]/90">
          <Plus className="w-4 h-4 mr-2" />
          Nouveau Colis
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Client, représentant, ville, téléphone..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            <select
              value={statutFilter}
              onChange={(e) => setStatutFilter(e.target.value)}
              className="px-4 py-2 border rounded-md bg-white dark:bg-[#040f1a] dark:border-gray-700"
            >
              <option value="">Tous les statuts</option>
              <option value="en_preparation">En préparation</option>
              <option value="pret">Prêt</option>
              <option value="expedie">Expédié</option>
            </select>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Référence</th>
                  <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Client</th>
                  <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Réf. Commande</th>
                  <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Poids (kg)</th>
                  <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Statut</th>
                  <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Code-barres</th>
                  <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Actions</th>
                </tr>
              </thead>
              <tbody>
                {colisList?.map((colis) => (
                  <tr key={colis.colis_id} className="border-b hover:bg-gray-50 dark:hover:bg-[#040f1a]/50">
                    <td className="py-3 px-4 font-medium">{colis.reference}</td>
                    <td className="py-3 px-4">
                      <div className="font-medium">{colis.client_nom || <span className="text-gray-400 italic">—</span>}</div>
                      {colis.client_ville && <div className="text-xs text-gray-400">{colis.client_ville}</div>}
                    </td>
                    <td className="py-3 px-4 font-mono text-sm text-[#F97316]">
                      {colis.commande_reference || colis.commande_id}
                    </td>
                    <td className="py-3 px-4">{colis.poids_total}</td>
                    <td className="py-3 px-4">{getStatutBadge(colis.statut)}</td>
                    <td className="py-3 px-4 font-mono text-sm">{colis.code_barres}</td>
                    <td className="py-3 px-4">
                      <div className="flex gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedColis(colis);
                            setShowDetail(true);
                          }}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        {colis.statut === "en_preparation" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleStatutChange(colis.colis_id, "pret")}
                          >
                            <CheckCircle className="w-4 h-4" />
                          </Button>
                        )}
                        {(user?.role === "super_admin" || user?.role === "admin") && colis.statut !== "expedie" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(colis.colis_id)}
                          >
                            <Trash2 className="w-4 h-4 text-red-500" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {colisList?.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                Aucun colis trouvé
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Dialog open={showDetail} onOpenChange={setShowDetail}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Détails du Colis</DialogTitle>
            <DialogDescription>
              {selectedColis?.reference}
            </DialogDescription>
          </DialogHeader>
          {selectedColis && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">Référence</label>
                  <p className="font-semibold">{selectedColis.reference}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Code-barres</label>
                  <p className="font-mono">{selectedColis.code_barres}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Commande</label>
                  <p className="font-semibold font-mono text-[#F97316]">
                    {selectedColis.commande_reference || selectedColis.commande_id}
                  </p>
                </div>
                {selectedColis.client_nom && (
                  <div>
                    <label className="text-sm font-medium text-gray-500">Client</label>
                    <p className="font-semibold">{selectedColis.client_nom}</p>
                    {selectedColis.client_ville && <p className="text-sm text-gray-400">{selectedColis.client_ville}</p>}
                    {selectedColis.client_telephone && <p className="text-sm text-gray-400">{selectedColis.client_telephone}</p>}
                  </div>
                )}
                <div>
                  <label className="text-sm font-medium text-gray-500">Statut</label>
                  <div>{getStatutBadge(selectedColis.statut)}</div>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Poids total</label>
                  <p className="font-semibold">{selectedColis.poids_total} kg</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Expédition</label>
                  <p className="font-semibold">{selectedColis.expedition_id || "Non assigné"}</p>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Produits</label>
                <div className="mt-2 space-y-2">
                  {selectedColis.produits.map((prod, idx) => (
                    <div key={idx} className="p-2 bg-gray-50 dark:bg-[#040f1a] rounded">
                      <p className="font-medium">{prod.produit_id}</p>
                      <p className="text-sm text-gray-500">Quantité: {prod.quantite} | Poids: {prod.poids_total} kg</p>
                    </div>
                  ))}
                </div>
              </div>
              {selectedColis.notes && (
                <div>
                  <label className="text-sm font-medium text-gray-500">Notes</label>
                  <p className="mt-1">{selectedColis.notes}</p>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
    </DashboardLayout>
  );
};

export default Colis;
