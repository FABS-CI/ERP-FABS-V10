/**
 * Page FNE — Paramètres (V10)
 * Onglet 1 : Configuration (formulaire éditable, super_admin)
 * Onglet 2 : Tests API DGI (5 boutons de test)
 */
import React, { useState, useEffect, useContext } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft, Wifi, WifiOff, ShieldCheck, AlertTriangle, CheckCircle2,
  Settings2, FlaskConical, Eye, EyeOff, Save, RotateCcw, FileText,
  Receipt, CreditCard, ReceiptRefund, BarChart3
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";
import {
  getFNESettings, updateFNESettings, pingDGI,
  testSignInvoice, testSignB2B, testSignB2G,
  testRefundInvoice, testBalanceSticker,
} from "../services/fneApi";

// Récupère le rôle depuis le localStorage (pattern ERP FABS-CI)
function useUserRole() {
  try {
    const user = JSON.parse(localStorage.getItem("user") || "{}");
    return user?.role || null;
  } catch {
    return null;
  }
}

const TABS = [
  { id: "config",  label: "Configuration",  icon: Settings2   },
  { id: "tests",   label: "Tests API DGI",   icon: FlaskConical },
];

export default function FNESettings() {
  const navigate = useNavigate();
  const userRole = useUserRole();
  const isSuperAdmin = userRole === "super_admin";

  const [activeTab, setActiveTab]     = useState("config");
  const [loading, setLoading]         = useState(true);
  const [settings, setSettings]       = useState(null);
  const [pingResult, setPingResult]   = useState(null);
  const [pinging, setPinging]         = useState(false);

  // Formulaire édition
  const [editMode, setEditMode]       = useState(false);
  const [saving, setSaving]           = useState(false);
  const [showKey, setShowKey]         = useState(false);
  const [form, setForm]               = useState({});

  // Tests API
  const [testResults, setTestResults] = useState({});
  const [testRunning, setTestRunning] = useState({});
  const [lastTestInvoiceId, setLastTestInvoiceId] = useState(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const s = await getFNESettings();
      setSettings(s);
      // Initialiser le formulaire avec les valeurs courantes
      setForm({
        company_ncc:          s?.company?.ncc || "",
        company_idu:          s?.company?.idu || "",
        company_name:         s?.company?.name || "",
        company_regime:       s?.company?.regime || "",
        company_secteur:      s?.company?.secteur || "",
        company_dran:         s?.company?.dran || "",
        company_centre_impots:s?.company?.centre_impots || "",
        point_of_sale:        s?.company?.point_of_sale || "01",
        establishment:        s?.company?.establishment || "Siège Social",
        fne_base_url_prod:    s?.api?.base_url_prod || "",
        dgi_api_key:          "",   // Toujours vide par sécurité
        use_production:       s?.api?.use_production || false,
      });
    } catch (e) {
      toast.error("Impossible de charger les paramètres FNE");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = { ...form };
      // Ne pas envoyer dgi_api_key si vide (évite d'écraser)
      if (!payload.dgi_api_key) delete payload.dgi_api_key;
      await updateFNESettings(payload);
      toast.success("Configuration FNE sauvegardée");
      setEditMode(false);
      await loadSettings();
    } catch (e) {
      const msg = e?.response?.data?.detail || e.message || "Erreur de sauvegarde";
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  const handlePing = async () => {
    setPinging(true);
    try {
      const r = await pingDGI();
      setPingResult(r);
      if (r.ok) toast.success(`API DGI joignable (${r.elapsed_ms} ms)`);
      else toast.error(`API DGI injoignable`);
    } catch (e) {
      toast.error("Erreur ping DGI");
      setPingResult({ ok: false, error: e.message });
    } finally {
      setPinging(false);
    }
  };

  // ── Test runner générique ───────────────────────────────────────────────
  const runTest = async (testId, fn) => {
    setTestRunning(p => ({ ...p, [testId]: true }));
    setTestResults(p => ({ ...p, [testId]: null }));
    const started = Date.now();
    try {
      const result = await fn();
      const elapsed = Date.now() - started;
      setTestResults(p => ({ ...p, [testId]: { ok: true, data: result, elapsed } }));
      toast.success(`Test "${testId}" réussi`);
      // Sauvegarder le dernier ID de facture pour le test d'avoir
      if (testId === "b2c" || testId === "b2b") {
        const invoiceId = result?.data?.fne_id || result?.data?.reference;
        if (invoiceId) setLastTestInvoiceId(invoiceId);
      }
    } catch (e) {
      const elapsed = Date.now() - started;
      const detail = e?.response?.data?.detail || e.message || "Erreur inconnue";
      setTestResults(p => ({ ...p, [testId]: { ok: false, error: detail, elapsed } }));
      toast.error(`Test "${testId}" échoué`);
    } finally {
      setTestRunning(p => ({ ...p, [testId]: false }));
    }
  };

  const TEST_BUTTONS = [
    {
      id: "ping",
      label: "Ping API DGI",
      description: "Vérifie la connectivité réseau avec le serveur DGI",
      icon: Wifi,
      color: "bg-[#3B82F6]",
      run: async () => {
        const r = await pingDGI();
        if (!r.ok) throw new Error(r.error || "Connexion échouée");
        return r;
      },
    },
    {
      id: "b2c",
      label: "Facture B2C (test)",
      description: "Certifie une facture client particulier (montant 1 000 FCFA)",
      icon: Receipt,
      color: "bg-[#10B981]",
      run: () => testSignInvoice({ template: "B2C" }),
    },
    {
      id: "b2b",
      label: "Facture B2B (test)",
      description: "Certifie une facture entreprise avec NCC client",
      icon: FileText,
      color: "bg-[#FF6200]",
      run: () => testSignB2B("9876543Z"),
    },
    {
      id: "b2g",
      label: "Facture B2G (test)",
      description: "Certifie une facture gouvernementale / institution publique",
      icon: CreditCard,
      color: "bg-[#8B5CF6]",
      run: () => testSignB2G(),
    },
    {
      id: "refund",
      label: "Avoir (test)",
      description: "Crée un avoir sur la dernière facture certifiée en test",
      icon: RotateCcw,
      color: "bg-[#EF4444]",
      run: () => {
        if (!lastTestInvoiceId) throw new Error("Lancez d'abord un test B2C ou B2B pour obtenir un invoiceId");
        return testRefundInvoice(lastTestInvoiceId, []);
      },
    },
    {
      id: "balance",
      label: "Balance Sticker",
      description: "Consulte le solde de timbres fiscaux chez la DGI",
      icon: BarChart3,
      color: "bg-[#F59E0B]",
      run: () => testBalanceSticker(),
    },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="fne-settings-page">
        {/* Header */}
        <Button variant="ghost" onClick={() => navigate("/fne")} data-testid="btn-back">
          <ArrowLeft className="h-4 w-4 mr-2" /> Retour FNE
        </Button>

        <div className="flex items-start justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <ShieldCheck className="h-8 w-8 text-[#FF6200]" />
              Paramètres FNE
            </h1>
            <p className="text-muted-foreground mt-1">
              Configuration de l'intégration DGI Côte d'Ivoire — EDITIONS FABS-CI
            </p>
          </div>
          <Badge className={settings?.api?.use_production ? "bg-[#10B981] text-white" : "bg-[#F59E0B] text-white"}>
            {settings?.api?.use_production ? "🟢 PRODUCTION" : "🟡 TEST / SANDBOX"}
          </Badge>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 border-b">
          {TABS.map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? "border-[#FF6200] text-[#FF6200]"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {loading ? (
          <Skeleton className="h-96 w-full" />
        ) : (
          <>
            {/* ═══════════════ ONGLET CONFIGURATION ═══════════════ */}
            {activeTab === "config" && (
              <div className="space-y-6">
                {/* Statut API KEY */}
                {!settings?.api?.api_key_configured && (
                  <div className="p-4 rounded-lg bg-[#F59E0B]/10 border border-[#F59E0B]/40 flex items-start gap-3" data-testid="config-warning">
                    <AlertTriangle className="h-5 w-5 text-[#F59E0B] mt-0.5 shrink-0" />
                    <div>
                      <p className="font-semibold text-sm">API KEY DGI non configurée — mode sandbox</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {isSuperAdmin
                          ? 'Renseignez la clé via le formulaire ci-dessous (champ "Clé API DGI").'
                          : "Contactez votre administrateur système pour configurer la clé API DGI."}
                      </p>
                    </div>
                  </div>
                )}

                {/* Formulaire */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Entreprise */}
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <div>
                        <CardTitle className="text-base">Entreprise</CardTitle>
                        <CardDescription>Infos fiscales transmises à la DGI</CardDescription>
                      </div>
                      {isSuperAdmin && !editMode && (
                        <Button variant="outline" size="sm" onClick={() => setEditMode(true)}>
                          <Settings2 className="h-4 w-4 mr-1.5" /> Modifier
                        </Button>
                      )}
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <FormField label="NCC" field="company_ncc" form={form} setForm={setForm} editMode={editMode} mono />
                      <FormField label="IDU" field="company_idu" form={form} setForm={setForm} editMode={editMode} mono />
                      <FormField label="Nom société" field="company_name" form={form} setForm={setForm} editMode={editMode} />
                      <FormField label="Régime d'imposition" field="company_regime" form={form} setForm={setForm} editMode={editMode} />
                      <FormField label="Secteur d'activité" field="company_secteur" form={form} setForm={setForm} editMode={editMode} />
                      <FormField label="Direction (DRAN)" field="company_dran" form={form} setForm={setForm} editMode={editMode} />
                      <FormField label="Centre d'impôts" field="company_centre_impots" form={form} setForm={setForm} editMode={editMode} />
                      <FormField label="Point de vente" field="point_of_sale" form={form} setForm={setForm} editMode={editMode} />
                      <FormField label="Établissement" field="establishment" form={form} setForm={setForm} editMode={editMode} />
                    </CardContent>
                  </Card>

                  {/* API */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">API DGI</CardTitle>
                      <CardDescription>Connexion à l'API de certification</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {/* URL test (lecture seule) */}
                      <div>
                        <Label className="text-xs text-muted-foreground">URL API Test</Label>
                        <p className="font-mono text-xs mt-0.5 p-2 bg-muted rounded">{settings?.api?.base_url_test}</p>
                      </div>

                      <FormField label="URL API Production" field="fne_base_url_prod" form={form} setForm={setForm} editMode={editMode} mono
                        placeholder="Transmise par la DGI après inscription" />

                      {/* API KEY */}
                      {editMode ? (
                        <div className="space-y-1">
                          <Label className="text-xs font-medium">Clé API DGI (DGI_API_KEY)</Label>
                          <div className="relative">
                            <Input
                              type={showKey ? "text" : "password"}
                              value={form.dgi_api_key}
                              onChange={e => setForm(p => ({ ...p, dgi_api_key: e.target.value }))}
                              placeholder="Collez votre clé API DGI ici"
                              className="pr-10 font-mono text-xs"
                            />
                            <button
                              type="button"
                              onClick={() => setShowKey(v => !v)}
                              className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground"
                            >
                              {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </button>
                          </div>
                          <p className="text-xs text-muted-foreground">Laisser vide pour conserver la clé actuelle</p>
                        </div>
                      ) : (
                        <div>
                          <Label className="text-xs text-muted-foreground">Clé API DGI</Label>
                          <div className="flex items-center gap-2 mt-0.5">
                            {settings?.api?.api_key_configured ? (
                              <span className="flex items-center gap-1.5 text-sm text-[#10B981]">
                                <CheckCircle2 className="h-4 w-4" />
                                Configurée <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{settings.api.api_key_masked}</code>
                              </span>
                            ) : (
                              <span className="flex items-center gap-1.5 text-sm text-[#F59E0B]">
                                <AlertTriangle className="h-4 w-4" />
                                Non configurée — sandbox
                              </span>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Mode production toggle */}
                      {editMode && (
                        <div className="flex items-center gap-3 pt-2">
                          <input
                            type="checkbox"
                            id="use_production"
                            checked={form.use_production}
                            onChange={e => setForm(p => ({ ...p, use_production: e.target.checked }))}
                            className="w-4 h-4 accent-[#FF6200]"
                          />
                          <label htmlFor="use_production" className="text-sm cursor-pointer">
                            Activer le mode <strong>PRODUCTION</strong>
                            <span className="block text-xs text-muted-foreground">Uniquement après validation DGI</span>
                          </label>
                        </div>
                      )}

                      {/* Boutons save/cancel */}
                      {editMode && (
                        <div className="flex gap-2 pt-3">
                          <Button onClick={handleSave} disabled={saving} className="flex-1 bg-[#FF6200] hover:bg-[#e55800]">
                            <Save className="h-4 w-4 mr-1.5" />
                            {saving ? "Sauvegarde…" : "Enregistrer"}
                          </Button>
                          <Button variant="outline" onClick={() => { setEditMode(false); loadSettings(); }}>
                            Annuler
                          </Button>
                        </div>
                      )}

                      {/* Ping */}
                      <div className="pt-2 border-t space-y-2">
                        <Button onClick={handlePing} disabled={pinging} variant="outline" className="w-full" data-testid="btn-ping-dgi">
                          {pinging ? (
                            "Test en cours…"
                          ) : pingResult?.ok ? (
                            <><Wifi className="h-4 w-4 mr-2 text-[#10B981]" /> Ping DGI — OK ({pingResult.elapsed_ms} ms)</>
                          ) : pingResult?.ok === false ? (
                            <><WifiOff className="h-4 w-4 mr-2 text-[#EF4444]" /> Ping DGI — Échec</>
                          ) : (
                            <><Wifi className="h-4 w-4 mr-2" /> Tester la connexion DGI</>
                          )}
                        </Button>
                        {pingResult && !pingResult.ok && (
                          <p className="text-xs text-[#EF4444] px-1">{pingResult.error}</p>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            )}

            {/* ═══════════════ ONGLET TESTS API ═══════════════ */}
            {activeTab === "tests" && (
              <div className="space-y-4">
                <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 text-sm text-blue-800 dark:text-blue-200">
                  <p className="font-semibold">Mode test — environnement sandbox DGI</p>
                  <p className="text-xs mt-0.5">
                    Ces tests envoient de vraies requêtes à l'URL test DGI ({settings?.api?.base_url_test}).
                    {!settings?.api?.api_key_configured && " ⚠️ API KEY non configurée — les tests échoueront avec 401."}
                  </p>
                </div>

                {lastTestInvoiceId && (
                  <div className="text-xs text-muted-foreground px-1">
                    Dernier invoiceId DGI : <code className="bg-muted px-1.5 py-0.5 rounded">{lastTestInvoiceId}</code>
                    (utilisé pour le test d'avoir)
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {TEST_BUTTONS.map(test => {
                    const Icon = test.icon;
                    const result = testResults[test.id];
                    const running = testRunning[test.id];
                    return (
                      <Card key={test.id} className="flex flex-col" data-testid={`test-card-${test.id}`}>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm flex items-center gap-2">
                            <span className={`p-1.5 rounded-md ${test.color}`}>
                              <Icon className="h-4 w-4 text-white" />
                            </span>
                            {test.label}
                          </CardTitle>
                          <CardDescription className="text-xs">{test.description}</CardDescription>
                        </CardHeader>
                        <CardContent className="flex-1 flex flex-col justify-between gap-3">
                          <Button
                            onClick={() => runTest(test.id, test.run)}
                            disabled={running}
                            size="sm"
                            variant="outline"
                            className="w-full"
                            data-testid={`btn-test-${test.id}`}
                          >
                            {running ? "En cours…" : "Lancer le test"}
                          </Button>

                          {result && (
                            <div className={`p-2 rounded text-xs border ${
                              result.ok
                                ? "bg-[#10B981]/10 border-[#10B981]/40 text-[#10B981]"
                                : "bg-[#EF4444]/10 border-[#EF4444]/40 text-[#EF4444]"
                            }`} data-testid={`test-result-${test.id}`}>
                              <p className="font-semibold">{result.ok ? "✓ Succès" : "✗ Échec"} — {result.elapsed}ms</p>
                              {result.ok && result.data && (
                                <pre className="mt-1 text-[10px] overflow-auto max-h-32 text-foreground bg-background/50 p-1 rounded whitespace-pre-wrap">
                                  {JSON.stringify(result.data, null, 2)}
                                </pre>
                              )}
                              {!result.ok && (
                                <p className="mt-1 break-words">{result.error}</p>
                              )}
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  );
}

// ─── Composant FormField ────────────────────────────────────────────────────
function FormField({ label, field, form, setForm, editMode, mono, placeholder }) {
  if (!editMode) {
    return (
      <div className="flex items-center justify-between border-b py-2 gap-3">
        <span className="text-xs text-muted-foreground">{label}</span>
        <span className={`text-right text-sm ${mono ? "font-mono text-xs" : ""} max-w-[60%] truncate`}>
          {form[field] || "—"}
        </span>
      </div>
    );
  }
  return (
    <div className="space-y-1">
      <Label className="text-xs font-medium">{label}</Label>
      <Input
        value={form[field] || ""}
        onChange={e => setForm(p => ({ ...p, [field]: e.target.value }))}
        placeholder={placeholder || label}
        className={`h-8 text-sm ${mono ? "font-mono text-xs" : ""}`}
      />
    </div>
  );
}
