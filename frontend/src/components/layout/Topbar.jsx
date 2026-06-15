import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { LogOut, ChevronDown, Bell, Search, Menu, Loader2, CheckCheck, Inbox } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import { useNotifications } from "../../hooks/useNotifications";
import { COMPANY, ROLES } from "../../constants/company";
import { rechercheGlobale } from "../../services/rechercheApi";

const TYPE_LABEL = {
  client: "Client",
  produit: "Produit",
  commande: "Commande",
  facture: "Facture",
  bon_livraison: "BL",
};

export default function Topbar({ onToggleSidebar }) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const userRef = useRef(null);
  const notifRef = useRef(null);
  const searchRef = useRef(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);

  useEffect(() => {
    const onClick = (e) => {
      if (userRef.current && !userRef.current.contains(e.target)) setOpen(false);
      if (notifRef.current && !notifRef.current.contains(e.target)) setNotifOpen(false);
      if (searchRef.current && !searchRef.current.contains(e.target)) setSearchOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  useEffect(() => {
    if (!searchQuery || searchQuery.length < 2) {
      setSearchResults([]);
      return;
    }
    setSearchLoading(true);
    const t = setTimeout(async () => {
      try {
        const data = await rechercheGlobale(searchQuery, 20);
        setSearchResults(data || []);
        setSearchOpen(true);
      } catch {
        setSearchResults([]);
      } finally {
        setSearchLoading(false);
      }
    }, 300);
    return () => clearTimeout(t);
  }, [searchQuery]);

  const handleSelectResult = (r) => {
    setSearchOpen(false);
    setSearchQuery("");
    navigate(r.url);
  };

  const {
    items: notifItems,
    count: notifCount,
    connected: notifConnected,
    markAsRead,
    markAllAsRead,
  } = useNotifications();

  if (!user) return null;

  const initials = (user.nom_complet || user.email || "?")
    .split(" ")
    .map((s) => s[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  const formatRelative = (iso) => {
    if (!iso) return "";
    const d = new Date(iso);
    const diffSec = Math.floor((Date.now() - d.getTime()) / 1000);
    if (diffSec < 60) return "à l'instant";
    if (diffSec < 3600) return `il y a ${Math.floor(diffSec / 60)} min`;
    if (diffSec < 86400) return `il y a ${Math.floor(diffSec / 3600)} h`;
    return d.toLocaleDateString("fr-FR", { day: "2-digit", month: "short" });
  };

  const typeBadgeColor = (type) => {
    switch (type) {
      case "success": return "#10B981";
      case "warning": return "#F59E0B";
      case "error":   return "#EF4444";
      default:        return "#3B82F6";
    }
  };

  return (
    <header
      data-testid="topbar"
      className="h-16 fixed top-0 right-0 left-0 md:left-64 z-20 flex items-center justify-between px-4 md:px-6"
      style={{
        background: "rgba(17,24,39,0.85)",
        backdropFilter: "blur(12px)",
        borderBottom: "1px solid rgba(255,255,255,0.07)",
      }}
    >
      {/* Left */}
      <div className="flex items-center gap-3">
        <button
          data-testid="topbar-toggle-sidebar"
          onClick={onToggleSidebar}
          aria-label="Ouvrir le menu"
          className="md:hidden p-2 rounded-xl transition-colors"
          style={{ color: "#E2E8F0" }}
          onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.08)"}
          onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
        >
          <Menu className="w-5 h-5" />
        </button>
        <span
          data-testid="topbar-school-year"
          className="hidden sm:inline-flex text-[11px] font-semibold px-3 py-1.5 rounded-lg"
          style={{
            background: "rgba(249,115,22,0.1)",
            color: "#F97316",
            border: "1px solid rgba(249,115,22,0.2)",
            letterSpacing: "0.06em",
          }}
        >
          {COMPANY.anneeScolaire}
        </span>
      </div>

      {/* Center — Recherche */}
      <div className="flex-1 max-w-xl mx-3 md:mx-6 relative" ref={searchRef}>
        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "#94A3B8" }} />
        <input
          data-testid="topbar-search"
          type="text"
          placeholder="Rechercher clients, produits, commandes…"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onFocus={() => searchResults.length > 0 && setSearchOpen(true)}
          style={{
            width: "100%",
            paddingLeft: "36px",
            paddingRight: "36px",
            paddingTop: "8px",
            paddingBottom: "8px",
            fontSize: "13px",
            background: "rgba(255,255,255,0.05)",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: "10px",
            color: "#E2E8F0",
            outline: "none",
            transition: "border-color 0.2s, box-shadow 0.2s",
          }}
          onFocusCapture={(e) => {
            e.target.style.borderColor = "#F97316";
            e.target.style.boxShadow = "0 0 0 3px rgba(249,115,22,0.12)";
          }}
          onBlurCapture={(e) => {
            e.target.style.borderColor = "rgba(255,255,255,0.1)";
            e.target.style.boxShadow = "none";
          }}
        />
        {searchLoading && (
          <Loader2 className="w-4 h-4 absolute right-3 top-1/2 -translate-y-1/2 animate-spin" style={{ color: "#94A3B8" }} />
        )}

        {searchOpen && searchQuery.length >= 2 && (
          <div
            data-testid="topbar-search-results"
            className="absolute left-0 right-0 mt-2 max-h-96 overflow-y-auto z-30"
            style={{
              background: "#1E293B",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: "14px",
              boxShadow: "0 16px 48px rgba(0,0,0,0.5)",
            }}
          >
            {searchResults.length === 0 && !searchLoading ? (
              <div className="px-4 py-6 text-center text-sm" style={{ color: "#94A3B8" }}>
                Aucun résultat pour « {searchQuery} »
              </div>
            ) : (
              <ul>
                {searchResults.map((r) => (
                  <li key={`${r.type}-${r.id}`} style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                    <button
                      onClick={() => handleSelectResult(r)}
                      className="w-full text-left px-4 py-2.5 transition-colors"
                      style={{ background: "transparent" }}
                      onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.04)"}
                      onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
                      data-testid={`search-result-${r.type}-${r.reference}`}
                    >
                      <div className="flex items-center justify-between">
                        <span style={{ fontSize: "10px", fontWeight: 600, color: "#F97316", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                          {TYPE_LABEL[r.type] || r.type}
                        </span>
                        <span style={{ fontSize: "11px", fontFamily: "monospace", color: "#94A3B8" }}>{r.reference}</span>
                      </div>
                      <div style={{ fontSize: "13px", fontWeight: 500, color: "#E2E8F0", marginTop: "2px" }}>{r.titre}</div>
                      {r.sous_titre && (
                        <div style={{ fontSize: "12px", color: "#94A3B8" }}>{r.sous_titre}</div>
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>

      {/* Right */}
      <div className="flex items-center gap-1 sm:gap-2">

        {/* Notifications */}
        <div className="relative" ref={notifRef}>
          <button
            data-testid="topbar-notifications-btn"
            onClick={() => setNotifOpen((o) => !o)}
            aria-label="Notifications"
            className="relative p-2 rounded-xl transition-colors"
            style={{ color: "#94A3B8" }}
            onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.08)"}
            onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
          >
            <Bell className="w-5 h-5" />
            {notifCount > 0 && (
              <span
                data-testid="topbar-notif-badge"
                className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 rounded-full text-white text-[10px] font-bold flex items-center justify-center"
                style={{ background: "#EF4444" }}
              >
                {notifCount}
              </span>
            )}
          </button>

          {notifOpen && (
            <div
              data-testid="topbar-notif-dropdown"
              className="absolute right-0 mt-2 w-96 max-h-[480px] flex flex-col overflow-hidden"
              style={{
                background: "#1E293B",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: "16px",
                boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
              }}
            >
              <div className="px-4 py-3 flex items-center justify-between" style={{ borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
                <div className="flex items-center gap-2">
                  <p style={{ fontSize: "14px", fontWeight: 600, color: "#E2E8F0" }}>Notifications</p>
                  <span
                    title={notifConnected ? "Connecté en temps réel" : "Hors ligne"}
                    className="inline-block w-2 h-2 rounded-full"
                    style={{ background: notifConnected ? "#10B981" : "#94A3B8" }}
                    data-testid="notif-ws-status"
                  />
                </div>
                {notifCount > 0 && (
                  <button
                    data-testid="notif-mark-all-read"
                    onClick={markAllAsRead}
                    className="flex items-center gap-1 text-xs"
                    style={{ color: "#F97316" }}
                  >
                    <CheckCheck className="w-3.5 h-3.5" />
                    Tout marquer lu
                  </button>
                )}
              </div>

              <div className="flex-1 overflow-y-auto" data-testid="notif-list">
                {notifItems.length === 0 ? (
                  <div className="p-8 text-center" style={{ color: "#94A3B8" }}>
                    <Inbox className="w-8 h-8 mx-auto mb-2 opacity-40" />
                    <p className="text-sm">Aucune notification pour le moment.</p>
                  </div>
                ) : (
                  notifItems.slice(0, 12).map((n) => (
                    <button
                      key={n.notification_id}
                      data-testid={`notif-item-${n.notification_id}`}
                      onClick={async () => {
                        if (!n.lue) await markAsRead(n.notification_id);
                        setNotifOpen(false);
                        if (n.lien) navigate(n.lien);
                      }}
                      className="w-full text-left px-4 py-3 transition-colors"
                      style={{
                        borderBottom: "1px solid rgba(255,255,255,0.05)",
                        opacity: n.lue ? 0.65 : 1,
                        background: "transparent",
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.04)"}
                      onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
                    >
                      <div className="flex items-start gap-3">
                        <span
                          className="mt-1.5 w-2 h-2 rounded-full shrink-0"
                          style={{ background: typeBadgeColor(n.type) }}
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <p style={{ fontSize: "13px", fontWeight: 600, color: "#E2E8F0" }} className="truncate">
                              {n.titre}
                            </p>
                            <span style={{ fontSize: "10px", color: "#94A3B8", whiteSpace: "nowrap" }}>
                              {formatRelative(n.created_at)}
                            </span>
                          </div>
                          <p style={{ fontSize: "12px", color: "#94A3B8", marginTop: "2px" }} className="line-clamp-2">
                            {n.message}
                          </p>
                        </div>
                      </div>
                    </button>
                  ))
                )}
              </div>

              <button
                data-testid="notif-see-all"
                onClick={() => { setNotifOpen(false); navigate("/notifications"); }}
                className="px-4 py-2.5 text-center text-xs font-semibold transition-colors"
                style={{
                  color: "#F97316",
                  borderTop: "1px solid rgba(255,255,255,0.08)",
                  background: "transparent",
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.04)"}
                onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
              >
                Voir toutes les notifications
              </button>
            </div>
          )}
        </div>

        {/* User menu */}
        <div className="relative" ref={userRef}>
          <button
            data-testid="topbar-user-menu"
            onClick={() => setOpen((o) => !o)}
            className="flex items-center gap-2 sm:gap-3 px-2 py-1.5 rounded-xl transition-colors"
            onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.08)"}
            onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
          >
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold text-white"
              style={{ background: "linear-gradient(135deg,#F97316,#FB923C)" }}
            >
              {initials}
            </div>
            <div className="text-left hidden lg:block">
              <p style={{ fontSize: "13px", fontWeight: 600, color: "#E2E8F0", lineHeight: 1.3 }}>
                {user.nom_complet}
              </p>
              <p style={{ fontSize: "11px", color: "#94A3B8", lineHeight: 1.2 }}>
                {ROLES[user.role] || user.role}
              </p>
            </div>
            <ChevronDown className="w-3.5 h-3.5 hidden sm:block" style={{ color: "#94A3B8" }} />
          </button>

          {open && (
            <div
              data-testid="topbar-user-dropdown"
              className="absolute right-0 mt-2 w-64 overflow-hidden"
              style={{
                background: "#1E293B",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: "16px",
                boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
              }}
            >
              <div className="px-4 py-3" style={{ borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
                <p style={{ fontSize: "14px", fontWeight: 600, color: "#E2E8F0" }}>{user.nom_complet}</p>
                <p style={{ fontSize: "12px", color: "#94A3B8" }} className="truncate">{user.email}</p>
                <span
                  className="inline-block mt-2 px-2 py-0.5 rounded-lg text-[10px] font-semibold uppercase tracking-wide"
                  style={{ background: "rgba(249,115,22,0.15)", color: "#F97316" }}
                >
                  {ROLES[user.role] || user.role}
                </span>
              </div>
              <button
                data-testid="topbar-logout-btn"
                onClick={logout}
                className="w-full flex items-center gap-2 px-4 py-3 text-sm transition-colors"
                style={{ color: "#EF4444", background: "transparent" }}
                onMouseEnter={(e) => e.currentTarget.style.background = "rgba(239,68,68,0.08)"}
                onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
              >
                <LogOut className="w-4 h-4" />
                Se déconnecter
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
