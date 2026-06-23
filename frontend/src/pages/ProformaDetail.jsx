/**
 * Page Détail Proforma - Visualisation et actions
 * ERP FABS-CI
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, FileText, RefreshCw, Eye, 
  CheckCircle, XCircle, Clock, AlertCircle
} from 'lucide-react';
import { 
  getProforma, 
  generateProformaPDF, 
  sendProformaWhatsApp, 
  sendProformaEmail,
  convertProformaToInvoice 
} from '../services/proformasApi';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Skeleton } from '../components/ui/skeleton';
import { toast } from 'sonner';
import { useAuth } from '../hooks/useAuth';
import DashboardLayout from '../components/layout/DashboardLayout';
import PageHeader from "../components/PageHeader";
import DocumentActionBar from '../components/document/DocumentActionBar';

const STATUT_CONFIG = {
  brouillon: { label: 'Brouillon', color: 'bg-gray-500', icon: Clock },
  generee: { label: 'Générée', color: 'bg-blue-500', icon: FileText },
  envoyee: { label: 'Envoyée', color: 'bg-green-500', icon: FileText },
  consultee: { label: 'Consultée', color: 'bg-purple-500', icon: Eye },
  acceptee: { label: 'Acceptée', color: 'bg-emerald-500', icon: CheckCircle },
  refusee: { label: 'Refusée', color: 'bg-red-500', icon: XCircle },
  expiree: { label: 'Expirée', color: 'bg-orange-500', icon: AlertCircle },
  convertie_facture: { label: 'Convertie en Facture', color: 'bg-teal-500', icon: RefreshCw },
};

export default function ProformaDetail() {
  const { proformaId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [proforma, setProforma] = useState(null);
  const [loading, setLoading] = useState(true);
  const [convertLoading, setConvertLoading] = useState(false);

  useEffect(() => {
    fetchProforma();
  }, [proformaId]);

  const fetchProforma = async () => {
    try {
      setLoading(true);
      const data = await getProforma(proformaId);
      setProforma(data);
    } catch (error) {
      console.error('Erreur chargement proforma:', error);
      toast.error('Erreur lors du chargement de la proforma');
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePDF = async () => {
    return await generateProformaPDF(proformaId);
  };

  const handleDownloadPDF = async () => {
    return await generateProformaPDF(proformaId);
  };

  const handlePrintPDF = async () => {
    return await generateProformaPDF(proformaId);
  };

  const handleSendWhatsApp = async (payload) => {
    return await sendProformaWhatsApp(proformaId, payload);
  };

  const handleSendEmail = async (payload) => {
    return await sendProformaEmail(proformaId, payload);
  };

  const handleConvertToInvoice = async () => {
    if (!confirm('Êtes-vous sûr de vouloir convertir cette proforma en facture ?')) return;
    
    try {
      setConvertLoading(true);
      const result = await convertProformaToInvoice(proformaId);
      toast.success('Proforma convertie en facture avec succès');
      navigate(`/factures/${result.facture_id}`);
    } catch (error) {
      console.error('Erreur conversion facture:', error);
      toast.error('Erreur lors de la conversion en facture');
    } finally {
      setConvertLoading(false);
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

  const StatutIcon = STATUT_CONFIG[proforma?.statut_proforma]?.icon || Clock;

  if (loading) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <Skeleton className="h-8 w-8" />
            <Skeleton className="h-8 w-64" />
          </div>
          <Card>
            <CardContent className="pt-6">
              <Skeleton className="h-64 w-full" />
            </CardContent>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  if (!proforma) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <Button variant="ghost" onClick={() => navigate('/proformas')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Retour
          </Button>
          <Card>
            <CardContent className="pt-6 text-center py-12">
              <FileText className="h-12 w-12 mx-auto text-gray-400 mb-4" />
              <p className="text-gray-600 dark:text-gray-400">Proforma introuvable</p>
            </CardContent>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  const isAssistante = user?.role === 'assistante';
  const canConvert = proforma.statut_proforma !== 'convertie_facture' && !isAssistante;
  const alreadyConverted = proforma.statut_proforma === 'convertie_facture' && proforma.facture_id;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => navigate('/proformas')}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Retour
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-[#0A2540] dark:text-white">
                Proforma {proforma.numero_proforma}
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                {proforma.client_nom}
              </p>
            </div>
          </div>
          <Badge className={`${STATUT_CONFIG[proforma.statut_proforma].color} text-white`}>
            <StatutIcon className="h-4 w-4 mr-1" />
            {STATUT_CONFIG[proforma.statut_proforma].label}
          </Badge>
        </div>

        {/* Action Buttons */}
        <Card>
          <CardHeader>
            <CardTitle>Actions</CardTitle>
            <CardDescription>Générer et partager la proforma</CardDescription>
          </CardHeader>
          <CardContent>
            <DocumentActionBar
              documentType="Facture Proforma"
              documentId={proformaId}
              documentReference={proforma.numero_proforma}
              clientNom={proforma.client_nom}
              clientWhatsApp={proforma.client_numero_whatsapp}
              clientEmail={proforma.client_email}
              montant={proforma.montant_ttc ? new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 }).format(proforma.montant_ttc) + ' FCFA' : null}
              onGeneratePDF={handleGeneratePDF}
              onPrint={handlePrintPDF}
              onDownload={handleDownloadPDF}
              onSendWhatsApp={handleSendWhatsApp}
              onSendEmail={handleSendEmail}
            />
            {canConvert && (
              <div className="mt-4 pt-4 border-t">
                <Button
                  onClick={handleConvertToInvoice}
                  disabled={convertLoading}
                  className="bg-[#FF6200] hover:bg-[#E55900] text-white"
                  data-testid="btn-convertir-facture"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  {convertLoading ? "Conversion en cours..." : "Convertir en Facture"}
                </Button>
              </div>
            )}
            {alreadyConverted && (
              <div className="mt-4 pt-4 border-t">
                <Button
                  onClick={() => navigate(`/factures/${proforma.facture_id}`)}
                  className="bg-[#0A2540] hover:bg-[#0A2540]/90 text-white"
                  data-testid="btn-voir-facture"
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Voir la facture associée
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Proforma Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Informations Proforma</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Numéro</p>
                <p className="font-semibold">{proforma.numero_proforma}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Date émission</p>
                <p className="font-semibold">{formatDate(proforma.date_emission)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Date expiration</p>
                <p className="font-semibold">{formatDate(proforma.date_expiration)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Statut</p>
                <Badge className={`${STATUT_CONFIG[proforma.statut_proforma].color} text-white`}>
                  {STATUT_CONFIG[proforma.statut_proforma].label}
                </Badge>
              </div>
              {proforma.commande_reference && (
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Commande source</p>
                  <p className="font-semibold">{proforma.commande_reference}</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Montants</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Montant HT</p>
                <p className="font-semibold text-lg">{formatCurrency(proforma.montant_ht)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">TVA (18%)</p>
                <p className="font-semibold text-lg">{formatCurrency(proforma.montant_tva)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Remise globale</p>
                <p className="font-semibold text-lg">{proforma.remise_globale}%</p>
              </div>
              <div className="pt-4 border-t">
                <p className="text-sm text-gray-600 dark:text-gray-400">Montant TTC</p>
                <p className="font-bold text-2xl text-[#FF6200]">{formatCurrency(proforma.montant_ttc)}</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Client Info */}
        <Card>
          <CardHeader>
            <CardTitle>Informations Client</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Nom</p>
              <p className="font-semibold">{proforma.client_nom}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Téléphone</p>
              <p className="font-semibold">{proforma.client_telephone || '-'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">WhatsApp</p>
              <p className="font-semibold">{proforma.client_numero_whatsapp || '-'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Email</p>
              <p className="font-semibold">{proforma.client_email || '-'}</p>
            </div>
          </CardContent>
        </Card>

        {/* Tracking */}
        <Card>
          <CardHeader>
            <CardTitle>Historique des actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Générée le</p>
                <p className="font-semibold">{proforma.date_generation_proforma ? formatDate(proforma.date_generation_proforma) : '-'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Envoyée WhatsApp</p>
                <p className="font-semibold">{proforma.envoye_whatsapp ? formatDate(proforma.date_envoi_whatsapp) : 'Non'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Envoyée Email</p>
                <p className="font-semibold">{proforma.envoye_email ? formatDate(proforma.date_envoi_email) : 'Non'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Impressions</p>
                <p className="font-semibold">{proforma.nombre_impressions}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Téléchargements</p>
                <p className="font-semibold">{proforma.nombre_telechargements}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
