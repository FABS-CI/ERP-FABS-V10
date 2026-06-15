import { useState } from "react";
import { Navigate } from "react-router-dom";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import Breadcrumb from "./Breadcrumb";
import { useAuth } from "../../hooks/useAuth";

export default function DashboardLayout({ children }) {
  const { user, isLoading } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "#0B1220" }}>
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 rounded-full border-2 border-[#F97316] border-t-transparent animate-spin" />
          <p className="text-sm" style={{ color: "#94A3B8" }}>Chargement…</p>
        </div>
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;

  return (
    <div className="min-h-screen" style={{ background: "#0B1220" }}>
      <Sidebar mobileOpen={mobileOpen} onMobileClose={() => setMobileOpen(false)} />
      <Topbar onToggleSidebar={() => setMobileOpen((o) => !o)} />
      <main
        className="md:ml-64 min-h-screen px-4 md:px-8 pt-20 md:pt-24 pb-8"
        style={{ background: "#0B1220" }}
      >
        <Breadcrumb />
        {children}
      </main>
    </div>
  );
}
