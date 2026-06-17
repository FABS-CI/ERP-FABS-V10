/**
 * Composant Pagination — TICKET-004
 * Navigation pages générique, réutilisable dans toute l'app
 */
import React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "./button";

/**
 * @param {number}   total       Nombre total d'éléments
 * @param {number}   page        Page courante (1-indexée)
 * @param {number}   pageSize    Éléments par page
 * @param {function} onPageChange Callback (newPage: number)
 */
export default function Pagination({ total, page, pageSize, onPageChange }) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  if (totalPages <= 1) return null;

  // Fenêtre de pages à afficher : max 5 boutons autour de la page courante
  const buildPages = () => {
    const delta = 2;
    const range = [];
    for (
      let i = Math.max(1, page - delta);
      i <= Math.min(totalPages, page + delta);
      i++
    ) {
      range.push(i);
    }
    // Ajouter première / dernière page + ellipses si nécessaire
    if (range[0] > 2) range.unshift("...");
    if (range[0] !== 1) range.unshift(1);
    if (range[range.length - 1] < totalPages - 1) range.push("...");
    if (range[range.length - 1] !== totalPages) range.push(totalPages);
    return range;
  };

  const pages = buildPages();
  const debut = (page - 1) * pageSize + 1;
  const fin = Math.min(page * pageSize, total);

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
      {/* Compteur */}
      <span className="text-sm text-gray-500 dark:text-white/50">
        {debut}–{fin} sur {total} résultat{total > 1 ? "s" : ""}
      </span>

      {/* Boutons navigation */}
      <div className="flex items-center gap-1">
        {/* Précédent */}
        <Button
          variant="outline"
          size="sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          aria-label="Page précédente"
          className="h-8 w-8 p-0"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>

        {/* Numéros de pages */}
        {pages.map((p, idx) =>
          p === "..." ? (
            <span key={`ellipsis-${idx}`} className="px-2 text-gray-400 select-none">
              …
            </span>
          ) : (
            <Button
              key={p}
              variant={p === page ? "default" : "outline"}
              size="sm"
              onClick={() => onPageChange(p)}
              className={`h-8 w-8 p-0 ${
                p === page
                  ? "bg-[#FF6200] hover:bg-[#E55900] text-white border-[#FF6200]"
                  : ""
              }`}
            >
              {p}
            </Button>
          )
        )}

        {/* Suivant */}
        <Button
          variant="outline"
          size="sm"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
          aria-label="Page suivante"
          className="h-8 w-8 p-0"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
