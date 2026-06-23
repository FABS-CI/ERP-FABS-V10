/**
 * Configuration thème — Module colors & metadata
 * 
 * Cette config est utilisée par :
 * - ThemeContext.jsx
 * - themeUtils.js
 * - Sidebar.jsx (pour afficher icônes module)
 */

export const MODULE_THEMES = {
  // ── Dashboard ──
  dashboard: {
    id: "dashboard",
    name: "Tableau de bord",
    description: "Vue d'ensemble, KPIs, Analytics",
    color: "#3B82F6",       // Bleu
    icon: "LayoutDashboard",
    routes: ["/", "/dashboard", "/bi-analytics"],
  },

  // ── Gestion Commerciale ──
  commerciale: {
    id: "commerciale",
    name: "Gestion Commerciale",
    description: "Clients, Commandes, Factures, Paiements",
    color: "#F97316",       // Orange
    icon: "ShoppingCart",
    routes: [
      "/clients",
      "/commandes",
      "/factures",
      "/paiements",
      "/devis",
      "/proformas",
      "/notifications",
    ],
  },

  // ── Stocks & Logistique ──
  stocks: {
    id: "stocks",
    name: "Stocks & Logistique",
    description: "Produits, Stock, Expeditions, Colis",
    color: "#10B981",       // Vert
    icon: "Warehouse",
    routes: [
      "/produits",
      "/stock",
      "/inventaire",
      "/bons-livraison",
      "/bons-retour",
      "/colis",
      "/expeditions",
      "/ordres-colisage",
      "/logistique",
      "/livraisons-directes",
      "/incidents",
      "/fleet",
      "/logistics-costs",
    ],
  },

  // ── Finances ──
  finances: {
    id: "finances",
    name: "Finances",
    description: "Comptabilité, FNE, Rapports, Analytiques",
    color: "#14B8A6",       // Teal
    icon: "Wallet",
    routes: [
      "/comptabilite",
      "/rapports",
      "/analytics",
      "/fne",
      "/etat-compte-clients",
    ],
  },

  // ── RH ──
  rh: {
    id: "rh",
    name: "Ressources Humaines",
    description: "Employés, Contrats, Congés, Paie",
    color: "#8B5CF6",       // Violet/Purple
    icon: "Briefcase",
    routes: [
      "/employes",
      "/departements",
      "/fonctions",
      "/categories-pro",
      "/contrats",
      "/conges",
      "/absences",
      "/missions",
      "/evaluations",
      "/paie",
      "/rh-dashboard",
      "/rapports-rh",
    ],
  },

  // ── Achats ──
  achats: {
    id: "achats",
    name: "Achats & Approvisionnements",
    description: "Fournisseurs, Approvisionnements",
    color: "#14B8A6",       // Teal (même que Finances)
    icon: "Briefcase",
    routes: ["/fournisseurs", "/approvisionnements"],
  },

  // ── Admin ──
  admin: {
    id: "admin",
    name: "Administration",
    description: "Paramètres, Utilisateurs, Documents, Backup",
    color: "#9CA3AF",       // Gris
    icon: "Shield",
    routes: [
      "/utilisateurs",
      "/parametres",
      "/documents",
      "/backup",
      "/file-storage",
      "/historique-envois",
    ],
  },
};

/**
 * Couleurs par statut/état (universelles, pas liées à un module)
 */
export const STATUS_COLORS = {
  success: "#10B981",       // Vert
  warning: "#F59E0B",       // Amber
  error: "#EF4444",         // Red
  info: "#3B82F6",          // Bleu
  pending: "#8B5CF6",       // Purple
  draft: "#9CA3AF",         // Gris
};

/**
 * Transitions de thème
 */
export const THEME_TRANSITION = {
  duration: 300,            // ms
  easing: "ease-in-out",
};

/**
 * Dark mode defaults
 */
export const DARK_MODE = {
  enabled: true,
  auto: true,               // Respecter préférence système
};
