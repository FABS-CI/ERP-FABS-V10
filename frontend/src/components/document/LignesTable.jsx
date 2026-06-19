/**
 * Composant réutilisable pour afficher les lignes de documents
 * Facture, Commande, Bon de Livraison...
 */
import React from 'react';
import { Badge } from '../ui/badge';

export default function LignesTable({ lignes, showPrix = true, titre = "Lignes" }) {
  if (!Array.isArray(lignes) || lignes.length === 0) {
    return <div className="text-gray-500 text-sm">Aucune ligne</div>;
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('fr-FR', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount) + ' FCFA';
  };

  // Grouper par cycle si présent
  const grouped = {};
  const cycles_order = [];
  
  lignes.forEach((ligne) => {
    const cycle = ligne.produit_cycle || ligne.classe_cycle || "Divers";
    if (!grouped[cycle]) {
      grouped[cycle] = [];
      cycles_order.push(cycle);
    }
    grouped[cycle].push(ligne);
  });

  return (
    <div className="space-y-4">
      {cycles_order.map((cycle) => (
        <div key={cycle} className="space-y-2">
          {cycle !== "Divers" && (
            <h3 className="font-semibold text-sm text-gray-700 dark:text-gray-300 uppercase">
              {cycle}
            </h3>
          )}
          
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900/50">
                  <th className="text-left px-3 py-2 font-semibold text-gray-700 dark:text-gray-300">
                    Niveau
                  </th>
                  <th className="text-left px-3 py-2 font-semibold text-gray-700 dark:text-gray-300">
                    Matière
                  </th>
                  <th className="text-left px-3 py-2 font-semibold text-gray-700 dark:text-gray-300">
                    Code Article
                  </th>
                  <th className="text-left px-3 py-2 font-semibold text-gray-700 dark:text-gray-300">
                    Désignation
                  </th>
                  <th className="text-center px-3 py-2 font-semibold text-gray-700 dark:text-gray-300">
                    Qté
                  </th>
                  {showPrix && (
                    <>
                      <th className="text-right px-3 py-2 font-semibold text-gray-700 dark:text-gray-300">
                        PU
                      </th>
                      <th className="text-right px-3 py-2 font-semibold text-gray-700 dark:text-gray-300">
                        Montant
                      </th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody>
                {grouped[cycle].map((ligne, idx) => (
                  <tr
                    key={ligne.ligne_id || idx}
                    className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-900/30"
                  >
                    <td className="px-3 py-2 text-gray-900 dark:text-white">
                      {ligne.produit_niveau_scolaire || ligne.classe || "-"}
                    </td>
                    <td className="px-3 py-2 text-gray-900 dark:text-white">
                      {ligne.produit_matiere || "-"}
                    </td>
                    <td className="px-3 py-2 text-gray-700 dark:text-gray-300 font-mono text-xs">
                      {ligne.produit_reference || ligne.produit_id?.substring(0, 10) || "-"}
                    </td>
                    <td className="px-3 py-2 text-gray-900 dark:text-white max-w-[300px]">
                      <div className="font-medium">{ligne.produit_titre || "-"}</div>
                      {ligne.remise_ligne > 0 && (
                        <Badge variant="outline" className="mt-1 text-orange-600 text-xs">
                          Remise: -{ligne.remise_ligne}%
                        </Badge>
                      )}
                    </td>
                    <td className="px-3 py-2 text-center text-gray-900 dark:text-white font-medium">
                      {ligne.quantite}
                    </td>
                    {showPrix && (
                      <>
                        <td className="px-3 py-2 text-right text-gray-900 dark:text-white">
                          {formatCurrency(ligne.prix_unitaire)}
                        </td>
                        <td className="px-3 py-2 text-right text-gray-900 dark:text-white font-semibold">
                          {formatCurrency(ligne.montant_ligne || 0)}
                        </td>
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
}
