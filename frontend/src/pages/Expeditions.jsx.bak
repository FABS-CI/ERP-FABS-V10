import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { Plus, Search, Truck, Eye, CheckCircle, MapPin, Calendar } from "lucide-react";
import { listExpeditions, createExpedition, updateExpeditionStatut } from "@/services/colisageService";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/layout/PageHeader";

const Expeditions = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [statutFilter, setStatutFilter] = useState("");
  const [selectedExpedition, setSelectedExpedition] = useState(null);
  const [showDetail, setShowDetail] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [formData, setFormData] = useState({
    colis_ids: [],
    commande_id: "",
    adresse_livraison: {
      nom: "",
      adresse: "",
      ville: "",
      pays: "Côte d'Ivoire",
      telephone: "",
    },
    date_expedition: "",
    date_livraison_prevue: "",
    notes: "",
  });

  const { data: expeditionsList, isLoading } = useQuery(
    ["expeditions", search, statutFilter],
    () => listExpeditions({ q: search, statut: statutFilter }),
    { enabled: !!user }
  );

  const createMutation = useMutation(createExpedition, {
    onSuccess: () => {
      queryClient.invalidateQueries(["expeditions"]);
      toast.success("Expédition créée avec succès");
      setShowCreate(false);
      setFormData({
        colis_ids: [],
        commande_id: "",
        adresse_livraison: {
          nom: "",
          adresse: "",
          ville: "",
          pays: "Côte d'Ivoire",
          telephone: "",
        },
        date_expedition: "",
        date_livraison_prevue: "",
        notes: "",
      });
    },
    onError: () => {
      toast.error("Erreur lors de la création");
    },
  });

  const updateStatutMutation = useMutation(
    ({ expeditionId, statut, dateLivraisonReelle }) =>
      updateExpeditionStatut(expeditionId, statut, dateLivraisonReelle),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(["expeditions"]);
        toast.success("Statut mis à jour");
      },
      onError: () => {
        toast.error("Erreur lors de la mise à jour du statut");
      },
    }
  );

  const handleCreate = (e) => {
    e.preventDefault();
    createMutation.mutate(formData);
  };

  const handleStatutChange = (expeditionId, newStatut) => {
    const dateLivraisonReelle = newStatut === "livre" ? new Date().toISOString().split("T")[0] : null;
    updateStatutMutation.mutate({ expeditionId, statut: newStatut, dateLivraisonReelle });
  };

  const getStatutBadge = (statut) => {
    const variants = {
      en_preparation: "secondary",
      pret: "default",
      en_transit: "warning",
      livre: "success",
      annule: "destructive",
    };
    const labels = {
      en_preparation: "En préparation",
      pret: "Prêt",
      en_transit: "En transit",
      livre: "Livré",
      annule: "Annulé",
    };
    return (
      <Badge variant={variants[statut] || "secondary"}>
        {labels[statut] || statut}
      </Badge>
    );
  };

  if (isLoading) return <DashboardLayout><div>Chargement...</div></DashboardLayout>;

  return (
    <DashboardLayout>
    <div data-testid="expeditions-page">
      <PageHeader
        icon={Truck}
        title="Gestion des Expéditions"
        description="Liste des expéditions et livraisons"
        favoriteKey="expeditions"
        actions={
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button className="bg-[#FF6200] hover:bg-[#E65800]" data-testid="btn-new-expedition">
                <Plus className="w-4 h-4 mr-2" />
                Nouvelle Expédition
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Créer une Expédition</DialogTitle>
                <DialogDescription>
                  Sélectionnez les colis et définissez l'adresse de livraison
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleCreate} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="exp-commande">Commande ID *</Label>
                    <Input
                      id="exp-commande"
                      value={formData.commande_id}
                      onChange={(e) => setFormData({ ...formData, commande_id: e.target.value })}
                      required
                      data-testid="input-commande-id"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="exp-colis">Colis IDs (séparés par virgule) *</Label>
                    <Input
                      id="exp-colis"
                      value={formData.colis_ids.join(", ")}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          colis_ids: e.target.value.split(",").map((s) => s.trim()),
                        })
                      }
                      required
                      data-testid="input-colis-ids"
                    />
                  </div>
                </div>
                <div className="rounded-lg border border-gray-200 dark:border-white/10 p-3 space-y-3 bg-gray-50/50 dark:bg-white/5">
                  <Label className="text-[#0A2540] dark:text-white font-semibold">Adresse de livraison</Label>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label htmlFor="exp-nom" className="text-xs text-muted-foreground">Nom destinataire *</Label>
                      <Input
                        id="exp-nom"
                        value={formData.adresse_livraison.nom}
                        onChange={(e) =>
                          setFormData({ ...formData, adresse_livraison: { ...formData.adresse_livraison, nom: e.target.value } })
                        }
                        required
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="exp-tel" className="text-xs text-muted-foreground">Téléphone *</Label>
                      <Input
                        id="exp-tel"
                        value={formData.adresse_livraison.telephone}
                        onChange={(e) =>
                          setFormData({ ...formData, adresse_livraison: { ...formData.adresse_livraison, telephone: e.target.value } })
                        }
                        required
                      />
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="exp-adresse" className="text-xs text-muted-foreground">Adresse *</Label>
                    <Input
                      id="exp-adresse"
                      value={formData.adresse_livraison.adresse}
                      onChange={(e) =>
                        setFormData({ ...formData, adresse_livraison: { ...formData.adresse_livraison, adresse: e.target.value } })
                      }
                      required
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="exp-ville" className="text-xs text-muted-foreground">Ville *</Label>
                    <Input
                      id="exp-ville"
                      value={formData.adresse_livraison.ville}
                      onChange={(e) =>
                        setFormData({ ...formData, adresse_livraison: { ...formData.adresse_livraison, ville: e.target.value } })
                      }
                      required
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="exp-date-dep">Date d'expédition</Label>
                    <Input
                      id="exp-date-dep"
                      type="date"
                      value={formData.date_expedition}
                      onChange={(e) => setFormData({ ...formData, date_expedition: e.target.value })}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="exp-date-liv">Date de livraison prévue</Label>
                    <Input
                      id="exp-date-liv"
                      type="date"
                      value={formData.date_livraison_prevue}
                      onChange={(e) => setFormData({ ...formData, date_livraison_prevue: e.target.value })}
                    />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="exp-notes">Notes</Label>
                  <Textarea
                    id="exp-notes"
                    rows={2}
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  />
                </div>
                <div className="flex gap-2 justify-end">
                  <Button type="button" variant="outline" onClick={() => setShowCreate(false)}>
                    Annuler
                  </Button>
                  <Button type="submit" className="bg-[#FF6200] hover:bg-[#E65800]" data-testid="btn-submit-expedition">
                    Créer l'Expédition
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        }
      />

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
              <option value="en_transit">En transit</option>
              <option value="livre">Livré</option>
              <option value="annule">Annulé</option>
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
                  <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Colis</th>
                  <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Adresse</th>
                  <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Statut</th>
                  <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Actions</th>
                </tr>
              </thead>
              <tbody>
                {expeditionsList?.map((exp) => (
                  <tr key={exp.expedition_id} className="border-b hover:bg-gray-50 dark:hover:bg-[#040f1a]/50">
                    <td className="py-3 px-4 font-medium">{exp.reference}</td>
                    <td className="py-3 px-4">{exp.client_id}</td>
                    <td className="py-3 px-4">{exp.colis_ids.length} colis</td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1">
                        <MapPin className="w-4 h-4 text-gray-400" />
                        <span className="text-sm">{exp.adresse_livraison.ville}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4">{getStatutBadge(exp.statut)}</td>
                    <td className="py-3 px-4">
                      <div className="flex gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedExpedition(exp);
                            setShowDetail(true);
                          }}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        {exp.statut === "pret" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleStatutChange(exp.expedition_id, "en_transit")}
                          >
                            <Truck className="w-4 h-4" />
                          </Button>
                        )}
                        {exp.statut === "en_transit" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleStatutChange(exp.expedition_id, "livre")}
                          >
                            <CheckCircle className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {expeditionsList?.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                Aucune expédition trouvée
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Dialog open={showDetail} onOpenChange={setShowDetail}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Détails de l'Expédition</DialogTitle>
            <DialogDescription>
              {selectedExpedition?.reference}
            </DialogDescription>
          </DialogHeader>
          {selectedExpedition && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">Référence</label>
                  <p className="font-semibold">{selectedExpedition.reference}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Statut</label>
                  <div>{getStatutBadge(selectedExpedition.statut)}</div>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Client</label>
                  <p className="font-semibold">{selectedExpedition.client_id}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Commande</label>
                  <p className="font-semibold">{selectedExpedition.commande_id}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Date d'expédition</label>
                  <p className="font-semibold">{selectedExpedition.date_expedition || "Non définie"}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Date de livraison prévue</label>
                  <p className="font-semibold">{selectedExpedition.date_livraison_prevue || "Non définie"}</p>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Adresse de livraison</label>
                <div className="mt-2 p-3 bg-gray-50 dark:bg-[#040f1a] rounded">
                  <p className="font-semibold">{selectedExpedition.adresse_livraison.nom}</p>
                  <p>{selectedExpedition.adresse_livraison.adresse}</p>
                  <p>{selectedExpedition.adresse_livraison.ville}, {selectedExpedition.adresse_livraison.pays}</p>
                  <p className="text-sm text-gray-500">{selectedExpedition.adresse_livraison.telephone}</p>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Colis ({selectedExpedition.colis_ids.length})</label>
                <div className="mt-2 space-y-1">
                  {selectedExpedition.colis_ids.map((colisId) => (
                    <div key={colisId} className="p-2 bg-gray-50 dark:bg-[#040f1a] rounded text-sm font-mono">
                      {colisId}
                    </div>
                  ))}
                </div>
              </div>
              {selectedExpedition.notes && (
                <div>
                  <label className="text-sm font-medium text-gray-500">Notes</label>
                  <p className="mt-1">{selectedExpedition.notes}</p>
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

export default Expeditions;
