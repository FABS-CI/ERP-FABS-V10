/**
 * DocumentActionBar - Barre d'actions standard pour tous les documents commerciaux
 * ERP FABS-CI
 * 
 * Boutons standardisés :
 * - Aperçu PDF
 * - Imprimer
 * - Télécharger PDF
 * - Envoyer WhatsApp
 * - Envoyer Email
 */
import React, { useState } from 'react';
import { Eye, Printer, Download, MessageCircle, Mail } from 'lucide-react';
import { Button } from '../ui/button';
import { toast } from 'sonner';

export default function DocumentActionBar({
  documentType, // 'proforma', 'commande', 'facture', 'avoir', 'bl', 'recu'
  documentId,
  documentReference,
  clientWhatsApp,
  clientEmail,
  onGeneratePDF,
  onPrint,
  onDownload,
  onSendWhatsApp,
  onSendEmail,
  canPreview = true,
  canPrint = true,
  canDownload = true,
  canSendWhatsApp = true,
  canSendEmail = true,
}) {
  const [pdfLoading, setPdfLoading] = useState(false);
  const [whatsappLoading, setWhatsappLoading] = useState(false);
  const [emailLoading, setEmailLoading] = useState(false);
  const [showPdfPreview, setShowPdfPreview] = useState(false);
  const [pdfUrl, setPdfUrl] = useState(null);

  const handlePreview = async () => {
    try {
      setPdfLoading(true);
      const pdfBlob = await onGeneratePDF();
      const url = URL.createObjectURL(pdfBlob);
      setPdfUrl(url);
      setShowPdfPreview(true);
      toast.success('PDF généré avec succès');
    } catch (error) {
      console.error('Erreur génération PDF:', error);
      toast.error('Erreur lors de la génération du PDF');
    } finally {
      setPdfLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
      setPdfLoading(true);
      const pdfBlob = await onDownload();
      const url = URL.createObjectURL(pdfBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${documentType}_${documentReference}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('PDF téléchargé avec succès');
    } catch (error) {
      console.error('Erreur téléchargement PDF:', error);
      toast.error('Erreur lors du téléchargement du PDF');
    } finally {
      setPdfLoading(false);
    }
  };

  const handlePrint = async () => {
    try {
      setPdfLoading(true);
      const pdfBlob = await onPrint();
      const url = URL.createObjectURL(pdfBlob);
      const printWindow = window.open(url, '_blank');
      if (printWindow) {
        printWindow.onload = () => {
          printWindow.print();
        };
      }
      toast.success('Impression lancée');
    } catch (error) {
      console.error('Erreur impression PDF:', error);
      toast.error('Erreur lors de l\'impression du PDF');
    } finally {
      setPdfLoading(false);
    }
  };

  const handleSendWhatsApp = async () => {
    try {
      setWhatsappLoading(true);
      const result = await onSendWhatsApp();
      window.open(result.whatsapp_url, '_blank');
      toast.success('WhatsApp ouvert avec message prérempli');
    } catch (error) {
      console.error('Erreur envoi WhatsApp:', error);
      toast.error('Erreur lors de l\'ouverture de WhatsApp');
    } finally {
      setWhatsappLoading(false);
    }
  };

  const handleSendEmail = async () => {
    try {
      setEmailLoading(true);
      const result = await onSendEmail();
      toast.success(result.message || 'Email envoyé avec succès');
    } catch (error) {
      console.error('Erreur envoi Email:', error);
      toast.error('Erreur lors de l\'envoi de l\'email');
    } finally {
      setEmailLoading(false);
    }
  };

  return (
    <>
      <div className="flex flex-wrap gap-3">
        {canPreview && (
          <Button
            onClick={handlePreview}
            disabled={pdfLoading}
            variant="outline"
            size="sm"
          >
            <Eye className="h-4 w-4 mr-2" />
            Aperçu PDF
          </Button>
        )}
        {canPrint && (
          <Button
            onClick={handlePrint}
            disabled={pdfLoading}
            variant="outline"
            size="sm"
          >
            <Printer className="h-4 w-4 mr-2" />
            Imprimer
          </Button>
        )}
        {canDownload && (
          <Button
            onClick={handleDownload}
            disabled={pdfLoading}
            variant="outline"
            size="sm"
          >
            <Download className="h-4 w-4 mr-2" />
            Télécharger PDF
          </Button>
        )}
        {canSendWhatsApp && (
          <Button
            onClick={handleSendWhatsApp}
            disabled={whatsappLoading || !clientWhatsApp}
            className="bg-green-600 hover:bg-green-700 text-white"
            size="sm"
          >
            <MessageCircle className="h-4 w-4 mr-2" />
            Envoyer WhatsApp
          </Button>
        )}
        {canSendEmail && (
          <Button
            onClick={handleSendEmail}
            disabled={emailLoading || !clientEmail}
            variant="outline"
            size="sm"
          >
            <Mail className="h-4 w-4 mr-2" />
            Envoyer Email
          </Button>
        )}
      </div>

      {!clientWhatsApp && canSendWhatsApp && (
        <p className="text-sm text-yellow-600 mt-2">
          ⚠️ Numéro WhatsApp non configuré pour ce client
        </p>
      )}
      {!clientEmail && canSendEmail && (
        <p className="text-sm text-yellow-600 mt-2">
          ⚠️ Email non configuré pour ce client
        </p>
      )}

      {/* PDF Preview Modal */}
      {showPdfPreview && pdfUrl && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
            <div className="flex justify-between items-center p-4 border-b">
              <h3 className="text-lg font-semibold">
                Aperçu {documentType} {documentReference}
              </h3>
              <Button variant="ghost" onClick={() => setShowPdfPreview(false)}>
                Fermer
              </Button>
            </div>
            <div className="p-4">
              <iframe
                src={pdfUrl}
                className="w-full h-[70vh]"
                title="PDF Preview"
              />
            </div>
          </div>
        </div>
      )}
    </>
  );
}
