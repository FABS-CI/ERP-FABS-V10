/**
 * useWhatsAppShare — partage natif WhatsApp via Web Share API (niveau OS)
 *
 * Comportement :
 *   1. Génère le PDF via onGeneratePDF()
 *   2. navigator.canShare({ files }) → true  → share sheet OS (PDF joint)
 *                                    → false → télécharge le PDF + ouvre wa.me sans numéro
 *   3. Loggue l'événement via POST /api/historique-partages (best-effort)
 *
 * Usage :
 *   const { shareViaWhatsApp, sharing } = useWhatsAppShare({ onGeneratePDF, documentType, documentReference, clientNom, montant, apiShareUrl });
 *   <button onClick={shareViaWhatsApp} disabled={sharing}>WhatsApp</button>
 */
import { useState } from 'react';
import { toast } from 'sonner';
import { tokenStore } from './useAuth';

function buildMessage(documentType, documentReference, clientNom, montant) {
  const typeLabel = documentType
    ? documentType.charAt(0).toUpperCase() + documentType.slice(1)
    : 'Document';
  let msg = `Bonjour${clientNom ? ' ' + clientNom : ''},\n\nVeuillez trouver ci-joint votre ${typeLabel}`;
  if (documentReference) msg += ` N° ${documentReference}`;
  if (montant) msg += `\n\nMontant : ${montant}`;
  msg += `\n\nMerci de votre confiance.\nÉditions FABS-CI`;
  return msg;
}

async function logShareEvent({ apiShareUrl, documentType, documentReference }) {
  if (!apiShareUrl) return;
  try {
    const token = tokenStore.get();
    await fetch(apiShareUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        canal: 'whatsapp',
        statut: 'partage_lance',
        document_type: documentType || null,
        document_ref: documentReference || null,
      }),
    });
  } catch {
    // best-effort — ne pas bloquer l'UX
  }
}

export function useWhatsAppShare({
  onGeneratePDF,
  documentType,
  documentReference,
  clientNom,
  montant,
  apiShareUrl, // ex: /api/factures/{id}/partager-whatsapp
}) {
  const [sharing, setSharing] = useState(false);

  const shareViaWhatsApp = async () => {
    if (!onGeneratePDF) {
      toast.error('Génération PDF non configurée');
      return;
    }

    setSharing(true);
    let blob;
    try {
      blob = await onGeneratePDF();
    } catch {
      toast.error('Erreur lors de la génération du PDF');
      setSharing(false);
      return;
    }

    const filename = `${documentType || 'document'}_${documentReference || 'FABS'}.pdf`;
    const message  = buildMessage(documentType, documentReference, clientNom, montant);

    // Tenter le partage natif avec fichier joint
    const pdfFile = new File([blob], filename, { type: 'application/pdf' });
    const canShareFile =
      typeof navigator.share === 'function' &&
      typeof navigator.canShare === 'function' &&
      navigator.canShare({ files: [pdfFile] });

    if (canShareFile) {
      try {
        await navigator.share({ files: [pdfFile], text: message, title: filename });
        toast.success('Document partagé');
        await logShareEvent({ apiShareUrl, documentType, documentReference });
      } catch (err) {
        // AbortError = utilisateur a annulé — pas une vraie erreur
        if (err?.name !== 'AbortError') {
          toast.error('Erreur partage natif — essai fallback');
          fallback(blob, filename, message);
        }
      }
    } else {
      fallback(blob, filename, message);
    }

    setSharing(false);
  };

  return { shareViaWhatsApp, sharing };
}

// ── Fallback : télécharge le PDF + ouvre wa.me sans numéro ─────────────────
function fallback(blob, filename, message) {
  // 1. Télécharger le PDF automatiquement
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 5000);

  // 2. Ouvrir WhatsApp Web sans numéro (l'utilisateur choisit le contact)
  const waUrl = `https://wa.me/?text=${encodeURIComponent(message)}`;
  window.open(waUrl, '_blank', 'noopener,noreferrer');

  toast.info('PDF téléchargé — joignez-le manuellement dans WhatsApp', { duration: 6000 });
}
