import { useEffect, useState } from "react";
import { BarChart3, Users, Briefcase, Calendar, TrendingUp, Download } from "lucide-react";
import { getRHDashboard } from "../services/rhApi";
import { Button } from "../components/ui/button";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";

export default function RapportsRH() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await getRHDashboard();
      setStats(data);
    } catch (error) {
      console.error("Error loading RH stats:", error);
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

  const rapportCards = [
    {
      title: "Effectif Global",
      icon: Users,
      value: stats?.total_employes || 0,
      description: "Nombre total d'employés",
    },
    {
      title: "Taux d'Activité",
      icon: TrendingUp,
      value: stats?.total_employes ? ((stats?.employes_actifs / stats?.total_employes) * 100).toFixed(1) : 0,
      suffix: "%",
      description: "Pourcentage d'employés actifs",
    },
    {
      title: "Contrats Actifs",
      icon: Briefcase,
      value: stats?.contrats_actifs || 0,
      description: "Contrats en cours de validité",
    },
    {
      title: "Congés en Attente",
      icon: Calendar,
      value: stats?.conges_en_attente || 0,
      description: "Demandes de congé à traiter",
    },
  ];

  return (
    <DashboardLayout>
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Rapports RH</h1>
          <p className="text-sm text-gray-500 dark:text-white/50">Rapports et statistiques des ressources humaines</p>
        </div>
        <Button variant="outline">
          <Download className="w-4 h-4 mr-2" />
          Exporter
        </Button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {rapportCards.map((card) => (
          <div key={card.title} className="bg-white dark:bg-[#0b1e30] rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-2 bg-blue-50 rounded-lg">
                <card.icon className="w-5 h-5 text-blue-600" />
              </div>
              <span className="text-2xl font-bold text-gray-900 dark:text-white">
                {card.value}{card.suffix || ""}
              </span>
            </div>
            <h3 className="font-medium text-gray-900 dark:text-white">{card.title}</h3>
            <p className="text-sm text-gray-500 dark:text-white/50 mt-1">{card.description}</p>
          </div>
        ))}
      </div>

      {/* Report Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Effectif Report */}
        <div className="bg-white dark:bg-[#0b1e30] rounded-lg shadow-sm p-6">
          <div className="flex items-center gap-3 mb-4">
            <BarChart3 className="w-5 h-5 text-gray-600 dark:text-white/70" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Effectif par Département</h2>
          </div>
          <div className="space-y-3">
            {[
              { dept: "Direction Générale", count: 2 },
              { dept: "Commercial", count: 5 },
              { dept: "Logistique", count: 4 },
              { dept: "Stock & Magasin", count: 6 },
              { dept: "Administration", count: 4 },
              { dept: "Informatique", count: 2 },
              { dept: "Comptabilité", count: 1 },
            ].map((item) => (
              <div key={item.dept} className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-white/70">{item.dept}</span>
                <div className="flex items-center gap-2">
                  <div className="w-32 h-2 bg-gray-200 dark:bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${(item.count / (stats?.total_employes || 1)) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium">{item.count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Contrats Report */}
        <div className="bg-white dark:bg-[#0b1e30] rounded-lg shadow-sm p-6">
          <div className="flex items-center gap-3 mb-4">
            <Briefcase className="w-5 h-5 text-gray-600 dark:text-white/70" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Répartition des Contrats</h2>
          </div>
          <div className="space-y-3">
            {[
              { type: "CDI", count: 18, color: "bg-green-500" },
              { type: "CDD", count: 3, color: "bg-blue-500" },
              { type: "Stage", count: 2, color: "bg-yellow-500" },
              { type: "Prestataire", count: 1, color: "bg-purple-500" },
            ].map((item) => (
              <div key={item.type} className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-white/70">{item.type}</span>
                <div className="flex items-center gap-2">
                  <div className="w-32 h-2 bg-gray-200 dark:bg-white/10 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${item.color} rounded-full`}
                      style={{ width: `${(item.count / (stats?.contrats_actifs || 1)) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium">{item.count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Alertes Report */}
        <div className="bg-white dark:bg-[#0b1e30] rounded-lg shadow-sm p-6">
          <div className="flex items-center gap-3 mb-4">
            <Calendar className="w-5 h-5 text-orange-600" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Alertes à Traiter</h2>
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
              <span className="text-sm font-medium text-red-800">Contrats expirant dans 30 jours</span>
              <span className="text-sm font-bold text-red-800">{stats?.contrats_expirant_30 || 0}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
              <span className="text-sm font-medium text-orange-800">Contrats expirant dans 90 jours</span>
              <span className="text-sm font-bold text-orange-800">{stats?.contrats_expirant_90 || 0}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
              <span className="text-sm font-medium text-yellow-800">Congés en attente</span>
              <span className="text-sm font-bold text-yellow-800">{stats?.conges_en_attente || 0}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
              <span className="text-sm font-medium text-gray-800 dark:text-white">Documents expirés</span>
              <span className="text-sm font-bold text-gray-800 dark:text-white">{stats?.documents_expires || 0}</span>
            </div>
          </div>
        </div>

        {/* Statut Report */}
        <div className="bg-white dark:bg-[#0b1e30] rounded-lg shadow-sm p-6">
          <div className="flex items-center gap-3 mb-4">
            <Users className="w-5 h-5 text-gray-600 dark:text-white/70" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Statut des Employés</h2>
          </div>
          <div className="space-y-3">
            {[
              { statut: "Actif", count: stats?.employes_actifs || 0, color: "bg-green-500" },
              { statut: "En congé", count: stats?.employes_conge || 0, color: "bg-orange-500" },
              { statut: "Suspendu", count: stats?.employes_absents || 0, color: "bg-red-500" },
            ].map((item) => (
              <div key={item.statut} className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-white/70">{item.statut}</span>
                <div className="flex items-center gap-2">
                  <div className="w-32 h-2 bg-gray-200 dark:bg-white/10 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${item.color} rounded-full`}
                      style={{ width: `${(item.count / (stats?.total_employes || 1)) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium">{item.count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
    </DashboardLayout>
  );
}
