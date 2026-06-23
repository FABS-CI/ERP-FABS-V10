/**
 * Page détail commande avec timeline et actions
 * Sprint 6
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, XCircle, Package, Truck, FileText, AlertCircle, Receipt, Trash2, Pencil } from 'lucide-react';
import {
  getCommande,
  validerCommande,
  preparerCommande,
  livrerCommande,
  annulerCommande,
  generateCommandePDF,
  sendCommandeWhatsApp,
  sendCommandeEmail,
  deleteCommande,
} from '../services/commandesApi';
import { generateFactureFromCommande } from '../services/facturesApi';
import { livrerBon } from '../services/bonsLivraisonApi';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Separator } from '../components/ui/separator';
import { Skeleton } from '../components/ui/skeleton';
import LignesTable from '../components/document/LignesTable';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../components/ui/alert-dialog';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import { useAuth } from '../hooks/useAuth';
import { can } from '../constants/permissions';
import DashboardLayout from '../components/layout/DashboardLayout';
import PageHeader from "../components/PageHeader";
import DocumentActionBar from '../components/document/DocumentActionBar';

const STATUT_CONFIG = {
  brouillon: { label: 'Brouillon', color: 'bg-gray-500', icon: FileText },
  en_attente: { label: 'En attente', color: 'bg-yellow-500', icon: AlertCircle },
  validee: { label: 'Validée', color: 'bg-blue-500', icon: CheckCircle },
  preparee: { label: 'Préparée', color: 'bg-purple-500', icon: Package },
  livree: { label: 'Livrée', color: 'bg-green-500', icon: Truck },
  annulee: { label: 'Annulée', color: 'bg-red-500', icon: XCircle },
};

export default function CommandeDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [commande, setCommande] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [cancelMotif, setCancelMotif] = useState('');

  useEffect(() => {
    fetchCommande();
  }, [id]);

  const fetchCommande = async ({ silent = false } = {}) => {
    if (!silent) setLoading(true);
    try {
      const data = await getCommande(id);
      // S'assurer que les propriétés essentielles sont des tableaux
      const commandeData = {
        ...data,
        lignes: Array.isArray(data?.lignes) ? data.lignes : [],
        historique: Array.isArray(data?.historique) ? data.historique : [],
      };
      setCommande(commandeData);
    } catch (error) {
      if (!silent) {
        toast.error('Erreur lors du chargement de la commande');
        navigate('/commandes');
      }
    } finally {
      if (!silent) setLoading(false);
    }
  };

  const handleAction = async (action, actionFn) => {
    setActionLoading(true);
    try {
      await actionFn(id);
      // Les endpoints d'action (valider/preparer/livrer) renvoient une commande SANS
      // les lignes. On recharge donc la commande complète pour garder lignes + statut.
      await fetchCommande({ silent: true });
      toast.success(`Commande ${action} avec succès`);
    } catch (error) {
      toast.error(error.response?.data?.detail || `Erreur lors de l'action: ${action}`);
    } finally {
      setActionLoading(false);
    }
  };

  // Livraison : si un (des) bon(s) de livraison existe(nt), on livre via le BL
  // (déduction de stock garantie). Sinon, fallback sur l'action commande directe.
  const handleLivrer = async () => {
    setActionLoading(true);
    try {
      const bls = commande?.transformations?.bons_livraison || [];
      const aLivrer = bls.filter((bl) => bl.statut !== 'livre');
      if (aLivrer.length > 0) {
        for (const bl of aLivrer) {
          await livrerBon(bl.bl_id);
        }
      } else {
        await livrerCommande(id);
      }
      await fetchCommande({ silent: true });
      toast.success('Commande livrée avec succès');
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur lors de la livraison");
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!cancelMotif || cancelMotif?.length < 10) {
      toast.error('Veuillez fournir un motif d\'au moins 10 caractères');
      return;
    }
    setActionLoading(true);
    try {
      await annulerCommande(id, cancelMotif);
      await fetchCommande({ silent: true });
      toast.success('Commande annulée');
      setShowCancelDialog(false);
      setCancelMotif('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors de l\'annulation');
    } finally {
      setActionLoading(false);
    }
  };

  const handleGeneratePDF = async () => {
    return await generateCommandePDF(id);
  };

  const handleDownloadPDF = async () => {
    return await generateCommandePDF(id);
  };

  const handlePrintPDF = async () => {
    return await generateCommandePDF(id);
  };

  const handleSendWhatsApp = async (payload) => {
    return await sendCommandeWhatsApp(id, payload);
  };

  const handleSendEmail = async (payload) => {
    return await sendCommandeEmail(id, payload);
  };

  // 🆕 Générer une facture depuis cette commande (Workflow V10)
  const handleGenerateFacture = async () => {
    if (!window.confirm("Générer une facture définitive depuis cette commande ?")) return;
    setActionLoading(true);
    try {
      const result = await generateFactureFromCommande(id);
      toast.success(`Facture ${result.reference || ""} générée avec succès`);
      navigate(`/factures/${result.facture_id}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur lors de la génération de la facture");
    } finally {
      setActionLoading(false);
    }
  };

  // assistante : lecture + création/modif brouillon uniquement — pas de validation ni annulation ni facture
  const isAssistanteCommerciale = () => user?.role === 'assistante';

  const canGenerateFacture = () => {
    if (!user || !commande) return false;
    if (!['validee', 'preparee', 'livree'].includes(commande.statut)) return false;
    // Anti-doublon : si une facture existe déjà, on n'autorise plus la génération
    if (commande.transformations?.facture_generee) return false;
    return ['super_admin', 'directeur_general', 'directeur_commercial', 'comptable'].includes(user.role);
  };

  const canValidate = () => {
    if (!user || !commande) return false;
    if (commande.montant_total > 500000) {
      return user.role === 'super_admin' || user.role === 'directeur_general';
    }
    return ['super_admin', 'directeur_general', 'directeur_commercial', 'secretariat', 'comptable'].includes(user.role);
  };

  const canPrepare = () => {
    return user && ['super_admin', 'directeur_general', 'responsable_magasinier'].includes(user.role);
  };

  const canDeliver = () => {
    return user && ['super_admin', 'directeur_general', 'service_logistique'].includes(user.role);
  };

  const canCancelOrder = () => {
    return user && ['super_admin', 'directeur_general', 'directeur_commercial', 'secretariat'].includes(user.role);
  };

  const handleDelete = async () => {
    if (!window.confirm(`Supprimer définitivement la commande ${commande.reference} ?\n\nTous les documents associés (proformas, BL, factures) seront également supprimés. Cette action est irréversible.`)) return;
    setActionLoading(true);
    try {
      await deleteCommande(id);
      toast.success(`Commande ${commande.reference} supprimée`);
      navigate('/commandes');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la suppression');
      setActionLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('fr-FR', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount) + ' FCFA';
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('fr-FR');
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <Skeleton className="h-12 w-64" />
          <Skeleton className="h-64 w-full" />
        </div>
      </DashboardLayout>
    );
  }

  if (!commande) return null;

  const StatusIcon = STATUT_CONFIG[commande.statut].icon;

  return (
    <DashboardLayout>
    <div className="space-y-6">
      <PageHeader
        title={commande.reference}
        subtitle={`Détail — ${STATUT_CONFIG[commande.statut].label}`}
        pagePath="/commandes"
        actions={
          <div className="flex flex-wrap gap-2">
          <DocumentActionBar
            documentType="Bon de Commande"
            documentId={commande.commande_id}
            documentReference={commande.reference}
            clientWhatsApp={commande.client_numero_whatsapp}
            clientEmail={commande.client_email}
            clientNom={commande.client_nom}
            montant={commande.montant_total ? `${Number(commande.montant_total).toLocaleString('fr-FR')} FCFA` : ''}
            onGeneratePDF={handleGeneratePDF}
            onPrint={handlePrintPDF}
            onDownload={handleDownloadPDF}
            onSendWhatsApp={handleSendWhatsApp}
            onSendEmail={handleSendEmail}
          />
          {commande.statut === 'brouillon' && (
            <Button
              variant="outline"
              onClick={() => navigate(`/commandes/${id}/modifier`)}
              disabled={actionLoading}
              data-testid="btn-modifier"
            >
              <Pencil className="h-4 w-4 mr-2" />
              Modifier
            </Button>
          )}

          {commande.statut === 'en_attente' && canValidate() && (
            <Button
              onClick={() => handleAction('validée', validerCommande)}
              disabled={actionLoading}
              className="bg-blue-600 hover:bg-blue-700"
              data-testid="btn-valider"
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Valider
            </Button>
          )}

          {commande.statut === 'validee' && canPrepare() && (
            <Button
              onClick={() => handleAction('préparée', preparerCommande)}
              disabled={actionLoading}
              className="bg-purple-600 hover:bg-purple-700"
              data-testid="btn-preparer"
            >
              <Package className="h-4 w-4 mr-2" />
              Marquer préparée
            </Button>
          )}

          {commande.statut === 'preparee' && canDeliver() && (
            <Button
              onClick={handleLivrer}
              disabled={actionLoading}
              className="bg-green-600 hover:bg-green-700"
              data-testid="btn-livrer"
            >
              <Truck className="h-4 w-4 mr-2" />
              Marquer livrée
            </Button>
          )}

          {/* 🆕 Workflow V10 : Commande → Facture définitive */}
          {canGenerateFacture() && (
            <Button
              onClick={handleGenerateFacture}
              disabled={actionLoading}
              className="bg-blue-600 hover:bg-blue-700 text-white"
              data-testid="btn-generer-facture"
            >
              <Receipt className="h-4 w-4 mr-2" />
              Générer Facture
            </Button>
          )}

          {/* Anti-doublon : facture déjà générée -> badge cliquable, plus de bouton */}
          {commande.transformations?.facture_generee && (
            <button
              type="button"
              onClick={() => navigate(`/factures/${commande.transformations.facture.facture_id}`)}
              className="inline-flex items-center gap-2 rounded-md border border-green-600 bg-green-50 px-3 py-2 text-sm font-medium text-green-700 hover:bg-green-100"
              data-testid="badge-facture-generee"
            >
              <CheckCircle className="h-4 w-4" />
              Facture générée : {commande.transformations.facture.reference}
            </button>
          )}

          {!['livree', 'annulee'].includes(commande.statut) && canCancelOrder() && (
            <Button
              variant="outline"
              onClick={() => setShowCancelDialog(true)}
              disabled={actionLoading}
              className="text-red-600 border-red-600 hover:bg-red-50"
              data-testid="btn-annuler"
            >
              <XCircle className="h-4 w-4 mr-2" />
              Annuler
            </Button>
          )}

          {user?.role === 'super_admin' && (
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={actionLoading}
              data-testid="btn-supprimer"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Supprimer
            </Button>
          )}
        </div>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Main Info */}
        <div className="lg:col-span-2 space-y-6">
          {/* Client Info */}
          <Card>
            <CardHeader>
              <CardTitle>Informations client</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">Nom:</span>{' '}
                  <span className="font-medium">{commande.client_nom || '-'}</span>
                </div>
                <div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">Date commande:</span>{' '}
                  <span className="font-medium">{formatDate(commande.date_commande)}</span>
                </div>
                {commande.date_livraison_prevue && (
                  <div>
                    <span className="text-sm text-gray-600 dark:text-gray-400">Livraison prévue:</span>{' '}
                    <span className="font-medium">{formatDate(commande.date_livraison_prevue)}</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Lignes */}
          <Card>
            <CardHeader>
              <CardTitle>Lignes de commande</CardTitle>
              <CardDescription>{commande?.lignes?.length || 0} produit(s)</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <LignesTable lignes={commande?.lignes || []} showPrix={true} />
              </div>

              <Separator className="my-4" />

              {/* Totals */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Sous-total HT:</span>
                  <span>{formatCurrency(commande.montant_ht)}</span>
                </div>
                {commande.remise_globale > 0 && (
                  <div className="flex justify-between text-sm text-orange-600">
                    <span>Remise globale ({commande.remise_globale}%):</span>
                    <span>-{formatCurrency(commande.montant_remise)}</span>
                  </div>
                )}
                <Separator />
                <div className="flex justify-between text-lg font-bold">
                  <span>Total:</span>
                  <span className="text-[#FF6200]">{formatCurrency(commande.montant_total)}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Notes */}
          {commande.notes && (
            <Card>
              <CardHeader>
                <CardTitle>Notes</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{commande.notes}</p>
              </CardContent>
            </Card>
          )}

          {/* Cancel Reason */}
          {commande.motif_annulation && (
            <Card className="border-red-200 dark:border-red-800">
              <CardHeader>
                <CardTitle className="text-red-600">Motif d'annulation</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700 dark:text-gray-300">{commande.motif_annulation}</p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Column - Timeline */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Timeline</CardTitle>
              <CardDescription>Historique des statuts</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Created */}
                <div className="flex gap-3">
                  <div className="flex flex-col items-center">
                    <div className="w-8 h-8 rounded-full bg-gray-500 flex items-center justify-center">
                      <FileText className="h-4 w-4 text-white" />
                    </div>
                    <div className="w-0.5 h-full bg-gray-300 dark:bg-gray-600 mt-2" />
                  </div>
                  <div className="flex-1 pb-4">
                    <div className="font-medium">Créée</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      {formatDate(commande.date_commande)}
                    </div>
                  </div>
                </div>

                {/* En attente */}
                {(commande.statut !== 'brouillon') && (
                  <div className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className="w-8 h-8 rounded-full bg-yellow-500 flex items-center justify-center">
                        <AlertCircle className="h-4 w-4 text-white" />
                      </div>
                      {(commande.date_validation || commande.statut === 'en_attente') && (
                        <div className="w-0.5 h-full bg-gray-300 dark:bg-gray-600 mt-2" />
                      )}
                    </div>
                    <div className="flex-1 pb-4">
                      <div className="font-medium">En attente validation</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        {formatDate(commande.date_commande)}
                      </div>
                    </div>
                  </div>
                )}

                {/* Validée */}
                {commande.date_validation && (
                  <div className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
                        <CheckCircle className="h-4 w-4 text-white" />
                      </div>
                      {(commande.date_preparation || ['validee', 'preparee', 'livree'].includes(commande.statut)) && (
                        <div className="w-0.5 h-full bg-gray-300 dark:bg-gray-600 mt-2" />
                      )}
                    </div>
                    <div className="flex-1 pb-4">
                      <div className="font-medium">Validée</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        {formatDate(commande.date_validation)}
                      </div>
                    </div>
                  </div>
                )}

                {/* Préparée */}
                {commande.date_preparation && (
                  <div className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className="w-8 h-8 rounded-full bg-purple-500 flex items-center justify-center">
                        <Package className="h-4 w-4 text-white" />
                      </div>
                      {(commande.date_livraison || ['preparee', 'livree'].includes(commande.statut)) && (
                        <div className="w-0.5 h-full bg-gray-300 dark:bg-gray-600 mt-2" />
                      )}
                    </div>
                    <div className="flex-1 pb-4">
                      <div className="font-medium">Préparée</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        {formatDate(commande.date_preparation)}
                      </div>
                    </div>
                  </div>
                )}

                {/* Livrée */}
                {commande.date_livraison && (
                  <div className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center">
                        <Truck className="h-4 w-4 text-white" />
                      </div>
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">Livrée</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        {formatDate(commande.date_livraison)}
                      </div>
                    </div>
                  </div>
                )}

                {/* Annulée */}
                {commande.statut === 'annulee' && (
                  <div className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className="w-8 h-8 rounded-full bg-red-500 flex items-center justify-center">
                        <XCircle className="h-4 w-4 text-white" />
                      </div>
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">Annulée</div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* État des transformations (anti-doublon) */}
          {commande.transformations && (
            <Card>
              <CardHeader>
                <CardTitle>État des transformations</CardTitle>
                <CardDescription>Documents déjà générés depuis cette commande</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {/* Facture */}
                  {commande.transformations.facture_generee ? (
                    <button
                      type="button"
                      onClick={() => navigate(`/factures/${commande.transformations.facture.facture_id}`)}
                      className="w-full flex items-center gap-2 rounded-md border border-green-600 bg-green-50 px-3 py-2 text-sm font-medium text-green-700 hover:bg-green-100 text-left"
                    >
                      <CheckCircle className="h-4 w-4 shrink-0" />
                      Facture générée : {commande.transformations.facture.reference}
                    </button>
                  ) : (
                    <div className="flex items-center gap-2 rounded-md border border-dashed border-gray-300 dark:border-white/10 px-3 py-2 text-sm text-gray-500 dark:text-white/50">
                      <Receipt className="h-4 w-4 shrink-0" />
                      Aucune facture générée
                    </div>
                  )}

                  {/* Bons de livraison */}
                  {commande.transformations.bl_genere ? (
                    commande.transformations.bons_livraison.map((bl) => (
                      <div
                        key={bl.bl_id}
                        className="flex items-center gap-2 rounded-md border border-green-600 bg-green-50 px-3 py-2 text-sm font-medium text-green-700"
                      >
                        <CheckCircle className="h-4 w-4 shrink-0" />
                        Bon de livraison : {bl.reference}
                        <span className="ml-auto text-xs font-normal text-green-600">
                          {bl.statut === 'livre' ? 'livré' : bl.statut}
                        </span>
                      </div>
                    ))
                  ) : (
                    <div className="flex items-center gap-2 rounded-md border border-dashed border-gray-300 dark:border-white/10 px-3 py-2 text-sm text-gray-500 dark:text-white/50">
                      <Truck className="h-4 w-4 shrink-0" />
                      Aucun bon de livraison généré
                    </div>
                  )}

                  {commande.transformations.totalement_livree && (
                    <div className="flex items-center gap-2 rounded-md border border-green-600 bg-green-50 px-3 py-2 text-sm font-medium text-green-700">
                      <CheckCircle className="h-4 w-4 shrink-0" />
                      Commande totalement livrée
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Cancel Dialog */}
      <AlertDialog open={showCancelDialog} onOpenChange={setShowCancelDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Annuler la commande</AlertDialogTitle>
            <AlertDialogDescription>
              Veuillez fournir un motif d'annulation (minimum 10 caractères).
            </AlertDialogDescription>
          </AlertDialogHeader>
          <Textarea
            placeholder="Motif d'annulation..."
            value={cancelMotif}
            onChange={(e) => setCancelMotif(e.target.value)}
            rows={4}
            data-testid="textarea-motif-annulation"
          />
          <AlertDialogFooter>
            <AlertDialogCancel>Annuler</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleCancel}
              disabled={actionLoading || cancelMotif.length < 10}
              className="bg-red-600 hover:bg-red-700"
              data-testid="btn-confirm-annulation"
            >
              Confirmer l'annulation
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
    </DashboardLayout>
  );
}
