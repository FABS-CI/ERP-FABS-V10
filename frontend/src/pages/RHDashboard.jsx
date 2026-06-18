import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Users, UserCheck, Calendar, AlertCircle, TrendingUp, Building2, Briefcase, FileText } from "lucide-react";
import { getRHDashboard, getRHAlertes } from "../services/rhApi";
import { useAuth } from "../hooks/useAuth";
import { toast } from "sonner";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/layout/PageHeader";

export default function RHDashboard() {
  const { role } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [alertes, setAlertes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const [statsData, alertesData] = await Promise.all([
        getRHDashboard(),
        getRHAlertes(),
      ]);
      setStats(statsData);
      setAlertes(alertesData);
    } catch (error) {
      console.error("Error loading RH dashboard:", error);
      toast.error("Erreur lors du chargement du tableau de bord RH");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-sm text-gray-500 dark:text-white/50">Chargement...</div>
      </div>
    );
  }

  const kpiCards = [
    {
      title: "Total Employés",
      value: stats?.total_employes || 0,
      icon: Users,
      color: "bg-blue-500",
      onClick: () => navigate("/rh/employes"),
    },
    {
      title: "Employés Actifs",
      value: stats?.employes_actifs || 0,
      icon: UserCheck,
      color: "bg-green-500",
      onClick: () => navigate("/rh/employes"),
    },
    {
      title: "En Congé",
      value: stats?.employes_conge || 0,
      icon: Calendar,
      color: "bg-orange-500",
      onClick: () => navigate("/rh/conges"),
    },
    {
      title: "Contrats Actifs",
      value: stats?.contrats_actifs || 0,
      icon: Briefcase,
      color: "bg-purple-500",
      onClick: () => navigate("/rh/contrats"),
    },
    {
      title: "Contrats Expirant (90j)",
      value: stats?.contrats_expirant_90 || 0,
      icon: AlertCircle,
      color: "bg-red-500",
      onClick: () => navigate("/rh/contrats"),
    },
    {
      title: "Missions en Cours",
      value: stats?.missions_en_cours || 0,
      icon: Building2,
      color: "bg-indigo-500",
      onClick: () => navigate("/rh/missions"),
    },
  ];

  return (
    <DashboardLayout>
    <div className="space-y-6" data-testid="rh-dashboard-page">
      <PageHeader
        icon={Users}
        title="Tableau de Bord RH"
        description="Vue d'ensemble des ressources humaines"
        favoriteKey="rh-dashboard"
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {kpiCards.map((kpi) => (
          <div
            key={kpi.title}
            onClick={kpi.onClick}
            className="bg-white dark:bg-[#0b1e30] rounded-lg shadow-sm p-6 cursor-pointer hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-white/70">{kpi.title}</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{kpi.value}</p>
              </div>
              <div className={`${kpi.color} p-3 rounded-lg`}>
                <kpi.icon className="w-6 h-6 text-white" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Alerts Section */}
      {alertes.length > 0 && (
        <div className="bg-white dark:bg-[#0b1e30] rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-orange-500" />
            Alertes RH
          </h2>
          <div className="space-y-3">
            {alertes.map((alerte, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg border ${
                  alerte.severite === "error"
                    ? "bg-red-50 border-red-200"
                    : alerte.severite === "warning"
                    ? "bg-orange-50 border-orange-200"
                    : "bg-blue-50 border-blue-200"
                }`}
              >
                <p className="text-sm font-medium text-gray-900 dark:text-white">{alerte.message}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white dark:bg-[#0b1e30] rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Actions Rapides</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button
            onClick={() => navigate("/rh/employes")}
            className="flex flex-col items-center p-4 bg-gray-50 dark:bg-white/5 rounded-lg hover:bg-gray-100 dark:bg-white/10 transition-colors"
          >
            <Users className="w-6 h-6 text-gray-700 dark:text-white/90 mb-2" />
            <span className="text-sm font-medium text-gray-700 dark:text-white/90">Employés</span>
          </button>
          <button
            onClick={() => navigate("/rh/contrats")}
            className="flex flex-col items-center p-4 bg-gray-50 dark:bg-white/5 rounded-lg hover:bg-gray-100 dark:bg-white/10 transition-colors"
          >
            <Briefcase className="w-6 h-6 text-gray-700 dark:text-white/90 mb-2" />
            <span className="text-sm font-medium text-gray-700 dark:text-white/90">Contrats</span>
          </button>
          <button
            onClick={() => navigate("/rh/conges")}
            className="flex flex-col items-center p-4 bg-gray-50 dark:bg-white/5 rounded-lg hover:bg-gray-100 dark:bg-white/10 transition-colors"
          >
            <Calendar className="w-6 h-6 text-gray-700 dark:text-white/90 mb-2" />
            <span className="text-sm font-medium text-gray-700 dark:text-white/90">Congés</span>
          </button>
          <button
            onClick={() => navigate("/rh/rapports")}
            className="flex flex-col items-center p-4 bg-gray-50 dark:bg-white/5 rounded-lg hover:bg-gray-100 dark:bg-white/10 transition-colors"
          >
            <FileText className="w-6 h-6 text-gray-700 dark:text-white/90 mb-2" />
            <span className="text-sm font-medium text-gray-700 dark:text-white/90">Rapports</span>
          </button>
        </div>
      </div>
    </div>
    </DashboardLayout>
  );
}
