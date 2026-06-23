import "@/App.css";
import "./styles/theme.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { lazy, Suspense } from "react";
import { AuthProvider } from "./hooks/useAuth";
import { ThemeProvider } from "./contexts/ThemeContext";
import ProtectedRoute from "./components/ProtectedRoute";
import { useAuth } from "./hooks/useAuth";
import { visibleModulesFor } from "./constants/permissions";
import { useIdleLogout } from "./hooks/useIdleLogout";
import IdleWarningModal from "./components/IdleWarningModal";

// Composant de redirection intelligente vers le premier module accessible
function SmartRedirect() {
  const { role, isLoading } = useAuth();
  if (isLoading) return null;
  if (!role) return <Navigate to="/login" replace />;
  const firstModule = visibleModulesFor(role)[0];
  return <Navigate to={firstModule ? firstModule.path : "/login"} replace />;
}

// Lazy load pages for code splitting
const Login = lazy(() => import("./pages/Login"));
const DevLogin = lazy(() => import("./pages/DevLogin"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const RHDashboard = lazy(() => import("./pages/RHDashboard"));
const Employes = lazy(() => import("./pages/Employes"));
const EmployeForm = lazy(() => import("./pages/EmployeForm"));
const Departements = lazy(() => import("./pages/Departements"));
const Fonctions = lazy(() => import("./pages/Fonctions"));
const CategoriesPro = lazy(() => import("./pages/CategoriesPro"));
const Contrats = lazy(() => import("./pages/Contrats"));
const Conges = lazy(() => import("./pages/Conges"));
const Absences = lazy(() => import("./pages/Absences"));
const Missions = lazy(() => import("./pages/Missions"));
const Evaluations = lazy(() => import("./pages/Evaluations"));
const RapportsRH = lazy(() => import("./pages/RapportsRH"));
const Clients = lazy(() => import("./pages/Clients"));
const ClientDetail = lazy(() => import("./pages/ClientDetail"));
const Produits = lazy(() => import("./pages/Produits"));
const ProduitDetail = lazy(() => import("./pages/ProduitDetail"));
const ProduitsInventaire = lazy(() => import("./pages/ProduitsInventaire"));
const Commandes = lazy(() => import("./pages/Commandes"));
const CommandeDetail = lazy(() => import("./pages/CommandeDetail"));
const CommandeForm = lazy(() => import("./components/commandes/CommandeForm"));
const Factures = lazy(() => import("./pages/Factures"));
const FactureDetail = lazy(() => import("./pages/FactureDetail"));
const Paiements = lazy(() => import("./pages/Paiements"));
const PaiementDetail = lazy(() => import("./pages/PaiementDetail"));
const Stock = lazy(() => import("./pages/Stock"));
const BonsLivraison = lazy(() => import("./pages/BonsLivraison"));
const BonsRetour = lazy(() => import("./pages/BonsRetour"));
const Comptabilite = lazy(() => import("./pages/Comptabilite"));
const AnalyticsReports = lazy(() => import("./pages/AnalyticsReports"));
const Utilisateurs = lazy(() => import("./pages/Utilisateurs"));
const Parametres = lazy(() => import("./pages/Parametres"));
const Documents = lazy(() => import("./pages/Documents"));
const DocumentDetail = lazy(() => import("./pages/DocumentDetail"));
const Colis = lazy(() => import("./pages/Colis"));
const Expeditions = lazy(() => import("./pages/Expeditions"));
const OrdresColisage = lazy(() => import("./pages/OrdresColisage"));
const OrdreColisageDetail = lazy(() => import("./pages/OrdreColisageDetail"));
const LivraisonsDirectes = lazy(() => import("./pages/LivraisonsDirectes"));
const Incidents = lazy(() => import("./pages/Incidents"));
const Notifications = lazy(() => import("./pages/Notifications"));
const Logistique = lazy(() => import("./pages/Logistique"));
const ComptabiliteAvancee = lazy(() => import("./pages/ComptabiliteAvancee"));
const Fleet = lazy(() => import("./pages/Fleet"));
const LogisticsCosts = lazy(() => import("./pages/LogisticsCosts"));
const LogistiqueHub = lazy(() => import("./pages/LogistiqueHub"));
const MultiChannelNotifications = lazy(() => import("./pages/MultiChannelNotifications"));
const BIAnalytics = lazy(() => import("./pages/BIAnalytics"));
const WorkflowApprovals = lazy(() => import("./pages/WorkflowApprovals"));
const ProformaDetail = lazy(() => import("./pages/ProformaDetail"));
const Proformas = lazy(() => import("./pages/Proformas"));
const HistoriqueEnvois = lazy(() => import("./pages/HistoriqueEnvois"));
// Sprint 2 V10 — Dashboard FNE Enterprise
const FNE = lazy(() => import("./pages/FNE"));
const FNEInvoiceDetail = lazy(() => import("./pages/FNEInvoiceDetail"));
const FNEInvoiceNew = lazy(() => import("./pages/FNEInvoiceNew"));
const FNESettings = lazy(() => import("./pages/FNESettings"));
const FNELogs = lazy(() => import("./pages/FNELogs"));
// Sprint 3 V10 — Module Fournisseurs
const Fournisseurs = lazy(() => import("./pages/Fournisseurs"));
const FournisseurDetail = lazy(() => import("./pages/FournisseurDetail"));
// Sprint 4 V10 — Module Approvisionnements
const Approvisionnements = lazy(() => import("./pages/Approvisionnements"));
const ApprovisionnementDetail = lazy(() => import("./pages/ApprovisionnementDetail"));
// Sprint 6b V10 — Paie
const Paie = lazy(() => import("./pages/Paie"));
// Sprint 7 V10 — Documents & Impression
const DocumentsImpression = lazy(() => import("./pages/DocumentsImpression"));
const FileStorage = lazy(() => import("./pages/FileStorage"));
const Backup = lazy(() => import("./pages/Backup"));
const NotFound = lazy(() => import("./pages/NotFound"));
const EtatCompteClients = lazy(() => import("./pages/EtatCompteClients"));

// Loading fallback for lazy loaded components — skeleton animé
function PageLoader() {
  return (
    <div className="min-h-screen bg-[#F5F5F5] dark:bg-[#040f1a] p-6">
      {/* Topbar skeleton */}
      <div className="h-14 bg-white dark:bg-[#0b1e30] rounded-xl mb-6 animate-pulse" />
      {/* Content skeletons */}
      <div className="space-y-4">
        <div className="h-8 w-1/3 bg-gray-200 dark:bg-[#0b2a40] rounded-lg animate-pulse" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 bg-white dark:bg-[#0b1e30] rounded-xl animate-pulse" />
          ))}
        </div>
        <div className="h-64 bg-white dark:bg-[#0b1e30] rounded-xl animate-pulse" />
        <div className="h-40 bg-white dark:bg-[#0b1e30] rounded-xl animate-pulse" />
      </div>
    </div>
  );
}

function AppWithIdle({ children }) {
  const { user, logout } = useAuth();
  const { showWarning, secondsLeft, stayConnected, doLogout } = useIdleLogout(logout, !!user);
  return (
    <>
      {children}
      {showWarning && (
        <IdleWarningModal
          secondsLeft={secondsLeft}
          onStay={stayConnected}
          onLogout={doLogout}
        />
      )}
    </>
  );
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <ThemeProvider>
            <AppWithIdle>
              <Suspense fallback={<PageLoader />}>
            <Routes>
              {/* Public Routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/dev-login" element={<DevLogin />} />
            
            {/* Protected Routes */}
            <Route path="/" element={<SmartRedirect />} />
            
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute moduleKey="dashboard">
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            
            {/* RH Module */}
            <Route
              path="/rh"
              element={
                <ProtectedRoute moduleKey="rh-employes">
                  <RHDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/rh/employes"
              element={
                <ProtectedRoute moduleKey="rh-employes">
                  <Employes />
                </ProtectedRoute>
              }
            />
            <Route
              path="/rh/departements"
              element={
                <ProtectedRoute moduleKey="rh-departements">
                  <Departements />
                </ProtectedRoute>
              }
            />
            <Route
              path="/rh/fonctions"
              element={
                <ProtectedRoute moduleKey="rh-fonctions">
                  <Fonctions />
                </ProtectedRoute>
              }
            />
            <Route
              path="/rh/categories-pro"
              element={
                <ProtectedRoute moduleKey="rh-fonctions">
                  <CategoriesPro />
                </ProtectedRoute>
              }
            />
            <Route
              path="/rh/contrats"
              element={
                <ProtectedRoute moduleKey="rh-contrats">
                  <Contrats />
                </ProtectedRoute>
              }
            />
            <Route
              path="/rh/conges"
              element={
                <ProtectedRoute moduleKey="rh-conges">
                  <Conges />
                </ProtectedRoute>
              }
            />
            <Route
              path="/rh/absences"
              element={
                <ProtectedRoute moduleKey="rh-absences">
                  <Absences />
                </ProtectedRoute>
              }
            />
            <Route
              path="/rh/missions"
              element={
                <ProtectedRoute moduleKey="rh-missions">
                  <Missions />
                </ProtectedRoute>
              }
            />
            <Route
              path="/rh/evaluations"
              element={
                <ProtectedRoute moduleKey="rh-evaluations">
                  <Evaluations />
                </ProtectedRoute>
              }
            />
            <Route
              path="/rh/rapports"
              element={
                <ProtectedRoute moduleKey="rh-rapports">
                  <RapportsRH />
                </ProtectedRoute>
              }
            />
            
            {/* Clients */}
            <Route
              path="/clients"
              element={
                <ProtectedRoute moduleKey="clients">
                  <Clients />
                </ProtectedRoute>
              }
            />
            <Route
              path="/clients/:id"
              element={
                <ProtectedRoute moduleKey="clients">
                  <ClientDetail />
                </ProtectedRoute>
              }
            />
            
            {/* Produits */}
            <Route
              path="/produits"
              element={
                <ProtectedRoute moduleKey="produits">
                  <Produits />
                </ProtectedRoute>
              }
            />
            <Route
              path="/produits/:id"
              element={
                <ProtectedRoute moduleKey="produits">
                  <ProduitDetail />
                </ProtectedRoute>
              }
            />
            <Route
              path="/produits-inventaire"
              element={
                <ProtectedRoute moduleKey="produits">
                  <ProduitsInventaire />
                </ProtectedRoute>
              }
            />
            
            {/* Commandes */}
            <Route
              path="/commandes"
              element={
                <ProtectedRoute moduleKey="commandes">
                  <Commandes />
                </ProtectedRoute>
              }
            />
            <Route
              path="/commandes/nouvelle"
              element={
                <ProtectedRoute moduleKey="commandes">
                  <CommandeForm />
                </ProtectedRoute>
              }
            />
            <Route
              path="/commandes/:id/modifier"
              element={
                <ProtectedRoute moduleKey="commandes">
                  <CommandeForm />
                </ProtectedRoute>
              }
            />
            <Route
              path="/commandes/:id"
              element={
                <ProtectedRoute moduleKey="commandes">
                  <CommandeDetail />
                </ProtectedRoute>
              }
            />
            
            {/* Proformas */}
            <Route
              path="/proformas"
              element={
                <ProtectedRoute moduleKey="proformas">
                  <Proformas />
                </ProtectedRoute>
              }
            />
            <Route
              path="/proformas/:proformaId"
              element={
                <ProtectedRoute moduleKey="proformas">
                  <ProformaDetail />
                </ProtectedRoute>
              }
            />

            {/* Historique des envois */}
            <Route
              path="/historique-envois"
              element={
                <ProtectedRoute>
                  <HistoriqueEnvois />
                </ProtectedRoute>
              }
            />
            
            {/* Factures */}
            <Route
              path="/factures"
              element={
                <ProtectedRoute moduleKey="factures">
                  <Factures />
                </ProtectedRoute>
              }
            />
            <Route
              path="/factures/:id"
              element={
                <ProtectedRoute moduleKey="factures">
                  <FactureDetail />
                </ProtectedRoute>
              }
            />

            {/* Sprint 2 V10 — FNE Enterprise (DGI Côte d'Ivoire) */}
            <Route
              path="/fne"
              element={
                <ProtectedRoute moduleKey="fne">
                  <FNE />
                </ProtectedRoute>
              }
            />
            <Route
              path="/fne/invoices/new"
              element={
                <ProtectedRoute moduleKey="fne">
                  <FNEInvoiceNew />
                </ProtectedRoute>
              }
            />
            <Route
              path="/fne/invoices/:invoiceId"
              element={
                <ProtectedRoute moduleKey="fne">
                  <FNEInvoiceDetail />
                </ProtectedRoute>
              }
            />
            <Route
              path="/fne/settings"
              element={
                <ProtectedRoute moduleKey="fne">
                  <FNESettings />
                </ProtectedRoute>
              }
            />
            <Route
              path="/fne/logs"
              element={
                <ProtectedRoute moduleKey="fne">
                  <FNELogs />
                </ProtectedRoute>
              }
            />

            {/* Sprint 3 V10 — Fournisseurs */}
            <Route
              path="/fournisseurs"
              element={
                <ProtectedRoute moduleKey="fournisseurs">
                  <Fournisseurs />
                </ProtectedRoute>
              }
            />
            <Route
              path="/fournisseurs/:fournisseurId"
              element={
                <ProtectedRoute moduleKey="fournisseurs">
                  <FournisseurDetail />
                </ProtectedRoute>
              }
            />

            {/* Sprint 4 V10 — Approvisionnements */}
            <Route
              path="/approvisionnements"
              element={
                <ProtectedRoute moduleKey="approvisionnements">
                  <Approvisionnements />
                </ProtectedRoute>
              }
            />
            <Route
              path="/approvisionnements/:approvisionnementId"
              element={
                <ProtectedRoute moduleKey="approvisionnements">
                  <ApprovisionnementDetail />
                </ProtectedRoute>
              }
            />

            {/* Sprint 6b V10 — Paie (sous-module RH) */}
            <Route
              path="/rh/paie"
              element={
                <ProtectedRoute moduleKey="rh-paie">
                  <Paie />
                </ProtectedRoute>
              }
            />

            {/* Sprint 7 V10 — Documents & Impression */}
            <Route
              path="/parametres/documents-impression"
              element={
                <ProtectedRoute moduleKey="documents-impression">
                  <DocumentsImpression />
                </ProtectedRoute>
              }
            />
            
            {/* Paiements */}
            <Route
              path="/paiements"
              element={
                <ProtectedRoute moduleKey="paiements">
                  <Paiements />
                </ProtectedRoute>
              }
            />
            <Route
              path="/paiements/:id"
              element={
                <ProtectedRoute moduleKey="paiements">
                  <PaiementDetail />
                </ProtectedRoute>
              }
            />
            
            {/* Stock */}
            <Route
              path="/stock"
              element={
                <ProtectedRoute moduleKey="stock">
                  <Stock />
                </ProtectedRoute>
              }
            />
            
            {/* Bons de Livraison */}
            <Route
              path="/livraisons"
              element={
                <ProtectedRoute moduleKey="livraisons">
                  <BonsLivraison />
                </ProtectedRoute>
              }
            />
            
            {/* Bons de Retour */}
            <Route
              path="/retours"
              element={
                <ProtectedRoute moduleKey="retours">
                  <BonsRetour />
                </ProtectedRoute>
              }
            />
            
            {/* Colisage */}
            <Route
              path="/colis"
              element={
                <ProtectedRoute>
                  <Colis />
                </ProtectedRoute>
              }
            />
            <Route
              path="/expeditions"
              element={
                <ProtectedRoute>
                  <Expeditions />
                </ProtectedRoute>
              }
            />
            <Route
              path="/ordres-colisage"
              element={
                <ProtectedRoute>
                  <OrdresColisage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/ordres-colisage/:id"
              element={
                <ProtectedRoute>
                  <OrdreColisageDetail />
                </ProtectedRoute>
              }
            />
            <Route
              path="/livraisons-directes"
              element={
                <ProtectedRoute>
                  <LivraisonsDirectes />
                </ProtectedRoute>
              }
            />
            <Route
              path="/incidents"
              element={
                <ProtectedRoute>
                  <Incidents />
                </ProtectedRoute>
              }
            />

            {/* Notifications */}
            <Route
              path="/notifications"
              element={
                <ProtectedRoute>
                  <Notifications />
                </ProtectedRoute>
              }
            />
            
            {/* Logistique */}
            <Route
              path="/logistique"
              element={
                <ProtectedRoute>
                  <Logistique />
                </ProtectedRoute>
              }
            />
            
            {/* Hub Logistique (vue centralisée) */}
            <Route
              path="/logistique-hub"
              element={
                <ProtectedRoute>
                  <LogistiqueHub />
                </ProtectedRoute>
              }
            />
            
            {/* Comptabilité Avancée */}
            <Route
              path="/comptabilite-avancee"
              element={
                <ProtectedRoute>
                  <ComptabiliteAvancee />
                </ProtectedRoute>
              }
            />
            
            {/* Legacy route aliases */}
            <Route path="/flotte" element={<Navigate to="/fleet" replace />} />
            <Route path="/administration/utilisateurs" element={<Navigate to="/utilisateurs" replace />} />

            {/* Fleet Management */}
            <Route
              path="/fleet"
              element={
                <ProtectedRoute>
                  <Fleet />
                </ProtectedRoute>
              }
            />
            
            {/* Logistics Costs */}
            <Route
              path="/logistics-costs"
              element={
                <ProtectedRoute>
                  <LogisticsCosts />
                </ProtectedRoute>
              }
            />
            
            {/* Multi-Channel Notifications */}
            <Route
              path="/multi-channel-notifications"
              element={
                <ProtectedRoute>
                  <MultiChannelNotifications />
                </ProtectedRoute>
              }
            />
            
            {/* BI Analytics */}
            <Route
              path="/bi-analytics"
              element={
                <ProtectedRoute>
                  <BIAnalytics />
                </ProtectedRoute>
              }
            />
            
            {/* Workflow Approvals */}
            <Route
              path="/workflow-approvals"
              element={
                <ProtectedRoute>
                  <WorkflowApprovals />
                </ProtectedRoute>
              }
            />
            
            {/* File Storage */}
            <Route
              path="/file-storage"
              element={
                <ProtectedRoute>
                  <FileStorage />
                </ProtectedRoute>
              }
            />
            
            {/* Backup */}
            <Route
              path="/backup"
              element={
                <ProtectedRoute>
                  <Backup />
                </ProtectedRoute>
              }
            />
            
            {/* Comptabilité */}
            <Route
              path="/comptabilite"
              element={
                <ProtectedRoute moduleKey="comptabilite">
                  <Comptabilite />
                </ProtectedRoute>
              }
            />
            
            {/* Rapports & Analytics */}
            <Route
              path="/rapports"
              element={
                <ProtectedRoute>
                  <AnalyticsReports />
                </ProtectedRoute>
              }
            />
            <Route
              path="/rapports/etat-compte-clients"
              element={
                <ProtectedRoute moduleKey="etat-compte-clients">
                  <EtatCompteClients />
                </ProtectedRoute>
              }
            />
            
            {/* Utilisateurs */}
            <Route
              path="/utilisateurs"
              element={
                <ProtectedRoute moduleKey="utilisateurs">
                  <Utilisateurs />
                </ProtectedRoute>
              }
            />
            
            {/* Paramètres */}
            <Route
              path="/parametres"
              element={
                <ProtectedRoute moduleKey="parametres">
                  <Parametres />
                </ProtectedRoute>
              }
            />
            
            {/* Redirections routes manquantes */}
            <Route path="/bons-livraison/:id" element={<Navigate to="/livraisons" replace />} />
            <Route path="/documents/analytics" element={<Navigate to="/documents" replace />} />
            <Route path="/documents/upload" element={<Navigate to="/documents" replace />} />
            <Route path="/rh/employes/new" element={<ProtectedRoute><EmployeForm /></ProtectedRoute>} />
            <Route path="/rh/employes/:id/edit" element={<ProtectedRoute><EmployeForm /></ProtectedRoute>} />

            {/* Documents AI */}
            <Route
              path="/documents"
              element={
                <ProtectedRoute>
                  <Documents />
                </ProtectedRoute>
              }
            />
            <Route
              path="/documents/:id"
              element={
                <ProtectedRoute>
                  <DocumentDetail />
                </ProtectedRoute>
              }
            />
            
            {/* 404 */}
            <Route path="*" element={<NotFound />} />
              </Routes>
              </Suspense>
            </AppWithIdle>
          </ThemeProvider>
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
