/**
 * PageHeader V10 — En-tête de page uniforme ERP FABS-CI
 * Style dark premium (maquette juin 2026)
 */
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ArrowLeft, Home, Star, LayoutDashboard } from "lucide-react";
import { Button } from "../ui/button";

const FAV_KEY = "fabs.favs";

const readFavs = () => {
  try { return JSON.parse(localStorage.getItem(FAV_KEY) || "[]"); }
  catch { return []; }
};

const writeFavs = (favs) => {
  localStorage.setItem(FAV_KEY, JSON.stringify(favs));
  window.dispatchEvent(new Event("fabs.favs.update"));
};

export default function PageHeader({
  icon: Icon,
  title,
  description,
  actions,
  showBack = true,
  showHome = true,
  showDashboard = true,
  showFavorite = true,
  favoriteKey,
  accentColor,
}) {
  const navigate = useNavigate();
  const location = useLocation();
  const key = favoriteKey || location.pathname;
  const onDashboard = location.pathname === "/dashboard" || location.pathname === "/";

  const [isFav, setIsFav] = useState(() => readFavs().some((f) => f.key === key));

  useEffect(() => {
    const handler = () => setIsFav(readFavs().some((f) => f.key === key));
    window.addEventListener("fabs.favs.update", handler);
    return () => window.removeEventListener("fabs.favs.update", handler);
  }, [key]);

  const toggleFav = () => {
    const favs = readFavs();
    const idx = favs.findIndex((f) => f.key === key);
    if (idx >= 0) { favs.splice(idx, 1); }
    else { favs.push({ key, label: title, path: location.pathname }); }
    writeFavs(favs);
    setIsFav(!isFav);
  };

  const accent = accentColor || "#F97316";

  return (
    <div className="space-y-4 mb-6" data-testid="page-header">
      {/* Nav rapide */}
      <div className="flex items-center gap-2 flex-wrap">
        {showBack && (
          <Button variant="outline" size="sm" onClick={() => navigate(-1)} data-testid="btn-back">
            <ArrowLeft className="w-4 h-4 mr-1" />
            Retour
          </Button>
        )}
        {showHome && !onDashboard && (
          <Button variant="outline" size="sm" onClick={() => navigate("/")} data-testid="btn-home">
            <Home className="w-4 h-4 mr-1" />
            Accueil
          </Button>
        )}
        {showDashboard && !onDashboard && (
          <Button variant="outline" size="sm" onClick={() => navigate("/dashboard")} data-testid="btn-dashboard">
            <LayoutDashboard className="w-4 h-4 mr-1" />
            Tableau de bord
          </Button>
        )}
        {showFavorite && (
          <Button
            variant="outline"
            size="sm"
            onClick={toggleFav}
            data-testid="btn-favorite"
            title={isFav ? "Retirer des favoris" : "Ajouter aux favoris"}
            style={isFav ? {
              background: "rgba(249,115,22,0.12)",
              borderColor: "rgba(249,115,22,0.3)",
              color: "#F97316",
            } : {}}
          >
            <Star className={`w-4 h-4 mr-1 ${isFav ? "fill-[#F97316]" : ""}`} />
            {isFav ? "Favori" : "Ajouter aux favoris"}
          </Button>
        )}
      </div>

      {/* Hero titre */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div className="flex items-start gap-4">
          {Icon && (
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center shrink-0"
              style={{
                background: `linear-gradient(135deg, ${accent}, ${accent}CC)`,
                boxShadow: `0 8px 24px ${accent}35`,
              }}
            >
              <Icon className="h-7 w-7 text-white" strokeWidth={2} />
            </div>
          )}
          <div className="min-w-0">
            <h1
              className="text-3xl md:text-4xl font-bold tracking-tight leading-tight"
              style={{ color: "#E2E8F0", letterSpacing: "-0.02em" }}
              data-testid="page-title"
            >
              {title}
            </h1>
            {description && (
              <p className="text-sm mt-1.5 max-w-2xl" style={{ color: "#94A3B8" }}>
                {description}
              </p>
            )}
          </div>
        </div>
        {actions && (
          <div className="flex gap-2 flex-wrap items-center shrink-0">
            {actions}
          </div>
        )}
      </div>
    </div>
  );
}
