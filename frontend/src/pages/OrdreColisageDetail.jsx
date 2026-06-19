import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "react-query";
import {
  Package, ArrowLeft, Zap, CheckCircle, Printer, QrCode,
  Box, AlertCircle, RefreshCw, Trash2, ChevronDown, ChevronRight
} from "lucide-react";
import {
  getOrdreColisage, getCartonsSuggeres, genererCartonsAuto,
  listCartons, validerCarton, deleteCarton, updateOrdreColisageStatut,
  getCartonQrCodeUrl, downloadCartonEtiquette, downloadOrdreEtiquettesBulk
} from "@/services/colisageService";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/layout/PageHeader";

const STATUT_CONFIG = {
  a_coliser: { label: "À coliser", color: "bg-yellow-100 text-yellow-800" },
  en_preparation: { label: "En préparation", color: "bg-blue-100 text-blue-800" },
  colisage_termine: { label: "Terminé", color: "bg-purple-100 text-purple-800" },
  livre: { label: "Livré", color: "bg-green-100 text-green-800" },
  expedie: { label: "Expédié", color: "bg-indigo-100 text-indigo-800" },
  cloture: { label: "Clôturé", color: "bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-white/90" },
  annule: { label: "Annulé", color: "bg-red-100 text-red-800" },
};

const STATUT_TRANSITIONS = {
  a_coliser: ["en_preparation", "annule"],
  en_preparation: ["colisage_termine", "a_coliser", "annule"],
  colisage_termine: ["livre", "expedie", "cloture"],
  livre: ["cloture"],
  expedie: ["cloture"],
};

const CARTON_STATUT = {
  en_preparation: { label: "Préparation", color: "bg-yellow-100 text-yellow-800" },
  pret: { label: "Prêt", color: "bg-green-100 text-green-800" },
  charge: { label: "Chargé", color: "bg-blue-100 text-blue-800" },
  livre: { label: "Livré", color: "bg-indigo-100 text-indigo-800" },
  incident: { label: "Incident", color: "bg-red-100 text-red-800" },
};

const StatutBadge = ({ statut, config = STATUT_CONFIG }) => {
  const cfg = config[statut] || { label: statut, color: "bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-white/90" };
  return (
    <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.color}`}>
      {cfg.label}
    </span>
  );
};

function EtiquetteCarton({ carton }) {
  return (
    <div className="border-2 border-black p-3 w-64 font-mono text-xs" style={{ fontFamily: "monospace" }}>
      <div className="text-center font-bold text-sm mb-1">EDITIONS FABS-CI</div>
      <div className="border-t border-black pt-1 mb-1">
        <div className="font-bold">{carton.reference}</div>
        <div>Cmd: {carton.ordre_reference}</div>
      </div>
      <div className="text-center my-1">
        <div className="text-[10px] uppercase tracking-wider text-gray-600">Carton</div>
        <div className="text-3xl font-bold leading-none">
          {carton.numero_carton}/{carton.total_cartons}
        </div>
      </div>
      <div className="text-xs">
        <div>Articles: {carton.total_articles ?? "—"} unités</div>
      </div>
      <div className="text-center mt-2 text-xs text-gray-600 dark:text-white/70">
        {carton.qr_code_url || `fabsci.ci/carton/${carton._id}`}
      </div>
    </div>
  );
}

export default function OrdreColisageDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showGenerer, setShowGenerer] = useState(false);
  const [showStatut, setShowStatut] = useState(false);
  const [showEtiquette, setShowEtiquette] = useState(null);
  const [newStatut, setNewStatut] = useState("");
  const [statutNotes, setStatutNotes] = useState("");
  const [genererConfig, setGenererConfig] = useState({ forcer: false });
  const [expandedCarton, setExpandedCarton] = useState(null);

  const { data: ordre, isLoading } = useQuery(
    ["ordre-colisage", id],
    () => getOrdreColisage(id),
    { enabled: !!id }
  );

  const { data: cartonsData } = useQuery(
    ["cartons-ordre", id],
    () => listCartons({ ordre_id: id }),
    { enabled: !!id }
  );

  const { data: suggestion } = useQuery(
    ["cartons-suggeres", id],
    () => getCartonsSuggeres(id),
    { enabled: !!id && ordre?.statut === "a_coliser" }
  );

  const genererMutation = useMutation(
    (config) => genererCartonsAuto(id, config),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(["cartons-ordre", id]);
        queryClient.invalidateQueries(["ordre-colisage", id]);
        toast.success(`${data.cartons_crees} cartons générés`);
        setShowGenerer(false);
      },
      onError: (err) => toast.error(err?.response?.data?.detail || "Erreur génération"),
    }
  );

  const validerMutation = useMutation(
    (cartonId) => validerCarton(cartonId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(["cartons-ordre", id]);
        toast.success("Carton validé");
      },
      onError: (err) => toast.error(err?.response?.data?.detail || "Erreur"),
    }
  );

  const supprimerMutation = useMutation(
    (cartonId) => deleteCarton(cartonId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(["cartons-ordre", id]);
        queryClient.invalidateQueries(["ordre-colisage", id]);
        toast.success("Carton supprimé");
      },
      onError: (err) => toast.error(err?.response?.data?.detail || "Erreur"),
    }
  );

  const statutMutation = useMutation(
    ({ statut, notes }) => updateOrdreColisageStatut(id, statut, notes),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(["ordre-colisage", id]);
        queryClient.invalidateQueries(["ordres-colisage"]);
        queryClient.invalidateQueries(["colisage-dashboard"]);
        toast.success("Statut mis à jour");
        setShowStatut(false);
      },
      onError: (err) => toast.error(err?.response?.data?.detail || "Erreur"),
    }
  );

  const cartons = cartonsData?.items || cartonsData || [];
  const transitions = STATUT_TRANSITIONS[ordre?.statut] || [];

  const handlePrintEtiquettes = () => {
    downloadOrdreEtiquettesBulk(id);
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64 text-gray-400">
          <RefreshCw className="w-6 h-6 animate-spin mr-2" /> Chargement...
        </div>
      </DashboardLayout>
    );
  }

  if (!ordre) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center h-64 text-gray-400">
          <AlertCircle className="w-8 h-8 mb-2" />
          <p>Ordre introuvable</p>
          <Button variant="outline" className="mt-3" onClick={() => navigate("/ordres-colisage")}>
            Retour
          </Button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6 print:m-0">
        {/* Header */}
        <div className="print:hidden">
          <PageHeader
            title={ordre.reference}
            description={`Facture ${ordre.facture_reference || ordre.facture_id} · Client: ${ordre.client_nom || "—"}`}
            icon={Package}
            accentColor="#F97316"
            favoriteKey="ordres_colisage"
            actions={
              <div className="flex items-center gap-2 flex-wrap">
                <Button variant="outline" size="sm" onClick={() => navigate("/ordres-colisage")} className="gap-1">
                  <ArrowLeft className="w-4 h-4" /> Retour
                </Button>
                {transitions.length > 0 && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1"
                    onClick={() => { setShowStatut(true); setNewStatut(transitions[0]); }}
                  >
                    <CheckCircle className="w-4 h-4" /> Avancer statut
                  </Button>
                )}
                {(ordre.statut === "a_coliser" || ordre.statut === "en_preparation") && (
                  <Button size="sm" className="gap-1" onClick={() => setShowGenerer(true)}>
                    <Zap className="w-4 h-4" /> Générer cartons
                  </Button>
                )}
                {cartons.length > 0 && (
                  <Button size="sm" variant="outline" className="gap-1" onClick={handlePrintEtiquettes}>
                    <Printer className="w-4 h-4" /> Imprimer étiquettes
                  </Button>
                )}
              </div>
            }
          />
        </div>

        {/* Info ordre */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 print:hidden">
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-gray-500 dark:text-white/50">Statut</p>
              <div className="mt-1"><StatutBadge statut={ordre.statut} /></div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-gray-500 dark:text-white/50">Mode expédition</p>
              <p className="text-sm font-medium capitalize mt-1">
                {ordre.mode_expedition_prevu?.replace("_", " ") || "—"}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-gray-500 dark:text-white/50">Cartons</p>
              <p className="text-xl font-bold text-orange-600 mt-1">{cartons.length}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-gray-500 dark:text-white/50">Priorité</p>
              <p className="text-sm font-medium capitalize mt-1">{ordre.priorite || "normale"}</p>
            </CardContent>
          </Card>
        </div>

        {/* Suggestion (si pas encore de cartons) */}
        {suggestion && cartons.length === 0 && ordre.statut !== "annule" && (
          <Card className="border-orange-200 bg-orange-50 print:hidden">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <Zap className="w-5 h-5 text-orange-500 mt-0.5" />
                <div className="flex-1">
                  <p className="font-medium text-orange-800">Suggestion automatique</p>
                  <p className="text-sm text-orange-700 mt-1">
                    {suggestion.nb_cartons_suggeres} carton(s) nécessaires pour {suggestion.total_articles} articles
                    ({suggestion.lignes?.length} lignes de produits)
                  </p>
                  <Button
                    size="sm"
                    className="mt-2 bg-orange-600 hover:bg-orange-700"
                    onClick={() => setShowGenerer(true)}
                  >
                    Générer automatiquement
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Lignes de commande */}
        {ordre.lignes && ordre.lignes.length > 0 && (
          <Card className="print:hidden">
            <CardHeader className="py-3 px-4">
              <CardTitle className="text-sm">Articles à coliser</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-white/70">
                    <th className="text-left px-4 py-2 font-medium">Produit</th>
                    <th className="text-right px-4 py-2 font-medium">Qté</th>
                    <th className="text-right px-4 py-2 font-medium">Cond./carton</th>
                    <th className="text-right px-4 py-2 font-medium">Nb cartons</th>
                  </tr>
                </thead>
                <tbody>
                  {ordre.lignes.map((ligne, i) => (
                    <tr key={i} className="border-b hover:bg-gray-50 dark:bg-white/5">
                      <td className="px-4 py-2">{ligne.produit_nom || ligne.produit_id}</td>
                      <td className="px-4 py-2 text-right">{ligne.quantite}</td>
                      <td className="px-4 py-2 text-right text-gray-500 dark:text-white/50">{ligne.conditionnement_carton ?? "—"}</td>
                      <td className="px-4 py-2 text-right font-medium">
                        {ligne.conditionnement_carton
                          ? Math.ceil(ligne.quantite / ligne.conditionnement_carton)
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        )}

        {/* Cartons */}
        <Card>
          <CardHeader className="py-3 px-4 border-b">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm flex items-center gap-2">
                <Box className="w-4 h-4" /> Cartons ({cartons.length})
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {cartons.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-24 text-gray-400 text-sm print:hidden">
                <Box className="w-6 h-6 mb-1" />
                Aucun carton — utilisez "Générer cartons" pour les créer automatiquement
              </div>
            ) : (
              <div className="divide-y">
                {cartons.map((carton) => (
                  <div key={carton._id || carton.carton_id}>
                    {/* Étiquette imprimable (masquée en screen, visible au print) */}
                    <div className="hidden print:block m-2">
                      <EtiquetteCarton carton={carton} />
                    </div>
                    {/* Vue liste normale */}
                    <div className="flex items-center px-4 py-3 hover:bg-gray-50 dark:bg-white/5 print:hidden">
                      <button
                        className="mr-2 text-gray-400"
                        onClick={() => setExpandedCarton(expandedCarton === carton._id ? null : carton._id)}
                      >
                        {expandedCarton === carton._id
                          ? <ChevronDown className="w-4 h-4" />
                          : <ChevronRight className="w-4 h-4" />}
                      </button>
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <span className="font-mono text-xs font-medium text-orange-700">{carton.reference}</span>
                          <StatutBadge statut={carton.statut} config={CARTON_STATUT} />
                          <span className="text-xs font-bold text-orange-700 bg-orange-100 dark:bg-orange-500/20 px-2 py-0.5 rounded">
                            Carton {carton.numero_carton}/{carton.total_cartons}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 dark:text-white/50 mt-0.5">
                          {carton.total_articles ?? "—"} articles
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm" variant="outline"
                          className="h-7 px-2 text-xs gap-1"
                          onClick={() => downloadCartonEtiquette(carton.carton_id || carton._id)}
                          title="Télécharger étiquette PDF"
                        >
                          <Printer className="w-3 h-3" /> PDF
                        </Button>
                        <Button
                          size="sm" variant="outline"
                          className="h-7 px-2 text-xs gap-1"
                          onClick={() => setShowEtiquette(carton)}
                          title="Voir QR Code"
                        >
                          <QrCode className="w-3 h-3" /> QR
                        </Button>
                        {carton.statut === "en_preparation" && (
                          <Button
                            size="sm" variant="outline"
                            className="h-7 px-2 text-xs gap-1 text-green-700 border-green-300"
                            onClick={() => validerMutation.mutate(carton._id || carton.carton_id)}
                          >
                            <CheckCircle className="w-3 h-3" /> Valider
                          </Button>
                        )}
                        {carton.statut === "en_preparation" && (
                          <Button
                            size="sm" variant="ghost"
                            className="h-7 px-2 text-xs text-red-600"
                            onClick={() => {
                              if (confirm("Supprimer ce carton ?"))
                                supprimerMutation.mutate(carton._id || carton.carton_id);
                            }}
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        )}
                      </div>
                    </div>
                    {/* Détail carton étendu */}
                    {expandedCarton === carton._id && carton.contenu && (
                      <div className="px-10 pb-3 print:hidden">
                        <table className="w-full text-xs bg-gray-50 dark:bg-white/5 rounded">
                          <thead>
                            <tr className="border-b text-gray-500 dark:text-white/50">
                              <th className="text-left px-3 py-1.5">Produit</th>
                              <th className="text-right px-3 py-1.5">Qté</th>
                            </tr>
                          </thead>
                          <tbody>
                            {carton.contenu.map((item, i) => (
                              <tr key={i} className="border-b last:border-0">
                                <td className="px-3 py-1.5">{item.produit_nom || item.produit_id}</td>
                                <td className="px-3 py-1.5 text-right">{item.quantite}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Notes */}
        {ordre.notes && (
          <Card className="print:hidden">
            <CardContent className="p-4">
              <p className="text-xs text-gray-500 dark:text-white/50 mb-1">Notes</p>
              <p className="text-sm">{ordre.notes}</p>
            </CardContent>
          </Card>
        )}

        {/* Dialog générer cartons */}
        <Dialog open={showGenerer} onOpenChange={setShowGenerer}>
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle>Générer cartons automatiquement</DialogTitle>
              <DialogDescription>
                {suggestion
                  ? `Estimation: ${suggestion.nb_cartons_suggeres} cartons pour ${suggestion.total_articles} articles`
                  : "Calcul basé sur le conditionnement des produits"}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="forcer"
                  checked={genererConfig.forcer}
                  onChange={(e) => setGenererConfig({ ...genererConfig, forcer: e.target.checked })}
                />
                <Label htmlFor="forcer">Régénérer (supprimer cartons existants)</Label>
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setShowGenerer(false)}>Annuler</Button>
                <Button
                  onClick={() => genererMutation.mutate(genererConfig)}
                  disabled={genererMutation.isLoading}
                >
                  {genererMutation.isLoading ? "Génération..." : "Générer"}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Dialog étiquette */}
        <Dialog open={!!showEtiquette} onOpenChange={(open) => !open && setShowEtiquette(null)}>
          <DialogContent className="max-w-xs">
            <DialogHeader>
              <DialogTitle>Étiquette carton</DialogTitle>
            </DialogHeader>
            {showEtiquette && (
              <div className="flex flex-col items-center gap-4">
                {/* Image QR depuis le backend */}
                <img
                  src={getCartonQrCodeUrl(showEtiquette.carton_id)}
                  alt="QR Code"
                  className="w-40 h-40 border rounded-lg p-2"
                  onError={(e) => { e.target.style.display = "none"; }}
                />
                <div className="w-full text-sm space-y-1">
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-white/50">Référence</span>
                    <span className="font-medium">{showEtiquette.reference || showEtiquette.carton_id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-white/50">Carton</span>
                    <span className="font-medium">{showEtiquette.numero_carton} / {showEtiquette.total_cartons}</span>
                  </div>
                  {showEtiquette.designation && (
                    <div className="flex justify-between">
                      <span className="text-gray-500 dark:text-white/50">Article</span>
                      <span className="font-medium text-right max-w-[60%]">{showEtiquette.designation}</span>
                    </div>
                  )}
                  {showEtiquette.quantite != null && (
                    <div className="flex justify-between">
                      <span className="text-gray-500 dark:text-white/50">Qté</span>
                      <span className="font-medium">{showEtiquette.quantite}{showEtiquette.est_partiel ? " (partiel)" : ""}</span>
                    </div>
                  )}
                </div>
                <p className="text-xs text-gray-400 text-center break-all">
                  {showEtiquette.qr_code || `https://erp.fabsci.ci/carton/${showEtiquette.carton_id}`}
                </p>
                <Button className="w-full gap-1" onClick={() => downloadCartonEtiquette(showEtiquette.carton_id)}>
                  <Printer className="w-4 h-4" /> Imprimer étiquette PDF
                </Button>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Dialog transition statut */}
        <Dialog open={showStatut} onOpenChange={setShowStatut}>
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle>Changer le statut</DialogTitle>
              <DialogDescription>Ordre: {ordre.reference}</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Nouveau statut</Label>
                <select
                  className="w-full border rounded-md px-3 py-2 text-sm mt-1"
                  value={newStatut}
                  onChange={(e) => setNewStatut(e.target.value)}
                >
                  {transitions.map((s) => (
                    <option key={s} value={s}>{STATUT_CONFIG[s]?.label || s}</option>
                  ))}
                </select>
              </div>
              <div>
                <Label>Notes</Label>
                <Textarea
                  value={statutNotes}
                  onChange={(e) => setStatutNotes(e.target.value)}
                  rows={2}
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setShowStatut(false)}>Annuler</Button>
                <Button
                  onClick={() => statutMutation.mutate({ statut: newStatut, notes: statutNotes || null })}
                  disabled={!newStatut || statutMutation.isLoading}
                >
                  Confirmer
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
