// EDITIONS FABS-CI — Matrice d'accès rôle → modules
// Conforme au ERP FABS-CI V10 ENTERPRISE — PROMPT MAÎTRE UNIFIÉ
//
// 10 rôles officiels (ordre hiérarchique) :
//   super_admin · directeur_general · comptable · directeur_commercial
//   gestionnaire_stock · responsable_magasinier · secretariat · assistante
//   service_logistique · assistante_commerciale

export const MODULES = [
  // 📊 TABLEAU DE BORD
  { key: "dashboard",            path: "/dashboard",            label: "Tableau de bord",        icon: "LayoutDashboard", group: "Tableau de bord" },
  { key: "bi-analytics",         path: "/bi-analytics",         label: "Business Intelligence", icon: "BarChart3",       group: "Tableau de bord" },
  { key: "rapports",             path: "/rapports",             label: "Rapports",               icon: "BarChart3",       group: "Tableau de bord" },

  // 👥 GESTION COMMERCIALE
  { key: "clients",              path: "/clients",              label: "Clients",                icon: "Users",           group: "Gestion commerciale" },
  { key: "commandes",            path: "/commandes",            label: "Commandes",              icon: "ShoppingCart",    group: "Gestion commerciale" },
  { key: "proformas",            path: "/proformas",            label: "Proformas",              icon: "FileSignature",   group: "Gestion commerciale" },
  { key: "factures",             path: "/factures",             label: "Factures",               icon: "FileText",        group: "Gestion commerciale" },
  { key: "paiements",            path: "/paiements",            label: "Paiements",              icon: "CreditCard",      group: "Gestion commerciale" },
  { key: "livraisons",           path: "/livraisons",           label: "Livraisons",             icon: "Truck",           group: "Gestion commerciale" },
  { key: "retours",              path: "/retours",              label: "Retours",                icon: "RotateCcw",       group: "Gestion commerciale" },
  { key: "colis",                path: "/colis",                label: "Colis",                  icon: "Package",         group: "Gestion commerciale" },
  { key: "expeditions",          path: "/expeditions",          label: "Expéditions",           icon: "Truck",           group: "Gestion commerciale" },

  // 📦 STOCKS & LOGISTIQUE
  { key: "produits",             path: "/produits",             label: "Produits",               icon: "BookOpen",        group: "Stocks & Logistique" },
  { key: "stock",                path: "/stock",                label: "Stock",                  icon: "Package",         group: "Stocks & Logistique" },
  { key: "logistique",           path: "/logistique",           label: "Logistique",            icon: "Truck",           group: "Stocks & Logistique" },
  { key: "fleet",                path: "/fleet",                label: "Flotte",                 icon: "Car",             group: "Stocks & Logistique" },
  { key: "logistics-costs",      path: "/logistics-costs",      label: "Coûts Logistiques",     icon: "DollarSign",      group: "Stocks & Logistique" },
  { key: "fournisseurs",         path: "/fournisseurs",         label: "Fournisseurs",           icon: "Building2",       group: "Stocks & Logistique" },
  { key: "approvisionnements",   path: "/approvisionnements",   label: "Approvisionnements",     icon: "Inbox",           group: "Stocks & Logistique" },

  // 💰 FINANCES
  { key: "comptabilite",         path: "/comptabilite",         label: "Comptabilité",          icon: "Calculator",      group: "Finances" },
  { key: "comptabilite-avancee", path: "/comptabilite-avancee", label: "Comptabilité Avancée", icon: "Calculator",      group: "Finances" },
  { key: "fne",                  path: "/fne",                  label: "FNE",                    icon: "ShieldCheck",     group: "Finances" },

  // 👨‍💼 RESSOURCES HUMAINES
  { key: "rh-employes",          path: "/rh/employes",          label: "Employés",               icon: "Users",           group: "Ressources Humaines" },
  { key: "rh-departements",      path: "/rh/departements",      label: "Départements",           icon: "Building2",       group: "Ressources Humaines" },
  { key: "rh-fonctions",         path: "/rh/fonctions",         label: "Fonctions",              icon: "Briefcase",       group: "Ressources Humaines" },
  { key: "rh-contrats",          path: "/rh/contrats",          label: "Contrats",               icon: "FileText",        group: "Ressources Humaines" },
  { key: "rh-conges",            path: "/rh/conges",            label: "Congés",                 icon: "CalendarDays",    group: "Ressources Humaines" },
  { key: "rh-absences",          path: "/rh/absences",          label: "Absences",               icon: "UserX",           group: "Ressources Humaines" },
  { key: "rh-missions",          path: "/rh/missions",          label: "Missions",               icon: "MapPin",          group: "Ressources Humaines" },
  { key: "rh-evaluations",       path: "/rh/evaluations",       label: "Évaluations",            icon: "Star",            group: "Ressources Humaines" },
  { key: "rh-rapports",          path: "/rh/rapports",          label: "Rapports RH",            icon: "BarChart3",       group: "Ressources Humaines" },
  { key: "rh-paie",              path: "/rh/paie",              label: "Paie",                   icon: "Wallet",          group: "Ressources Humaines" },

  // 🔔 NOTIFICATIONS
  { key: "notifications",        path: "/notifications",        label: "Notifications",          icon: "Bell",            group: "Notifications" },

  // 📁 DOCUMENTS & SAUVEGARDES
  { key: "file-storage",         path: "/file-storage",         label: "File Storage",           icon: "HardDrive",       group: "Documents & Sauvegardes" },
  { key: "backup",               path: "/backup",               label: "Backup",                 icon: "Database",        group: "Documents & Sauvegardes" },

  // ⚙️ ADMINISTRATION
  { key: "utilisateurs",         path: "/utilisateurs",         label: "Utilisateurs",           icon: "UserCog",         group: "Administration" },
  { key: "parametres",           path: "/parametres",           label: "Paramètres",            icon: "Settings",        group: "Administration" },
  { key: "documents-impression", path: "/parametres/documents-impression", label: "Documents & Impression", icon: "Printer", group: "Administration" },

  // Workflow Approvals (mentionné dans la matrice RBAC V10)
  { key: "workflow-approvals",   path: "/workflow-approvals",   label: "Workflow Approvals",     icon: "FileCheck",       group: "Administration" },
];

// ─────────────────────────────────────────────────────────────────
// Matrice des permissions (1 = autorisé, 0 = refusé)
// Source de vérité : ERP FABS-CI V10 — Matrice des Permissions
// ─────────────────────────────────────────────────────────────────
export const PERMISSIONS = {
  // 📊 TABLEAU DE BORD
  dashboard:                  { super_admin: 1, directeur_general: 1, comptable: 1, directeur_commercial: 1, gestionnaire_stock: 1, responsable_magasinier: 1, secretariat: 1, assistante: 0, service_logistique: 1, assistante_commerciale: 0 },
  "bi-analytics":             { super_admin: 1, directeur_general: 1, comptable: 0, directeur_commercial: 0, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 0, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },
  rapports:                   { super_admin: 1, directeur_general: 1, comptable: 1, directeur_commercial: 1, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 0, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },

  // 👥 GESTION COMMERCIALE
  clients:                    { super_admin: 1, directeur_general: 1, comptable: 1, directeur_commercial: 1, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 1, assistante: 1, service_logistique: 0, assistante_commerciale: 1 },
  commandes:                  { super_admin: 1, directeur_general: 1, comptable: 1, directeur_commercial: 1, gestionnaire_stock: 1, responsable_magasinier: 1, secretariat: 1, assistante: 1, service_logistique: 0, assistante_commerciale: 1 },
  // Proformas : phase pré-commerciale → mêmes accès que clients/commandes (READ_ROLES backend = super_admin, DG, dir_com, comptable, secretariat)
  proformas:                  { super_admin: 1, directeur_general: 1, comptable: 1, directeur_commercial: 1, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 1, assistante: 1, service_logistique: 0, assistante_commerciale: 1 },
  factures:                   { super_admin: 1, directeur_general: 1, comptable: 1, directeur_commercial: 0, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 0, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },
  paiements:                  { super_admin: 1, directeur_general: 1, comptable: 1, directeur_commercial: 0, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 0, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },
  livraisons:                 { super_admin: 1, directeur_general: 1, comptable: 1, directeur_commercial: 1, gestionnaire_stock: 1, responsable_magasinier: 1, secretariat: 0, assistante: 0, service_logistique: 1, assistante_commerciale: 0 },
  retours:                    { super_admin: 1, directeur_general: 1, comptable: 0, directeur_commercial: 1, gestionnaire_stock: 1, responsable_magasinier: 1, secretariat: 0, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },
  colis:                      { super_admin: 1, directeur_general: 1, comptable: 0, directeur_commercial: 1, gestionnaire_stock: 1, responsable_magasinier: 1, secretariat: 0, assistante: 0, service_logistique: 1, assistante_commerciale: 0 },
  expeditions:                { super_admin: 1, directeur_general: 1, comptable: 0, directeur_commercial: 1, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 0, assistante: 0, service_logistique: 1, assistante_commerciale: 0 },

  // 📦 STOCKS & LOGISTIQUE
  // Note V10 : Assistante voit Produits mais en prix de vente uniquement (👁*)
  produits:                   { super_admin: 1, directeur_general: 1, comptable: 0, directeur_commercial: 1, gestionnaire_stock: 1, responsable_magasinier: 0, secretariat: 0, assistante: 1, service_logistique: 0, assistante_commerciale: 0 },
  stock:                      { super_admin: 1, directeur_general: 1, comptable: 0, directeur_commercial: 0, gestionnaire_stock: 1, responsable_magasinier: 0, secretariat: 0, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },
  logistique:                 { super_admin: 1, directeur_general: 1, comptable: 0, directeur_commercial: 1, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 0, assistante: 0, service_logistique: 1, assistante_commerciale: 0 },
  fleet:                      { super_admin: 1, directeur_general: 1, comptable: 0, directeur_commercial: 0, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 0, assistante: 0, service_logistique: 1, assistante_commerciale: 0 },
  "logistics-costs":          { super_admin: 1, directeur_general: 1, comptable: 1, directeur_commercial: 0, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 0, assistante: 0, service_logistique: 1, assistante_commerciale: 0 },
  fournisseurs:               { super_admin: 1, directeur_general: 1, comptable: 0, directeur_commercial: 0, gestionnaire_stock: 1, responsable_magasinier: 0, secretariat: 0, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },
  approvisionnements:         { super_admin: 1, directeur_general: 1, comptable: 0, directeur_commercial: 0, gestionnaire_stock: 1, responsable_magasinier: 0, secretariat: 0, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },

  // 💰 FINANCES
  comptabilite:               { super_admin: 1, directeur_general: 1, comptable: 1, directeur_commercial: 0, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 0, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },
  "comptabilite-avancee":     { super_admin: 1, directeur_general: 0, comptable: 1, directeur_commercial: 0, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 0, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },
  fne:                        { super_admin: 1, directeur_general: 1, comptable: 1, directeur_commercial: 0, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 0, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },

  // 👨‍💼 RESSOURCES HUMAINES
  "rh-employes":              { super_admin: 1, directeur_general: 1, comptable: 1, directeur_commercial: 1, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 1, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },
  "rh-departements":         { super_admin: 1, directeur_general: 1, comptable: 1, directeur_commercial: 1, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 1, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },
  "rh-fonctions":             { super_admin: 1, directeur_general: 1, comptable: 1, directeur_commercial: 1, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 1, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },
  "rh-contrats":              { super_admin: 1, directeur_general: 1, comptable: 1, directeur_commercial: 0, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 1, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },
  "rh-conges":                { super_admin: 1, directeur_general: 1, comptable: 1, directeur_commercial: 1, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 1, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },
  "rh-absences":              { super_admin: 1, directeur_general: 1, comptable: 1, directeur_commercial: 1, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 1, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },
  "rh-missions":              { super_admin: 1, directeur_general: 1, comptable: 1, directeur_commercial: 1, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 1, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },
  "rh-evaluations":           { super_admin: 1, directeur_general: 1, comptable: 1, directeur_commercial: 1, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 0, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },
  "rh-rapports":              { super_admin: 1, directeur_general: 1, comptable: 1, directeur_commercial: 1, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 0, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },
  "rh-paie":                  { super_admin: 1, directeur_general: 1, comptable: 1, directeur_commercial: 0, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 0, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },

  // 🔔 NOTIFICATIONS (tous les rôles)
  notifications:              { super_admin: 1, directeur_general: 1, comptable: 1, directeur_commercial: 1, gestionnaire_stock: 1, responsable_magasinier: 1, secretariat: 1, assistante: 1, service_logistique: 1, assistante_commerciale: 1 },

  // 📁 DOCUMENTS & SAUVEGARDES
  "file-storage":             { super_admin: 1, directeur_general: 0, comptable: 0, directeur_commercial: 0, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 0, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },
  backup:                     { super_admin: 1, directeur_general: 0, comptable: 0, directeur_commercial: 0, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 0, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },

  // ⚙️ ADMINISTRATION
  utilisateurs:               { super_admin: 1, directeur_general: 0, comptable: 0, directeur_commercial: 0, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 0, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },
  parametres:                 { super_admin: 1, directeur_general: 0, comptable: 0, directeur_commercial: 0, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 0, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },
  "documents-impression":     { super_admin: 1, directeur_general: 0, comptable: 0, directeur_commercial: 0, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 0, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },

  // Workflow Approvals (matrice RBAC V10 — Super Admin, DG, Comptable)
  "workflow-approvals":       { super_admin: 1, directeur_general: 1, comptable: 0, directeur_commercial: 0, gestionnaire_stock: 0, responsable_magasinier: 0, secretariat: 0, assistante: 0, service_logistique: 0, assistante_commerciale: 0 },
};

// Liste officielle des 10 rôles V10
export const ROLES = [
  "super_admin",
  "directeur_general",
  "comptable",
  "directeur_commercial",
  "gestionnaire_stock",
  "responsable_magasinier",
  "secretariat",
  "assistante",
  "service_logistique",
  "assistante_commerciale",
];

export const ROLE_LABELS = {
  super_admin:             "Super Administrateur",
  directeur_general:       "Directeur Général",
  comptable:               "Comptable",
  directeur_commercial:    "Directeur Commercial",
  gestionnaire_stock:      "Gestionnaire de Stock",
  responsable_magasinier:  "Responsable Magasinier",
  secretariat:             "Secrétariat",
  assistante:              "Assistante",
  service_logistique:      "Service Logistique",
  assistante_commerciale:  "Assistante Commerciale",
};

/**
 * Vérifie si un rôle peut accéder à un module.
 * @param {string} role - Le rôle de l'utilisateur (parmi ROLES)
 * @param {string} moduleKey - La clé du module (parmi MODULES)
 * @returns {boolean}
 */
export function can(role, moduleKey) {
  if (!role || !moduleKey) return false;
  return PERMISSIONS[moduleKey]?.[role] === 1;
}

/**
 * Retourne les modules visibles pour un rôle donné.
 * @param {string} role
 * @returns {Array}
 */
export function visibleModulesFor(role) {
  return MODULES.filter((m) => can(role, m.key));
}

/**
 * Retourne les modules visibles pour un rôle, groupés par section.
 * @param {string} role
 * @returns {Object} { groupName: [modules] }
 */
export function visibleModulesGroupedFor(role) {
  const visible = visibleModulesFor(role);
  return visible.reduce((acc, m) => {
    const g = m.group || "Autre";
    if (!acc[g]) acc[g] = [];
    acc[g].push(m);
    return acc;
  }, {});
}
