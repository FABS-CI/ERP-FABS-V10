import { useNavigate } from "react-router-dom";
import { ArrowLeft, Home, Star, MoreVertical } from "lucide-react";
import { Button } from "./ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { useEffect, useState } from "react";

export default function PageHeader({ 
  title, 
  subtitle, 
  showBackButton = true, 
  onBackClick = null,
  showHomeButton = true,
  showAddFavorite = true,
  pagePath = null,
  actions = null,
}) {
  const navigate = useNavigate();
  const [isFavorite, setIsFavorite] = useState(false);

  // Load favorites from localStorage
  useEffect(() => {
    if (!pagePath) return;
    const favorites = JSON.parse(localStorage.getItem("page_favorites") || "[]");
    setIsFavorite(favorites.includes(pagePath));
  }, [pagePath]);

  const handleBack = () => {
    if (onBackClick) {
      onBackClick();
    } else {
      navigate(-1);
    }
  };

  const handleHome = () => {
    navigate("/dashboard");
  };

  const handleAddFavorite = () => {
    if (!pagePath) return;
    const favorites = JSON.parse(localStorage.getItem("page_favorites") || "[]");
    if (isFavorite) {
      const updated = favorites.filter((p) => p !== pagePath);
      localStorage.setItem("page_favorites", JSON.stringify(updated));
      setIsFavorite(false);
    } else {
      favorites.push(pagePath);
      localStorage.setItem("page_favorites", JSON.stringify(favorites));
      setIsFavorite(true);
    }
  };

  return (
    <div className="flex items-start justify-between mb-6">
      <div className="flex items-center gap-4 flex-1">
        {showBackButton && (
          <button
            onClick={handleBack}
            className="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition"
            title="Retour"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-white/70" />
          </button>
        )}
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {title}
          </h1>
          {subtitle && (
            <p className="text-sm text-gray-500 dark:text-white/50 mt-1">
              {subtitle}
            </p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2">
        {/* Actions personnalisées */}
        {actions && (
          <div className="flex items-center gap-2">
            {actions}
          </div>
        )}

        {/* Menu actions */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-10 w-10">
              <MoreVertical className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            {showHomeButton && (
              <DropdownMenuItem onClick={handleHome}>
                <Home className="w-4 h-4 mr-2" />
                <span>Tableau de bord</span>
              </DropdownMenuItem>
            )}
            {showAddFavorite && pagePath && (
              <DropdownMenuItem onClick={handleAddFavorite}>
                <Star
                  className={`w-4 h-4 mr-2 ${
                    isFavorite ? "fill-yellow-400 text-yellow-400" : ""
                  }`}
                />
                <span>
                  {isFavorite ? "Retirer des favoris" : "Ajouter aux favoris"}
                </span>
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}
