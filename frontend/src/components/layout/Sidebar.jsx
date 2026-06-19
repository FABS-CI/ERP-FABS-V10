import { useState, useEffect, useMemo } from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  LayoutDashboard, Users, BookOpen, ShoppingCart, FileText, FileSignature,
  CreditCard, Truck, RotateCcw, Package, Calculator, BarChart3, UserCog,
  Settings, X, Bell, Car, DollarSign, MessageSquare, FileCheck, HardDrive,
  Database, Building2, Inbox, ShieldCheck, Printer, ChevronDown,
  Wallet, Warehouse, Briefcase, FolderArchive, Shield, Star,
  CalendarDays, UserX, MapPin,
} from "lucide-react";
import Logo from "../Logo";
import { visibleModulesGroupedFor } from "../../constants/permissions";
import { useAuth } from "../../hooks/useAuth";

const ICONS = {
  LayoutDashboard, Users, BookOpen, ShoppingCart, FileText, FileSignature, CreditCard,
  Truck, RotateCcw, Package, Calculator, BarChart3, UserCog, Settings, Bell, Car,
  DollarSign, MessageSquare, FileCheck, HardDrive, Database,
  Building2, Inbox, ShieldCheck, Printer, Wallet, Briefcase, Star,
  CalendarDays, UserX, MapPin,
};

/* ── Config modules — palette maquette ─────────────────────────────────── */
const GROUP_CONFIG = [
  {
    name:    "Tableau de bord",
    label:   "Tableau de bord",
    icon:    LayoutDashboard,
    color:   "#3B82F6",
    light:   "rgba(59,130,246,0.12)",
    grad:    "linear-gradient(90deg,#3B82F6,#60A5FA)",
    shadow:  "rgba(59,130,246,0.3)",
  },
  {
    name:    "Gestion commerciale",
    label:   "Gestion commerciale",
    icon:    ShoppingCart,
    color:   "#F97316",
    light:   "rgba(249,115,22,0.12)",
    grad:    "linear-gradient(90deg,#F97316,#FB923C)",
    shadow:  "rgba(249,115,22,0.3)",
  },
  {
    name:    "Stocks & Logistique",
    label:   "Stocks & logistique",
    icon:    Warehouse,
    color:   "#10B981",
    light:   "rgba(16,185,129,0.12)",
    grad:    "linear-gradient(90deg,#10B981,#34D399)",
    shadow:  "rgba(16,185,129,0.3)",
  },
  {
    name:    "Finances",
    label:   "Finances",
    icon:    Wallet,
    color:   "#14B8A6",
    light:   "rgba(20,184,166,0.12)",
    grad:    "linear-gradient(90deg,#14B8A6,#2DD4BF)",
    shadow:  "rgba(20,184,166,0.3)",
  },
  {
    name:    "Ressources Humaines",
    label:   "Ressources humaines",
    icon:    Briefcase,
    color:   "#8B5CF6",
    light:   "rgba(139,92,246,0.12)",
    grad:    "linear-gradient(90deg,#8B5CF6,#A78BFA)",
    shadow:  "rgba(139,92,246,0.3)",
  },
  {
    name:    "Notifications",
    label:   "Notifications",
    icon:    Bell,
    color:   "#EF4444",
    light:   "rgba(239,68,68,0.12)",
    grad:    "linear-gradient(90deg,#EF4444,#F87171)",
    shadow:  "rgba(239,68,68,0.3)",
  },
  {
    name:    "Documents & Sauvegardes",
    label:   "Documents & sauvegardes",
    icon:    FolderArchive,
    color:   "#F59E0B",
    light:   "rgba(245,158,11,0.12)",
    grad:    "linear-gradient(90deg,#F59E0B,#FBBF24)",
    shadow:  "rgba(245,158,11,0.3)",
  },
  {
    name:    "Administration",
    label:   "Administration",
    icon:    Shield,
    color:   "#6366F1",
    light:   "rgba(99,102,241,0.12)",
    grad:    "linear-gradient(90deg,#6366F1,#818CF8)",
    shadow:  "rgba(99,102,241,0.3)",
  },
];

const LS_KEY = "fabs.sidebar.open";

export default function Sidebar({ mobileOpen = false, onMobileClose }) {
  const { role } = useAuth();
  const location = useLocation();
  const grouped = useMemo(() => visibleModulesGroupedFor(role), [role]);

  /* ── Favoris ─────────────────────────────────────────────────────────── */
  const [favs, setFavs] = useState(() => {
    try { return JSON.parse(localStorage.getItem("fabs.favs") || "[]"); }
    catch { return []; }
  });
  useEffect(() => {
    const refresh = () => {
      try { setFavs(JSON.parse(localStorage.getItem("fabs.favs") || "[]")); }
      catch { setFavs([]); }
    };
    window.addEventListener("fabs.favs.update", refresh);
    window.addEventListener("storage", refresh);
    return () => {
      window.removeEventListener("fabs.favs.update", refresh);
      window.removeEventListener("storage", refresh);
    };
  }, []);
  const removeFav = (key) => {
    const next = favs.filter((f) => f.key !== key);
    localStorage.setItem("fabs.favs", JSON.stringify(next));
    setFavs(next);
    window.dispatchEvent(new Event("fabs.favs.update"));
  };

  /* ── Groupe actif ────────────────────────────────────────────────────── */
  // Match précis : un module est actif si le chemin courant est égal à son path
  // ou s'il commence par "<path>/" (sous-page). On évite ainsi qu'un chemin comme
  // "/livraisons-directes" matche par erreur le module "/livraisons".
  const pathMatches = (current, path) =>
    current === path || current.startsWith(path + "/");

  const activeGroup = useMemo(() => {
    // On garde le module dont le path est le plus long parmi ceux qui matchent
    // (le plus spécifique gagne).
    let bestGroup = null;
    let bestLen = -1;
    for (const g of GROUP_CONFIG) {
      const items = grouped[g.name] || [];
      for (const m of items) {
        if (pathMatches(location.pathname, m.path) && m.path.length > bestLen) {
          bestLen = m.path.length;
          bestGroup = g.name;
        }
      }
    }
    return bestGroup;
  }, [grouped, location.pathname]);

  const activeGroupCfg = useMemo(
    () => GROUP_CONFIG.find((g) => g.name === activeGroup) || null,
    [activeGroup]
  );

  /* ── Accordéon ───────────────────────────────────────────────────────── */
  const [openGroup, setOpenGroup] = useState(() => {
    try { return localStorage.getItem(LS_KEY) || activeGroup; }
    catch { return activeGroup; }
  });

  useEffect(() => {
    if (activeGroup) {
      setOpenGroup(activeGroup);
      try { localStorage.setItem(LS_KEY, activeGroup); } catch {}
    }
  }, [activeGroup]);

  const toggleGroup = (name) => {
    setOpenGroup((cur) => {
      const next = cur === name ? null : name;
      try { localStorage.setItem(LS_KEY, next || ""); } catch {}
      return next;
    });
  };

  return (
    <>
      {/* Backdrop mobile */}
      {mobileOpen && (
        <button
          aria-label="Fermer le menu"
          onClick={onMobileClose}
          className="fixed inset-0 z-30 md:hidden"
          style={{ background: "rgba(0,0,0,0.7)" }}
          data-testid="sidebar-backdrop"
        />
      )}

      {/* Styles pour survol — injection CSS propre */}
      <style>{`
        .sidebar-item-hover {
          transition: all 0.15s ease;
        }
        .sidebar-item-hover:hover:not(.active) {
          color: #FFFFFF !important;
          border-radius: 10px !important;
        }
      `}</style>

      <aside
        data-testid="sidebar"
        className={`w-64 fixed inset-y-0 left-0 z-40 flex flex-col transition-transform duration-300 md:translate-x-0 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
        style={{
          background: "#111827",
          borderRight: "1px solid rgba(255,255,255,0.06)",
        }}
      >
        {/* ── En-tête ───────────────────────────────────────────────────── */}
        <div
          className="px-4 py-4 flex items-center justify-between"
          style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
        >
          <div className="flex-1 flex flex-col items-center gap-2">
            <Logo variant="dark" size="sm" />
            <span
              style={{
                fontSize: "11px",
                fontWeight: 600,
                color: "#94A3B8",
                letterSpacing: "0.06em",
              }}
            >
              Editions FABS-CI
            </span>
            {/* Indicateur module actif */}
            <div
              style={{
                height: "2px",
                width: "40px",
                borderRadius: "99px",
                background: activeGroupCfg ? activeGroupCfg.grad : "rgba(255,255,255,0.1)",
                transition: "background 0.4s ease",
              }}
            />
          </div>
          <button
            onClick={onMobileClose}
            aria-label="Fermer le menu"
            className="md:hidden p-1.5 rounded-lg"
            style={{ color: "#94A3B8" }}
            data-testid="sidebar-close-mobile"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* ── Navigation ────────────────────────────────────────────────── */}
        <nav className="flex-1 overflow-y-auto py-3 px-2.5">

          {/* Favoris */}
          {favs.length > 0 && (
            <div
              className="mb-3 pb-2"
              style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
              data-testid="sidebar-favs"
            >
              <div
                className="flex items-center gap-2 px-3 py-1 mb-1"
                style={{
                  fontSize: "10px", fontWeight: 600,
                  color: "rgba(255,255,255,0.3)",
                  letterSpacing: "0.08em",
                }}
              >
                <Star className="w-3 h-3" style={{ color: "#F97316", fill: "#F97316" }} />
                Favoris
              </div>
              <ul className="space-y-0.5">
                {favs.map((f) => {
                  const isActive = location.pathname === f.path;
                  return (
                    <li key={f.key} className="group flex items-center gap-1">
                      <NavLink
                        to={f.path}
                        data-testid={`fav-${f.key}`}
                        onClick={onMobileClose}
                        className="flex-1 flex items-center gap-2 px-3 py-1.5 truncate transition-all duration-150"
                        style={{
                          fontSize: "13px", fontWeight: isActive ? 600 : 500,
                          color: isActive ? "#fff" : "#94A3B8",
                          background: isActive ? "linear-gradient(90deg,#F97316,#FB923C)" : "transparent",
                          boxShadow: isActive ? "0 2px 10px rgba(249,115,22,0.3)" : "none",
                          borderRadius: "10px",
                          textDecoration: "none",
                        }}
                      >
                        <Star className="w-3 h-3 shrink-0" style={{ color: isActive ? "#fff" : "#F97316", fill: isActive ? "#fff" : "#F97316" }} />
                        <span className="truncate">{f.label || f.path}</span>
                      </NavLink>
                      <button
                        type="button"
                        onClick={(e) => { e.preventDefault(); removeFav(f.key); }}
                        className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded"
                        style={{ color: "rgba(255,255,255,0.3)" }}
                        data-testid={`fav-remove-${f.key}`}
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}

          {/* Groupes */}
          <ul className="space-y-1">
            {GROUP_CONFIG.map((g) => {
              const items = grouped[g.name] || [];
              if (items.length === 0) return null;

              const isOpen = openGroup === g.name;
              const isGroupActive = activeGroup === g.name;
              const GroupIcon = g.icon;

              return (
                <li
                  key={g.name}
                  data-testid={`sidebar-group-${g.name.toLowerCase().replace(/[^a-z]/g, "-")}`}
                >
                  {/* Bouton module */}
                  <button
                    type="button"
                    onClick={() => toggleGroup(g.name)}
                    data-testid={`group-toggle-${g.name.toLowerCase().replace(/[^a-z]/g, "-")}`}
                    className="w-full flex items-center justify-between gap-2 text-left transition-all duration-200"
                    style={{
                      padding: "10px 12px",
                      borderRadius: "14px",
                      background: isGroupActive ? g.grad : "transparent",
                      boxShadow: isGroupActive ? `0 4px 14px ${g.shadow}` : "none",
                    }}
                    onMouseEnter={(e) => {
                      if (!isGroupActive) {
                        e.currentTarget.style.background = `${g.color}28`;
                        e.currentTarget.style.boxShadow = `0 4px 12px ${g.shadow}`;
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isGroupActive) {
                        e.currentTarget.style.background = "transparent";
                        e.currentTarget.style.boxShadow = "none";
                      }
                    }}
                  >
                    <span className="flex items-center gap-2.5 min-w-0">
                      {/* Icône */}
                      <span
                        className="flex items-center justify-center shrink-0 rounded-xl"
                        style={{
                          width: "32px", height: "32px",
                          backgroundColor: isGroupActive ? "rgba(255,255,255,0.18)" : g.light,
                          transition: "background 0.2s",
                        }}
                      >
                        <GroupIcon
                          style={{
                            width: "18px", height: "18px",
                            color: isGroupActive ? "#FFFFFF" : g.color,
                            transition: "color 0.2s",
                          }}
                        />
                      </span>
                      {/* Label */}
                      <span
                        className="truncate"
                        style={{
                          fontSize: "13.5px", fontWeight: 600,
                          color: isGroupActive ? "#FFFFFF" : "#E2E8F0",
                          letterSpacing: "0.01em",
                          transition: "color 0.2s",
                          lineHeight: 1.3,
                        }}
                      >
                        {g.label}
                      </span>
                    </span>
                    <ChevronDown
                      style={{
                        width: "14px", height: "14px", flexShrink: 0,
                        color: isGroupActive ? "rgba(255,255,255,0.7)" : "rgba(255,255,255,0.25)",
                        transform: isOpen ? "rotate(180deg)" : "rotate(0deg)",
                        transition: "transform 0.25s ease, color 0.2s",
                      }}
                    />
                  </button>

                  {/* Sous-menu */}
                  <div
                    style={{
                      overflow: "hidden",
                      maxHeight: isOpen ? "900px" : "0px",
                      opacity: isOpen ? 1 : 0,
                      transition: "max-height 0.3s cubic-bezier(0.4,0,0.2,1), opacity 0.22s ease",
                    }}
                  >
                    <ul
                      className="mt-1 mb-1 space-y-0.5"
                      style={{
                        marginLeft: "18px",
                        paddingLeft: "10px",
                        borderLeft: `2px solid ${g.color}30`,
                      }}
                    >
                      {items.map((m) => {
                        const Icon = ICONS[m.icon] || LayoutDashboard;
                        return (
                          <li key={m.key}>
                            <NavLink
                              to={m.path}
                              end={m.path === "/dashboard"}
                              data-testid={`nav-${m.key}`}
                              onClick={onMobileClose}
                              style={({ isActive }) => ({
                                display: "flex",
                                alignItems: "center",
                                gap: "8px",
                                padding: "7px 10px",
                                borderRadius: "10px",
                                fontSize: "13px",
                                fontWeight: isActive ? 600 : 400,
                                color: isActive ? "#FFFFFF" : "#94A3B8",
                                background: isActive ? g.grad : "transparent",
                                boxShadow: isActive ? `0 2px 10px ${g.shadow}` : "none",
                                transition: "all 0.15s",
                                textDecoration: "none",
                              })}
                              onMouseEnter={(e) => {
                                const isActive = e.currentTarget.getAttribute("aria-current") === "page";
                                if (!isActive) {
                                  // Fond teinté fort + accent latéral épais
                                  e.currentTarget.style.background = `${g.color}30`;
                                  e.currentTarget.style.color = "#FFFFFF";
                                  e.currentTarget.style.boxShadow = `inset 5px 0 0 ${g.color}`;
                                  e.currentTarget.style.borderRadius = "10px";
                                }
                              }}
                              onMouseLeave={(e) => {
                                const isActive = e.currentTarget.getAttribute("aria-current") === "page";
                                if (!isActive) {
                                  e.currentTarget.style.background = "transparent";
                                  e.currentTarget.style.color = "#94A3B8";
                                  e.currentTarget.style.boxShadow = "none";
                                }
                              }}
                            >
                              {({ isActive }) => (
                                <>
                                  <Icon
                                    style={{
                                      width: "15px", height: "15px", flexShrink: 0,
                                      color: isActive ? "#FFFFFF" : g.color,
                                      opacity: isActive ? 1 : 0.7,
                                    }}
                                  />
                                  <span className="truncate">{m.label}</span>
                                </>
                              )}
                            </NavLink>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* ── Pied ──────────────────────────────────────────────────────── */}
        <div
          className="px-4 py-3"
          style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}
        >
          {activeGroupCfg && (
            <div
              className="mb-2 rounded-full"
              style={{ height: "2px", background: activeGroupCfg.grad, opacity: 0.4 }}
            />
          )}
          <p style={{ fontSize: "11px", fontWeight: 600, color: "rgba(255,255,255,0.35)", letterSpacing: "0.04em" }}>
            Editions FABS-CI
          </p>
          <p style={{ fontSize: "10px", color: "rgba(255,255,255,0.2)" }}>
            Bingerville · ERP V10
          </p>
        </div>
      </aside>
    </>
  );
}

/* Export de styles spécifiques sidebar */
export const sidebarStyles = `
  .sidebar-nav-item {
    transition: background-color 0.15s, color 0.15s, box-shadow 0.15s;
  }
`;
