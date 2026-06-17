/**
 * DocumentActions — boutons Aperçu / Imprimer / Partager WhatsApp
 *
 * Usage :
 *   <DocumentActions
 *     pdfUrl="/api/factures/<id>/pdf"
 *     filename="FABS-FC-26-27-0001.pdf"
 *     message="Bonjour, voici votre facture FABS-FC-26-27-0001"
 *     documentType="facture"
 *     documentReference="FABS-FC-26-27-0001"
 *     clientNom="ALPHA SARL"
 *     apiShareUrl="/api/factures/<id>/partager-whatsapp"  // optionnel
 *   />
 *
 * WhatsApp : Web Share API natif (PDF joint) → fallback download + wa.me sans numéro
 */
import { useRef } from "react";
import { Eye, Printer, MessageCircle } from "lucide-react";
import { Button } from "../ui/button";
import { toast } from "sonner";
import { tokenStore } from "../../hooks/useAuth";
import { useWhatsAppShare } from "../../hooks/useWhatsAppShare";

export default function DocumentActions({
  pdfUrl,
  filename,
  message,
  documentType,
  documentReference,
  clientNom,
  montant,
  apiShareUrl,
  testIdPrefix = "doc",
}) {
  const iframeRef = useRef(null);

  // Génère le blob PDF depuis l'API (utilisé par le hook de partage)
  const fetchPdfBlob = async () => {
    const token = tokenStore.get();
    const res = await fetch(pdfUrl, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.blob();
  };

  const { shareViaWhatsApp, sharing: waSharing } = useWhatsAppShare({
    onGeneratePDF: fetchPdfBlob,
    documentType,
    documentReference,
    clientNom,
    montant,
    apiShareUrl,
  });

  const openPdfBlob = async (action) => {
    try {
      const token = tokenStore.get();
      const res = await fetch(pdfUrl, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      if (action === "preview") {
        window.open(url, "_blank", "noopener,noreferrer");
      } else if (action === "print") {
        if (iframeRef.current) {
          iframeRef.current.src = url;
          iframeRef.current.onload = () => {
            try {
              iframeRef.current.contentWindow.focus();
              iframeRef.current.contentWindow.print();
            } catch (e) {
              window.open(url, "_blank");
            }
          };
        } else {
          const w = window.open(url, "_blank");
          if (w) setTimeout(() => w.print(), 800);
        }
      } else if (action === "download") {
        const a = document.createElement("a");
        a.href = url;
        a.download = filename || "document.pdf";
        a.click();
      }
    } catch (e) {
      toast.error("Impossible de charger le PDF");
    }
  };

  return (
    <div className="flex flex-wrap gap-2 items-center" data-testid={`${testIdPrefix}-actions`}>
      <Button
        variant="outline"
        size="sm"
        onClick={() => openPdfBlob("preview")}
        data-testid={`${testIdPrefix}-preview-btn`}
      >
        <Eye className="h-4 w-4 mr-2" />
        Aperçu
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => openPdfBlob("print")}
        data-testid={`${testIdPrefix}-print-btn`}
      >
        <Printer className="h-4 w-4 mr-2" />
        Imprimer
      </Button>
      <Button
        size="sm"
        onClick={shareViaWhatsApp}
        disabled={waSharing}
        className="bg-[#25D366] hover:bg-[#1EBE5D] text-white"
        data-testid={`${testIdPrefix}-whatsapp-btn`}
      >
        <MessageCircle className="h-4 w-4 mr-2" />
        {waSharing ? 'Partage…' : 'WhatsApp'}
      </Button>
      <iframe
        ref={iframeRef}
        title="print-frame"
        style={{ display: "none" }}
      />
    </div>
  );
}
