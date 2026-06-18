/**
 * LogistiqueHub.jsx — Hub centralisé pour tous les modules logistique
 *
 * Regroupe sous une interface unifiée :
 *   - Missions logistique
 *   - Ordres de colisage + Colis
 *   - Expéditions
 *   - Livraisons directes
 *   - Incidents
 *   - Flotte (Fleet)
 *   - Coûts logistiques
 *
 * Remplace les entrées sidebar dispersées par un point d'entrée unique.
 */
import { useState, Suspense, lazy } from "react";
import {
  Truck, Package, AlertTriangle, Car, DollarSign,
  MapPin, PackageOpen, ArrowRightLeft, Loader2
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/layout/PageHeader";

// Chargement lazy des sous-modules existants
const Logistique        = lazy(() => import("./Logistique"));
const OrdresColisage    = lazy(() => import("./OrdresColisage"));
const Expeditions       = lazy(() => import("./Expeditions"));
const LivraisonsDirectes = lazy(() => import("./LivraisonsDirectes"));
const Incidents         = lazy(() => import("./Incidents"));
const Fleet             = lazy(() => import("./Fleet"));
const LogisticsCosts    = lazy(() => import("./LogisticsCosts"));

// ── Définition des onglets ─────────────────────────────────────────────────────

const TABS = [
  {
    key: "missions",
    label: "Missions",
    icon: Truck,
    component: Logistique,
    description: "Planification et suivi des missions de livraison",
    roles: ["super_admin", "gestionnaire_stock", "responsable_magasinier", "service_logistique", "directeur_commercial"],
  },
  {
    key: "colisage",
    label: "Colisage",
    icon: PackageOpen,
    component: OrdresColisage,
    description: "Ordres de colisage et préparation des colis",
    roles: ["super_admin", "gestionnaire_stock", "responsable_magasinier", "service_logistique"],
  },
  {
    key: "expeditions",
    label: "Expéditions",
    icon: ArrowRightLeft,
    component: Expeditions,
    description: "Suivi des expéditions sortantes",
    roles: ["super_admin", "responsable_magasinier", "service_logistique"],
  },
  {
    key: "livraisons",
    label: "Livraisons directes",
    icon: MapPin,
    component: LivraisonsDirectes,
    description: "Livraisons directes sans expédition",
    roles: ["super_admin", "gestionnaire_stock", "responsable_magasinier", "service_logistique"],
  },
  {
    key: "incidents",
    label: "Incidents",
    icon: AlertTriangle,
    component: Incidents,
    description: "Gestion des incidents de livraison",
    roles: ["super_admin", "gestionnaire_stock", "responsable_magasinier", "service_logistique"],
  },
  {
    key: "flotte",
    label: "Flotte",
    icon: Car,
    component: Fleet,
    description: "Gestion du parc de véhicules",
    roles: ["super_admin", "service_logistique"],
  },
  {
    key: "couts",
    label: "Coûts",
    icon: DollarSign,
    component: LogisticsCosts,
    description: "Analyse des coûts et rentabilité logistique",
    roles: ["super_admin", "comptable", "service_logistique"],
  },
];

// ── Composant de chargement ────────────────────────────────────────────────────

function TabLoader() {
  return (
    <div className="flex items-center justify-center py-20 text-slate-400">
      <Loader2 className="w-6 h-6 animate-spin mr-2" />
      <span className="text-sm">Chargement...</span>
    </div>
  );
}

// ── Composant principal ────────────────────────────────────────────────────────

export default function LogistiqueHub() {
  const { role } = useAuth();
  const [activeTab, setActiveTab] = useState("missions");

  // Filtrer les onglets selon le rôle
  const visibleTabs = TABS.filter(
    (t) => !t.roles || t.roles.includes(role)
  );

  // Si l'onglet actif n'est plus accessible, revenir au premier
  const currentTab =
    visibleTabs.find((t) => t.key === activeTab) || visibleTabs[0];

  if (!currentTab) {
    return (
      <DashboardLayout>
        <PageHeader title="Logistique" subtitle="Accès non autorisé" icon={Truck} />
        <div className="p-8 text-center text-slate-400">
          Vous n'avez pas accès aux modules logistique.
        </div>
      </DashboardLayout>
    );
  }

  const ActiveComponent = currentTab.component;

  return (
    <DashboardLayout>
      {/* En-tête hub */}
      <div className="px-6 pt-6 pb-0">
        <PageHeader
          title="Hub Logistique"
          subtitle="Gestion centralisée des opérations logistiques"
          icon={Truck}
        />

        {/* Onglets */}
        <div className="flex flex-wrap gap-1 mt-4 border-b border-slate-200 pb-0">
          {visibleTabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = tab.key === currentTab.key;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={[
                  "flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium",
                  "rounded-t-lg border-b-2 transition-all duration-150",
                  "focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500",
                  isActive
                    ? "border-blue-600 text-blue-700 bg-blue-50"
                    : "border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50",
                ].join(" ")}
                title={tab.description}
                aria-selected={isActive}
              >
                <Icon
                  className={`w-4 h-4 ${isActive ? "text-blue-600" : "text-slate-400"}`}
                />
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Description de l'onglet actif */}
      <div className="px-6 pt-3 pb-1">
        <p className="text-xs text-slate-400">{currentTab.description}</p>
      </div>

      {/* Contenu de l'onglet — les sous-composants gèrent leur propre layout */}
      <div className="logistique-hub-content">
        <Suspense fallback={<TabLoader />}>
          <ActiveComponent hubMode={true} />
        </Suspense>
      </div>
    </DashboardLayout>
  );
}
