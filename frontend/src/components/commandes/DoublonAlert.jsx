/**
 * DoublonAlert — Dialog affiché lors d'un doublon détecté
 * Sprint 6 - Détection doublons temps réel
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, Eye, X, ArrowLeft } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';

/**
 * @param {Object} props
 * @param {boolean} props.open
 * @param {Object|null} props.commande  — commande doublon retournée par l'API
 * @param {'certain'|'probable'} props.niveau
 * @param {string} props.logId          — ID du log doublon (pour PATCH décision)
 * @param {Function} props.onContinue   — callback "Continuer quand même"
 * @param {Function} props.onCancel     — callback "Annuler la saisie"
 */
export default function DoublonAlert({ open, commande, niveau, logId, onContinue, onCancel }) {
  const navigate = useNavigate();

  if (!commande) return null;

  const isCertain = niveau === 'certain';

  const formatCurrency = (amount) =>
    new Intl.NumberFormat('fr-FR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(amount) + ' FCFA';

  const formatDate = (iso) => {
    if (!iso) return '-';
    try {
      return new Intl.DateTimeFormat('fr-FR', { dateStyle: 'long', timeStyle: 'short' }).format(new Date(iso));
    } catch {
      return iso;
    }
  };

  return (
    <Dialog open={open} onOpenChange={() => {}}>
      <DialogContent className="max-w-lg" onPointerDownOutside={(e) => e.preventDefault()}>
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-full ${isCertain ? 'bg-red-100' : 'bg-orange-100'}`}>
              <AlertTriangle className={`h-6 w-6 ${isCertain ? 'text-red-600' : 'text-orange-500'}`} />
            </div>
            <div>
              <DialogTitle className="text-lg">
                {isCertain ? 'Doublon détecté' : 'Commande similaire détectée'}
              </DialogTitle>
              <DialogDescription className="mt-1">
                {isCertain
                  ? 'Une commande identique a été saisie dans les dernières 48h.'
                  : 'Une commande similaire existe pour ce client (représentant/téléphone différent).'}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-3 my-2">
          <Badge
            className={`text-xs px-3 py-1 ${
              isCertain
                ? 'bg-red-100 text-red-700 border-red-200'
                : 'bg-orange-100 text-orange-700 border-orange-200'
            }`}
            variant="outline"
          >
            {isCertain ? 'Doublon certain' : 'Doublon probable'}
          </Badge>

          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-white/50">Référence</span>
              <span className="font-semibold text-[#0A2540] dark:text-white">{commande.reference || '-'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-white/50">Date</span>
              <span>{formatDate(commande.created_at)}</span>
            </div>
            <Separator />
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-white/50">Client</span>
              <span>{commande.client_nom || commande.client_id}</span>
            </div>
            {commande.client_representant && (
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-white/50">Représentant</span>
                <span>{commande.client_representant}</span>
              </div>
            )}
            {commande.client_telephone && (
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-white/50">Téléphone</span>
                <span>{commande.client_telephone}</span>
              </div>
            )}
            <Separator />
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-white/50">Montant total</span>
              <span className="font-bold text-[#FF6200]">{formatCurrency(commande.montant_total || 0)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-white/50">Statut</span>
              <Badge variant="outline" className="text-xs capitalize">{commande.statut}</Badge>
            </div>
          </div>
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2 mt-2">
          {/* Voir la commande existante */}
          <Button
            variant="outline"
            className="w-full sm:w-auto border-blue-300 text-blue-700 hover:bg-blue-50"
            onClick={() => navigate(`/commandes/${commande.commande_id}`)}
          >
            <Eye className="h-4 w-4 mr-2" />
            Voir la commande
          </Button>

          {/* Continuer quand même */}
          <Button
            variant="outline"
            className="w-full sm:w-auto border-orange-300 text-orange-700 hover:bg-orange-50"
            onClick={onContinue}
          >
            <X className="h-4 w-4 mr-2" />
            Continuer quand même
          </Button>

          {/* Annuler la saisie */}
          <Button
            className="w-full sm:w-auto bg-red-600 hover:bg-red-700 text-white"
            onClick={onCancel}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Annuler la saisie
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
