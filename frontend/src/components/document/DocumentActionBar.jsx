/**
 * DocumentActionBar — Barre d'actions documents ERP FABS-CI V10
 * Boutons : Aperçu PDF · Imprimer · Télécharger · WhatsApp · Email
 * WhatsApp : Web Share API natif (PDF joint) → fallback téléchargement + wa.me sans numéro
 * Email    : modale To/CC/BCC/Objet/Message
 */
import React, { useState } from 'react';
import { Eye, Printer, Download, MessageCircle, Mail, X, Send } from 'lucide-react';
import { Button } from '../ui/button';
import { toast } from 'sonner';
import { useWhatsAppShare } from '../../hooks/useWhatsAppShare';

/* ─── helpers ─────────────────────────────────────────────────── */
function buildDefaultEmailMessage(documentType, documentReference, clientNom) {
  const typeLabel = documentType
    ? documentType.charAt(0).toUpperCase() + documentType.slice(1)
    : 'Document';
  return `Bonjour${clientNom ? ' ' + clientNom : ''},\n\nVeuillez trouver ci-joint votre ${typeLabel}${documentReference ? ' N° ' + documentReference : ''}.\n\nNous restons à votre disposition pour toute information complémentaire.\n\nCordialement,\nÉditions FABS-CI`;
}

/* ─── composant ───────────────────────────────────────────────── */
export default function DocumentActionBar({
  documentType,
  documentId,
  documentReference,
  clientNom,
  clientEmail,
  montant,
  onGeneratePDF,
  onPrint,
  onDownload,
  onSendWhatsApp,   // legacy — conservé pour compat, non utilisé pour le partage
  onSendEmail,      // (payload: { destinataire, cc, bcc, objet, message }) => Promise
  apiShareUrl,      // ex: /api/factures/{id}/partager-whatsapp (log serveur, optionnel)
  canPreview    = true,
  canPrint      = true,
  canDownload   = true,
  canSendWhatsApp = true,
  canSendEmail    = true,
}) {
  const [pdfLoading, setPdfLoading]     = useState(false);
  const [pdfUrl, setPdfUrl]             = useState(null);
  const [showPdfPreview, setShowPdfPreview] = useState(false);

  /* ── WhatsApp via Web Share API ── */
  const { shareViaWhatsApp, sharing: waSharing } = useWhatsAppShare({
    onGeneratePDF,
    documentType,
    documentReference,
    clientNom,
    montant,
    apiShareUrl,
  });

  /* ── modale Email ── */
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [emailLoading, setEmailLoading]     = useState(false);
  const [emailForm, setEmailForm] = useState({
    destinataire: '',
    cc: '',
    bcc: '',
    objet: '',
    message: '',
  });

  /* pré-remplissage email */
  const openEmailModal = () => {
    setEmailForm({
      destinataire: clientEmail || '',
      cc: '',
      bcc: '',
      objet: `${documentType ? documentType.charAt(0).toUpperCase() + documentType.slice(1) : 'Document'}${documentReference ? ' ' + documentReference : ''}`.trim(),
      message: buildDefaultEmailMessage(documentType, documentReference, clientNom),
    });
    setShowEmailModal(true);
  };

  /* ── PDF ── */
  const handlePreview = async () => {
    try {
      setPdfLoading(true);
      const blob = await onGeneratePDF();
      const url = URL.createObjectURL(blob);
      setPdfUrl(url);
      setShowPdfPreview(true);
      toast.success('PDF généré');
    } catch (e) {
      toast.error('Erreur génération PDF');
    } finally {
      setPdfLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
      setPdfLoading(true);
      const blob = await onDownload();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${documentType || 'document'}_${documentReference || documentId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('PDF téléchargé');
    } catch (e) {
      toast.error('Erreur téléchargement PDF');
    } finally {
      setPdfLoading(false);
    }
  };

  const handlePrint = async () => {
    try {
      setPdfLoading(true);
      const blob = await onPrint();
      const url = URL.createObjectURL(blob);
      const win = window.open(url, '_blank');
      if (win) win.onload = () => win.print();
      toast.success('Impression lancée');
    } catch (e) {
      toast.error("Erreur impression");
    } finally {
      setPdfLoading(false);
    }
  };

  /* ── Email submit ── */
  const handleEmailSubmit = async () => {
    if (!emailForm.destinataire.trim()) {
      toast.error('Veuillez saisir un destinataire');
      return;
    }
    try {
      setEmailLoading(true);
      const result = await onSendEmail({
        destinataire: emailForm.destinataire.trim(),
        cc: emailForm.cc.trim() || null,
        bcc: emailForm.bcc.trim() || null,
        objet: emailForm.objet.trim() || null,
        message: emailForm.message.trim() || null,
      });
      toast.success(result?.message || 'Email envoyé avec succès');
      setShowEmailModal(false);
    } catch (e) {
      toast.error("Erreur lors de l'envoi de l'email");
    } finally {
      setEmailLoading(false);
    }
  };

  /* ── classes input réutilisables ── */
  const inputCls = 'w-full border border-gray-300 dark:border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#FF6200]/40 focus:border-[#FF6200]';

  return (
    <>
      {/* ══ Barre de boutons ══════════════════════════════════════ */}
      <div className="flex flex-wrap gap-3">
        {canPreview && (
          <Button onClick={handlePreview} disabled={pdfLoading} variant="outline" size="sm">
            <Eye className="h-4 w-4 mr-2" />
            Aperçu PDF
          </Button>
        )}
        {canPrint && (
          <Button onClick={handlePrint} disabled={pdfLoading} variant="outline" size="sm">
            <Printer className="h-4 w-4 mr-2" />
            Imprimer
          </Button>
        )}
        {canDownload && (
          <Button onClick={handleDownload} disabled={pdfLoading} variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Télécharger PDF
          </Button>
        )}
        {canSendWhatsApp && (
          <Button
            onClick={shareViaWhatsApp}
            disabled={waSharing || pdfLoading}
            className="bg-green-600 hover:bg-green-700 text-white"
            size="sm"
          >
            <MessageCircle className="h-4 w-4 mr-2" />
            {waSharing ? 'Partage…' : 'Partager WhatsApp'}
          </Button>
        )}
        {canSendEmail && (
          <Button onClick={openEmailModal} variant="outline" size="sm">
            <Mail className="h-4 w-4 mr-2" />
            Envoyer Email
          </Button>
        )}
      </div>

      {/* ══ Modale Email ═════════════════════════════════════════ */}
      {showEmailModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-[#0b1e30] rounded-xl shadow-2xl w-full max-w-lg">
            {/* header */}
            <div className="flex justify-between items-center px-6 py-4 border-b">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Mail className="h-5 w-5 text-[#0A2540]" />
                Envoyer par email
              </h3>
              <button onClick={() => setShowEmailModal(false)} className="text-gray-400 hover:text-gray-600 dark:text-white/70">
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* body */}
            <div className="px-6 py-4 space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">
                  À <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  value={emailForm.destinataire}
                  onChange={e => setEmailForm(f => ({ ...f, destinataire: e.target.value }))}
                  placeholder="destinataire@email.com"
                  className={inputCls}
                  autoFocus
                />
                {!clientEmail && (
                  <p className="text-xs text-gray-500 dark:text-white/50 mt-1">
                    Aucun email enregistré pour ce client — saisissez-le manuellement.
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">CC</label>
                <input
                  type="text"
                  value={emailForm.cc}
                  onChange={e => setEmailForm(f => ({ ...f, cc: e.target.value }))}
                  placeholder="cc1@email.com, cc2@email.com"
                  className={inputCls}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">BCC</label>
                <input
                  type="text"
                  value={emailForm.bcc}
                  onChange={e => setEmailForm(f => ({ ...f, bcc: e.target.value }))}
                  placeholder="bcc@email.com"
                  className={inputCls}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">Objet</label>
                <input
                  type="text"
                  value={emailForm.objet}
                  onChange={e => setEmailForm(f => ({ ...f, objet: e.target.value }))}
                  placeholder="Objet de l'email"
                  className={inputCls}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-white/90 mb-1">Message</label>
                <textarea
                  value={emailForm.message}
                  onChange={e => setEmailForm(f => ({ ...f, message: e.target.value }))}
                  rows={5}
                  className={`${inputCls} resize-none`}
                />
              </div>

              {onGeneratePDF && (
                <button
                  type="button"
                  onClick={handlePreview}
                  className="text-sm text-[#FF6200] underline underline-offset-2 hover:text-[#E55900]"
                >
                  Aperçu du PDF joint
                </button>
              )}
            </div>

            {/* footer */}
            <div className="px-6 py-4 border-t flex justify-end gap-3">
              <Button variant="outline" size="sm" onClick={() => setShowEmailModal(false)}>
                Annuler
              </Button>
              <Button
                size="sm"
                onClick={handleEmailSubmit}
                disabled={emailLoading || !emailForm.destinataire.trim()}
                className="bg-[#0A2540] hover:bg-[#0A2540]/90 text-white"
              >
                <Send className="h-4 w-4 mr-2" />
                {emailLoading ? 'Envoi…' : 'Envoyer'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ══ Modale Aperçu PDF ════════════════════════════════════ */}
      {showPdfPreview && pdfUrl && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-[#0b1e30] rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="flex justify-between items-center p-4 border-b">
              <h3 className="text-lg font-semibold">
                Aperçu — {documentType} {documentReference}
              </h3>
              <Button variant="ghost" size="sm" onClick={() => setShowPdfPreview(false)}>
                <X className="h-4 w-4 mr-1" /> Fermer
              </Button>
            </div>
            <iframe src={pdfUrl} className="w-full flex-1" title="Aperçu PDF" style={{ minHeight: '70vh' }} />
          </div>
        </div>
      )}
    </>
  );
}
