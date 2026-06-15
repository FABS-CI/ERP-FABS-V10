/**
 * Breadcrumb V10 — Fil d'Ariane automatique
 * Génère le chemin à partir de la route courante en utilisant la map MODULES
 */
import { Link, useLocation } from "react-router-dom";
import { ChevronRight, Home } from "lucide-react";
import { MODULES } from "../../constants/permissions";

export default function Breadcrumb() {
  const location = useLocation();
  if (location.pathname === "/" || location.pathname === "/dashboard") return null;

  const parts = location.pathname.split("/").filter(Boolean);

  // Identifier le groupe et le module exacts pour la route
  const moduleMatch = MODULES
    .map((m) => ({ ...m, score: location.pathname.startsWith(m.path) ? m.path.length : 0 }))
    .filter((m) => m.score > 0)
    .sort((a, b) => b.score - a.score)[0];

  const crumbs = [{ label: "Accueil", path: "/dashboard", isHome: true }];
  if (moduleMatch) {
    if (moduleMatch.group) crumbs.push({ label: moduleMatch.group, path: null });
    crumbs.push({ label: moduleMatch.label, path: moduleMatch.path });
    // Sous-page : si l'URL contient un ID après le path du module
    const rest = location.pathname.slice(moduleMatch.path.length).split("/").filter(Boolean);
    if (rest.length > 0) {
      crumbs.push({ label: rest.length === 1 && rest[0].length > 20 ? "Détail" : rest.join(" / "), path: null });
    }
  } else {
    parts.forEach((p, i) => crumbs.push({ label: p, path: "/" + parts.slice(0, i + 1).join("/") }));
  }

  return (
    <nav
      aria-label="Fil d'Ariane"
      className="flex items-center gap-1.5 text-xs text-muted-foreground mb-4 flex-wrap"
      data-testid="breadcrumb"
    >
      {crumbs.map((c, i) => (
        <span key={i} className="flex items-center gap-1.5">
          {i > 0 && <ChevronRight className="w-3 h-3 opacity-50" />}
          {c.isHome ? (
            <Link to={c.path} className="hover:text-[#FF6200] flex items-center gap-1" data-testid="bc-home">
              <Home className="w-3.5 h-3.5" />
            </Link>
          ) : c.path ? (
            <Link to={c.path} className="hover:text-[#FF6200] capitalize">{c.label}</Link>
          ) : (
            <span className="text-[#0A2540] dark:text-white font-medium capitalize">{c.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}
