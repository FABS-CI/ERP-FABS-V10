/**
 * Page détail facture avec actions
 * Sprint 7
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, FileText, Send, DollarSign, ShieldCheck, Package, Plus, Eye, CheckCircle, XCircle } from 'lucide-react';
import { getFacture, emettreFacture, genererAvoir, generateFacturePDF, sendFactureWhatsApp, sendFactureEmail, certifierFNE } from '../services/facturesApi';
import { getColisByFacture, createColis, updateColisStatut } from '../services/colisageService';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Separator } from '../components/ui/separator';
import { Skeleton } from '../components/ui/skeleton';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { useAuth } from '../hooks/useAuth';
import DashboardLayout from '../components/layout/DashboardLayout';
import DocumentActionBar from '../components/document/DocumentActionBar';

const STATUT_CONFIG = {
  brouillon: { label: 'Brouillon', color: 'bg-gray-500' },
  emise: { label: 'Émise', color: 'bg-blue-500' },
  partiellement_payee: { label: 'Partiellement payée', color: 'bg-orange-500' },
  payee: { label: 'Payée', color: 'bg-green-500' },
  annulee: { label: 'Annulée', color: 'bg-red-500' },
};

const FNE_STATUS_CONFIG = {
  pending: { label: '⏳ En attente DGI', color: 'bg-orange-500' },
  certified: { label: '✅ Certifiée DGI', color: 'bg-green-500' },
  rejected: { label: '❌ Rejetée DGI', color: 'bg-red-500' },
  failed: { label: '🔴 Échec technique', color: 'bg-red-700' },
};

export default function FactureDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [facture, setFacture] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [showAvoirDialog, setShowAvoirDialog] = useState(false);
  const [avoirData, setAvoirData] = useState({ montant: '', motif: '' });
  const [colisageData, setColisageData] = useState(null);
  const [loadingColisage, setLoadingColisage] = useState(false);
  const [showColisageForm, setShowColisageForm] = useState(false);
  const [colisFormData, setColisFormData] = useState({ lignes: [], poids_total: 0, notes: '' });
  const [savingColis, setSavingColis] = useState(false);

  const fetchFacture = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getFacture(id);
      const factureData = {
        ...data,
        lignes: Array.isArray(data?.lignes) ? data.lignes : [],
      };
      setFacture(factureData);
      setAvoirData(prev => ({ ...prev, montant: data.montant_ttc }));
      if (['emise', 'partiellement_payee', 'payee'].includes(data.statut)) {
        fetchColisage(data.facture_id);
      }
    } catch (error) {
      toast.error('Erreur lors du chargement de la facture');
      navigate('/factures');
    } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    fetchFacture();
  }, [fetchFacture]);

  const fetchColisage = async (factureId) => {
    if (!factureId) return;
    setLoadingColisage(true);
    try {
      const data = await getColisByFacture(factureId);
      setColisageData(data);
    } catch {
      // Silencieux si module non dispo
    } finally {
      setLoadingColisage(false);
    }
  };

  const initColisForm = (data) => {
    const lignes = data.lignes
      .filter((l) => l.quantite_restante > 0)
      .map((l) => ({
        ligne_facture_id: l.ligne_id,
        produit_id: l.produit_id,
        designation: l.designation,
        quantite_facturee: l.quantite,
        quantite_restante: l.quantite_restante,
        quantite_colisee: l.quantite_restante,
        poids_unitaire: 0,
        poids_total: 0,
      }));
    setColisFormData({ lignes, poids_total: 0, notes: '' });
    setShowColisageForm(true);
  };

  const handleCreerColis = async () => {
    const lignesValides = colisFormData.lignes.filter((l) => l.quantite_colisee > 0);
    if (!lignesValides.length) { toast.error('Au moins une ligne requise'); return; }
    setSavingColis(true);
    try {
      await createColis({
        facture_id: facture.facture_id,
        lignes: lignesValides,
        poids_total: parseFloat(colisFormData.poids_total) || 0,
        notes: colisFormData.notes || null,
      });
      toast.success('Colis créé avec succès');
      setShowColisageForm(false);
      fetchColisage(facture.facture_id);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erreur création colis');
    } finally {
      setSavingColis(false);
    }
  };

  const handleValiderColis = async (colisId) => {
    try {
      await updateColisStatut(colisId, 'valide');
      toast.success('Colis validé');
      fetchColisage(facture.facture_id);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erreur validation');
    }
  };

  const handleEmettre = async () => {
    setActionLoading(true);
    try {
      const updated = await emettreFacture(id);
      // S'assurer que lignes est un tableau
      const factureData = {
        ...updated,
        lignes: Array.isArray(updated?.lignes) ? updated.lignes : [],
      };
      setFacture(factureData);
      toast.success('Facture émise avec succès');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors de l\'émission');
    } finally {
      setActionLoading(false);
    }
  };

  const handleGenererAvoir = async () => {
    if (!avoirData.montant || !avoirData.motif || avoirData?.motif?.length < 10) {
      toast.error('Veuillez remplir tous les champs (motif min 10 caractères)');
      return;
    }
    
    setActionLoading(true);
    try {
      await genererAvoir(id, parseFloat(avoirData.montant), avoirData.motif);
      toast.success('Avoir généré avec succès');
      setShowAvoirDialog(false);
      fetchFacture();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la génération de l\'avoir');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCertifierFNE = async () => {
    setActionLoading(true);
    try {
      const updated = await certifierFNE(id);
      const factureData = {
        ...updated,
        lignes: Array.isArray(updated?.lignes) ? updated.lignes : [],
      };
      setFacture(factureData);
      toast.success('Certification FNE envoyée avec succès');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors de l\'envoi de la certification FNE');
    } finally {
      setActionLoading(false);
    }
  };

  const handleGeneratePDF = async () => {
    return await generateFacturePDF(id);
  };

  const handleDownloadPDF = async () => {
    return await generateFacturePDF(id);
  };

  const handlePrintPDF = async () => {
    return await generateFacturePDF(id);
  };

  const handleSendWhatsApp = async (payload) => {
    return await sendFactureWhatsApp(id, payload);
  };

  const handleSendEmail = async (payload) => {
    return await sendFactureEmail(id, payload);
  };

  const canEmit = () => {
    return user && ['super_admin', 'directeur_general', 'directeur_commercial', 'comptable'].includes(user.role);
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

  if (!facture) return null;

  return (
    <DashboardLayout>
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            onClick={() => navigate('/factures')}
            data-testid="btn-retour"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Retour
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-[#0A2540] dark:text-white">
              {facture.reference}
            </h1>
            <div className="flex items-center gap-2 mt-2">
              <Badge className={`${STATUT_CONFIG[facture.statut].color} text-white`}>
                {STATUT_CONFIG[facture.statut].label}
              </Badge>
              {facture.type_facture === 'avoir' && (
                <Badge variant="outline" className="text-red-600 border-red-600">
                  Avoir
                </Badge>
              )}
              {facture.fne_status && FNE_STATUS_CONFIG[facture.fne_status] && (
                <Badge className={`${FNE_STATUS_CONFIG[facture.fne_status].color} text-white`}>
                  {FNE_STATUS_CONFIG[facture.fne_status].label}
                </Badge>
              )}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-2 items-center">
          <DocumentActionBar
            documentType="Facture"
            documentId={facture.facture_id}
            documentReference={facture.reference}
            clientNom={facture.client_nom}
            clientWhatsApp={facture.client_numero_whatsapp}
            clientEmail={facture.client_email}
            montant={facture.montant_ttc ? new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 }).format(facture.montant_ttc) + ' FCFA' : null}
            onGeneratePDF={handleGeneratePDF}
            onPrint={handlePrintPDF}
            onDownload={handleDownloadPDF}
            onSendWhatsApp={handleSendWhatsApp}
            onSendEmail={handleSendEmail}
          />
          {facture.statut === 'brouillon' && canEmit() && (
            <Button
              onClick={handleEmettre}
              disabled={actionLoading}
              className="bg-blue-600 hover:bg-blue-700"
              data-testid="btn-emettre"
            >
              <Send className="h-4 w-4 mr-2" />
              Émettre
            </Button>
          )}

          {facture.statut === 'emise' && facture.type_facture === 'facture' && canEmit() && (
            <Button
              onClick={handleCertifierFNE}
              disabled={actionLoading || facture.fne_status === 'pending' || facture.fne_status === 'certified'}
              className="bg-green-600 hover:bg-green-700"
              data-testid="btn-certifier-fne"
            >
              <ShieldCheck className="h-4 w-4 mr-2" />
              Certifier FNE
            </Button>
          )}

          {facture.type_facture === 'facture' && canEmit() && (
            <Button
              variant="outline"
              onClick={() => setShowAvoirDialog(true)}
              disabled={actionLoading}
              data-testid="btn-generer-avoir"
            >
              <FileText className="h-4 w-4 mr-2" />
              Générer avoir
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Info */}
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
                  <span className="font-medium">{facture.client_nom || '-'}</span>
                </div>
                <div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">Date facture:</span>{' '}
                  <span className="font-medium">{formatDate(facture.date_facture)}</span>
                </div>
                {facture.date_echeance && (
                  <div>
                    <span className="text-sm text-gray-600 dark:text-gray-400">Date échéance:</span>{' '}
                    <span className="font-medium">{formatDate(facture.date_echeance)}</span>
                  </div>
                )}
                {facture.commande_reference && (
                  <div>
                    <span className="text-sm text-gray-600 dark:text-gray-400">Commande:</span>{' '}
                    <span className="font-medium font-mono">{facture.commande_reference}</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Lignes */}
          <Card>
            <CardHeader>
              <CardTitle>Lignes de facture</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Array.isArray(facture?.lignes) && facture.lignes.map((ligne) => (
                  <div key={ligne.ligne_id} className="flex justify-between items-start border-b pb-3 last:border-0">
                    <div className="flex-1">
                      <div className="font-medium">{ligne.designation}</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        Qté: {ligne.quantite} × {formatCurrency(ligne.prix_unitaire)}
                      </div>
                      {ligne.remise_ligne > 0 && (
                        <Badge variant="outline" className="mt-1 text-orange-600">
                          Remise: -{ligne.remise_ligne}%
                        </Badge>
                      )}
                    </div>
                    <div className="font-semibold">
                      {formatCurrency(ligne.montant_ht)}
                    </div>
                  </div>
                ))}
              </div>

              <Separator className="my-4" />

              {/* Totals */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Sous-total HT:</span>
                  <span>{formatCurrency(facture.montant_ht + (facture.montant_ht * facture.remise_globale / 100))}</span>
                </div>
                {facture.remise_globale > 0 && (
                  <div className="flex justify-between text-sm text-orange-600">
                    <span>Remise globale ({facture.remise_globale}%):</span>
                    <span>-{formatCurrency(facture.montant_ht * facture.remise_globale / 100)}</span>
                  </div>
                )}
                <div className="flex justify-between text-sm">
                  <span>Montant HT:</span>
                  <span>{formatCurrency(facture.montant_ht)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>TVA (18%):</span>
                  <span>{formatCurrency(facture.montant_tva)}</span>
                </div>
                <Separator />
                <div className="flex justify-between text-lg font-bold">
                  <span>Total TTC:</span>
                  <span className="text-[#FF6200]">{formatCurrency(facture.montant_ttc)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Montant réglé:</span>
                  <span className="text-green-600 font-semibold">{formatCurrency(facture.montant_regle)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Restant dû:</span>
                  <span className="text-orange-600 font-semibold">{formatCurrency(facture.montant_restant)}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Notes */}
          {facture.notes && (
            <Card>
              <CardHeader>
                <CardTitle>Notes</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{facture.notes}</p>
              </CardContent>
            </Card>
          )}

          {/* ─── SECTION COLISAGE ─── */}
          {['emise', 'partiellement_payee', 'payee'].includes(facture.statut) && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <Package className="h-5 w-5 text-[#F97316]" />
                    Colisage
                    {colisageData && (
                      <span className="text-sm font-normal text-gray-500 ml-2">
                        {colisageData.nb_colis} colis · {colisageData.nb_colis_valides} validé(s)
                      </span>
                    )}
                  </CardTitle>
                  <div className="flex gap-2">
                    {['super_admin', 'admin', 'gestionnaire', 'preparateur'].includes(user?.role) &&
                      colisageData && !colisageData.colisage_complet && (
                      <Button
                        size="sm"
                        className="bg-[#0A2540] hover:bg-[#0A2540]/90"
                        onClick={() => initColisForm(colisageData)}
                        disabled={loadingColisage}
                      >
                        <Plus className="h-4 w-4 mr-1" />
                        Créer un colis
                      </Button>
                    )}
                    <Button
                      size="sm" variant="outline"
                      onClick={() => fetchColisage(facture.facture_id)}
                      disabled={loadingColisage}
                    >
                      {loadingColisage ? '...' : 'Rafraîchir'}
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {loadingColisage && <p className="text-sm text-gray-400">Chargement...</p>}

                {colisageData && (
                  <div className="space-y-4">
                    {/* Résumé quantités par ligne */}
                    <div>
                      <div className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Avancement du colisage</div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-xs text-gray-500 border-b">
                              <th className="text-left pb-1">Produit</th>
                              <th className="text-center pb-1">Facturé</th>
                              <th className="text-center pb-1">Colisé</th>
                              <th className="text-center pb-1">Restant</th>
                              <th className="text-center pb-1">État</th>
                            </tr>
                          </thead>
                          <tbody>
                            {colisageData.lignes.map((lg) => (
                              <tr key={lg.ligne_id} className="border-b last:border-0">
                                <td className="py-1.5 pr-3 font-medium">{lg.designation}</td>
                                <td className="text-center py-1.5">{lg.quantite}</td>
                                <td className="text-center py-1.5 font-semibold text-[#0A2540] dark:text-white">{lg.quantite_colisee}</td>
                                <td className="text-center py-1.5">
                                  <span className={lg.quantite_restante === 0 ? 'text-green-600' : 'text-orange-500'}>
                                    {lg.quantite_restante}
                                  </span>
                                </td>
                                <td className="text-center py-1.5">
                                  {lg.quantite_restante === 0
                                    ? <span className="text-xs text-green-600 font-medium">✓ Complet</span>
                                    : <span className="text-xs text-orange-500">En cours</span>}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Liste des colis */}
                    {colisageData.colis.length > 0 && (
                      <div>
                        <Separator className="my-3" />
                        <div className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Colis créés</div>
                        <div className="space-y-2">
                          {colisageData.colis.map((c) => (
                            <div
                              key={c.colis_id}
                              className="flex items-center justify-between p-3 border rounded-lg bg-gray-50 dark:bg-[#040f1a]/30"
                            >
                              <div className="flex items-center gap-3">
                                <Package className="h-4 w-4 text-gray-400" />
                                <div>
                                  <div className="font-mono text-sm font-medium">{c.reference}</div>
                                  <div className="text-xs text-gray-500">
                                    {c.lignes?.length || 0} ligne(s) · {c.poids_total} kg
                                  </div>
                                </div>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold text-white ${
                                  c.statut === 'valide' ? 'bg-green-600' :
                                  c.statut === 'expedie' ? 'bg-blue-600' :
                                  c.statut === 'annule' ? 'bg-red-600' : 'bg-gray-500'
                                }`}>
                                  {c.statut === 'en_preparation' ? 'En préparation' :
                                   c.statut === 'valide' ? 'Validé' :
                                   c.statut === 'expedie' ? 'Expédié' : 'Annulé'}
                                </span>
                                {['super_admin', 'admin', 'gestionnaire'].includes(user?.role) &&
                                  c.statut === 'en_preparation' && (
                                  <Button
                                    size="sm" variant="outline"
                                    className="text-green-600 border-green-300 hover:bg-green-50 text-xs h-7"
                                    onClick={() => handleValiderColis(c.colis_id)}
                                  >
                                    <CheckCircle className="h-3 w-3 mr-1" />
                                    Valider
                                  </Button>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {colisageData.colis.length === 0 && (
                      <div className="text-center py-4 text-gray-400 text-sm">
                        Aucun colis créé pour cette facture.
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Résumé</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Type</div>
                <div className="font-semibold">{facture.type_facture === 'facture' ? 'Facture' : 'Avoir'}</div>
              </div>
              <Separator />
              <div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Statut</div>
                <div className="font-semibold">{STATUT_CONFIG[facture.statut].label}</div>
              </div>
              <Separator />
              <div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Date émission</div>
                <div className="font-semibold">{formatDate(facture.date_emission)}</div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Dialog Générer Avoir */}
      <Dialog open={showAvoirDialog} onOpenChange={setShowAvoirDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Générer un avoir</DialogTitle>
            <DialogDescription>
              Créer un avoir (note de crédit) pour cette facture
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="montant-avoir">Montant de l'avoir (FCFA)</Label>
              <Input
                id="montant-avoir"
                type="number"
                min="0"
                max={facture.montant_ttc}
                value={avoirData.montant}
                onChange={(e) => setAvoirData(prev => ({ ...prev, montant: e.target.value }))}
                data-testid="input-montant-avoir"
              />
              <p className="text-sm text-gray-500 mt-1">Maximum: {formatCurrency(facture.montant_ttc)}</p>
            </div>
            <div>
              <Label htmlFor="motif-avoir">Motif (minimum 10 caractères)</Label>
              <Textarea
                id="motif-avoir"
                placeholder="Raison de l'avoir..."
                rows={4}
                value={avoirData.motif}
                onChange={(e) => setAvoirData(prev => ({ ...prev, motif: e.target.value }))}
                data-testid="textarea-motif-avoir"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAvoirDialog(false)}>
              Annuler
            </Button>
            <Button
              onClick={handleGenererAvoir}
              disabled={actionLoading || !avoirData.montant || avoirData.motif.length < 10}
              className="bg-[#FF6200] hover:bg-[#E55900]"
              data-testid="btn-confirm-avoir"
            >
              Générer l'avoir
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>

      {/* Dialog Création Colis depuis FactureDetail */}
      <Dialog open={showColisageForm} onOpenChange={setShowColisageForm}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Créer un colis — {facture?.reference}</DialogTitle>
            <DialogDescription>
              Saisir les quantités à coliser pour cette facture
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {colisFormData.lignes.length === 0 && (
              <div className="text-center py-4 text-amber-600 text-sm bg-amber-50 dark:bg-amber-900/20 rounded p-3">
                Toutes les quantités ont déjà été colisées pour cette facture.
              </div>
            )}
            {colisFormData.lignes.length > 0 && (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-gray-500 border-b">
                    <th className="text-left pb-2">Produit</th>
                    <th className="text-center pb-2">Restant</th>
                    <th className="text-center pb-2 w-24">Qté à coliser</th>
                    <th className="text-center pb-2 w-24">Poids/u (kg)</th>
                  </tr>
                </thead>
                <tbody>
                  {colisFormData.lignes.map((lg, idx) => (
                    <tr key={lg.ligne_facture_id} className="border-b last:border-0">
                      <td className="py-2 pr-3">
                        <div className="font-medium">{lg.designation}</div>
                        <div className="text-xs text-gray-400">{lg.produit_id}</div>
                      </td>
                      <td className="text-center py-2">{lg.quantite_restante}</td>
                      <td className="py-2 px-2">
                        <Input
                          type="number" min={0} max={lg.quantite_restante}
                          value={lg.quantite_colisee}
                          onChange={(e) => {
                            const val = Math.min(parseInt(e.target.value) || 0, lg.quantite_restante);
                            setColisFormData((prev) => {
                              const ls = [...prev.lignes];
                              ls[idx] = { ...ls[idx], quantite_colisee: val };
                              return { ...prev, lignes: ls };
                            });
                          }}
                          className="w-20 text-center"
                        />
                      </td>
                      <td className="py-2 px-2">
                        <Input
                          type="number" min={0} step={0.1}
                          value={lg.poids_unitaire}
                          onChange={(e) => {
                            const pu = parseFloat(e.target.value) || 0;
                            setColisFormData((prev) => {
                              const ls = [...prev.lignes];
                              ls[idx] = { ...ls[idx], poids_unitaire: pu, poids_total: pu * ls[idx].quantite_colisee };
                              return { ...prev, lignes: ls };
                            });
                          }}
                          className="w-20 text-center"
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Poids total (kg)</Label>
                <Input
                  type="number" min={0} step={0.1}
                  value={colisFormData.poids_total}
                  onChange={(e) => setColisFormData((p) => ({ ...p, poids_total: e.target.value }))}
                />
              </div>
            </div>
            <div>
              <Label>Notes (optionnel)</Label>
              <Textarea
                rows={2} placeholder="Instructions..."
                value={colisFormData.notes}
                onChange={(e) => setColisFormData((p) => ({ ...p, notes: e.target.value }))}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowColisageForm(false)}>Annuler</Button>
            <Button
              onClick={handleCreerColis}
              disabled={savingColis || colisFormData.lignes.filter(l => l.quantite_colisee > 0).length === 0}
              className="bg-[#0A2540] hover:bg-[#0A2540]/90"
            >
              {savingColis ? 'Création...' : 'Créer le colis'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
}
