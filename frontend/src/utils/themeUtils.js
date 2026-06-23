/**
 * Theme Utilities — Génération variantes & détection module
 * 
 * Chaque module a une couleur base qui génère automatiquement :
 * - lighter (20% opacité)
 * - light (12% opacité)
 * - accent (teinte saturée)
 * - dark (20% plus sombre)
 * - darker (40% plus sombre)
 */

// ── Mapping module → couleur base ──────────────────────────────────
const MODULE_COLOR_MAP = {
  "dashboard": "#3B82F6",           // Bleu
  "commerciale": "#F97316",          // Orange
  "stocks": "#10B981",               // Vert
  "logistique": "#10B981",           // Vert (même que stocks)
  "finances": "#14B8A6",             // Teal
  "comptabilite": "#14B8A6",         // Teal (même que finances)
  "rh": "#8B5CF6",                   // Purple
  "ressources-humaines": "#8B5CF6",  // Purple
  "achats": "#14B8A6",               // Teal
  "approvisionnements": "#14B8A6",   // Teal
  "crm": "#EC4899",                  // Rose/Pink
  "admin": "#9CA3AF",                // Gris
  "parametres": "#9CA3AF",           // Gris
};

// ── Générer variantes couleur ──────────────────────────────────────
function generateColorVariants(baseColor) {
  const base = baseColor.replace("#", "");
  const r = parseInt(base.substring(0, 2), 16);
  const g = parseInt(base.substring(2, 4), 16);
  const b = parseInt(base.substring(4, 6), 16);

  return {
    base: baseColor,
    light: `rgba(${r},${g},${b},0.12)`,       // 12% opacité
    lighter: `rgba(${r},${g},${b},0.20)`,     // 20% opacité
    accent: baseColor,                         // Même que base (saturé)
    dark: adjustBrightness(baseColor, -0.2),  // 20% plus sombre
    darker: adjustBrightness(baseColor, -0.4), // 40% plus sombre
  };
}

// Ajuster luminosité couleur (HSL)
function adjustBrightness(color, percent) {
  const hex = color.replace("#", "");
  const r = parseInt(hex.substring(0, 2), 16) / 255;
  const g = parseInt(hex.substring(2, 4), 16) / 255;
  const b = parseInt(hex.substring(4, 6), 16) / 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let l = (max + min) / 2;

  l = Math.max(0, Math.min(1, l + percent));

  const newR = Math.round(r * 255 * (1 + percent));
  const newG = Math.round(g * 255 * (1 + percent));
  const newB = Math.round(b * 255 * (1 + percent));

  return `#${newR.toString(16).padStart(2, "0")}${newG.toString(16).padStart(2, "0")}${newB.toString(16).padStart(2, "0")}`;
}

// ── Config complète par module ─────────────────────────────────────
export const THEME_CONFIG = {
  dashboard: {
    name: "Tableau de bord",
    base: MODULE_COLOR_MAP.dashboard,
    variants: generateColorVariants(MODULE_COLOR_MAP.dashboard),
  },
  commerciale: {
    name: "Gestion commerciale",
    base: MODULE_COLOR_MAP.commerciale,
    variants: generateColorVariants(MODULE_COLOR_MAP.commerciale),
  },
  stocks: {
    name: "Stocks & Logistique",
    base: MODULE_COLOR_MAP.stocks,
    variants: generateColorVariants(MODULE_COLOR_MAP.stocks),
  },
  logistique: {
    name: "Stocks & Logistique",
    base: MODULE_COLOR_MAP.logistique,
    variants: generateColorVariants(MODULE_COLOR_MAP.logistique),
  },
  finances: {
    name: "Finances",
    base: MODULE_COLOR_MAP.finances,
    variants: generateColorVariants(MODULE_COLOR_MAP.finances),
  },
  comptabilite: {
    name: "Finances",
    base: MODULE_COLOR_MAP.comptabilite,
    variants: generateColorVariants(MODULE_COLOR_MAP.comptabilite),
  },
  rh: {
    name: "Ressources Humaines",
    base: MODULE_COLOR_MAP.rh,
    variants: generateColorVariants(MODULE_COLOR_MAP.rh),
  },
  "ressources-humaines": {
    name: "Ressources Humaines",
    base: MODULE_COLOR_MAP["ressources-humaines"],
    variants: generateColorVariants(MODULE_COLOR_MAP["ressources-humaines"]),
  },
  achats: {
    name: "Achats & Approvisionnements",
    base: MODULE_COLOR_MAP.achats,
    variants: generateColorVariants(MODULE_COLOR_MAP.achats),
  },
  approvisionnements: {
    name: "Achats & Approvisionnements",
    base: MODULE_COLOR_MAP.approvisionnements,
    variants: generateColorVariants(MODULE_COLOR_MAP.approvisionnements),
  },
  crm: {
    name: "CRM",
    base: MODULE_COLOR_MAP.crm,
    variants: generateColorVariants(MODULE_COLOR_MAP.crm),
  },
  admin: {
    name: "Administration",
    base: MODULE_COLOR_MAP.admin,
    variants: generateColorVariants(MODULE_COLOR_MAP.admin),
  },
  parametres: {
    name: "Paramètres",
    base: MODULE_COLOR_MAP.parametres,
    variants: generateColorVariants(MODULE_COLOR_MAP.parametres),
  },
};

// ── Détecter module depuis URL ─────────────────────────────────────
export function getModuleFromPath(pathname) {
  const path = pathname.toLowerCase().trim("/");

  // Routes dashboard
  if (
    path === "" ||
    path === "dashboard" ||
    path.startsWith("dashboard/") ||
    path === "bi-analytics"
  ) {
    return "dashboard";
  }

  // Routes gestion commerciale
  if (
    path.startsWith("clients") ||
    path.startsWith("commandes") ||
    path.startsWith("factures") ||
    path.startsWith("paiements") ||
    path.startsWith("devis") ||
    path.startsWith("proformas") ||
    path.startsWith("notifications") ||
    path.startsWith("workflow")
  ) {
    return "commerciale";
  }

  // Routes stocks & logistique
  if (
    path.startsWith("produits") ||
    path.startsWith("stock") ||
    path.startsWith("inventaire") ||
    path.startsWith("bons-livraison") ||
    path.startsWith("bons-retour") ||
    path.startsWith("colis") ||
    path.startsWith("expeditions") ||
    path.startsWith("ordres-colisage") ||
    path.startsWith("logistique") ||
    path.startsWith("livraisons-directes") ||
    path.startsWith("incidents") ||
    path.startsWith("fleet") ||
    path.startsWith("logistics-costs")
  ) {
    return "stocks";
  }

  // Routes finances & comptabilité
  if (
    path.startsWith("comptabilite") ||
    path.startsWith("rapports") ||
    path.startsWith("analytics") ||
    path.startsWith("fne") ||
    path.startsWith("etat-compte-clients")
  ) {
    return "finances";
  }

  // Routes RH
  if (
    path.startsWith("employes") ||
    path.startsWith("departements") ||
    path.startsWith("fonctions") ||
    path.startsWith("categories-pro") ||
    path.startsWith("contrats") ||
    path.startsWith("conges") ||
    path.startsWith("absences") ||
    path.startsWith("missions") ||
    path.startsWith("evaluations") ||
    path.startsWith("paie") ||
    path.startsWith("rh-dashboard") ||
    path.startsWith("rapports-rh")
  ) {
    return "rh";
  }

  // Routes achats & approvisionnements
  if (
    path.startsWith("fournisseurs") ||
    path.startsWith("approvisionnements")
  ) {
    return "achats";
  }

  // Routes admin
  if (
    path.startsWith("utilisateurs") ||
    path.startsWith("parametres") ||
    path.startsWith("documents") ||
    path.startsWith("backup") ||
    path.startsWith("file-storage") ||
    path.startsWith("historique-envois")
  ) {
    return "admin";
  }

  // Default
  return "dashboard";
}

// ── Utilitaire : obtenir couleur pour un chemin ───────────────────
export function getThemeForPath(pathname) {
  const module = getModuleFromPath(pathname);
  return THEME_CONFIG[module] || THEME_CONFIG.dashboard;
}
