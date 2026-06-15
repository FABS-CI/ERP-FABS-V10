/**
 * Page FNE — Paramètres (Sprint 2 V10)
 * Affiche la configuration FNE en cours + bouton ping DGI
 */
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Wifi, WifiOff, ShieldCheck, AlertTriangle, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import DashboardLayout from "../components/layout/DashboardLayout";
import { getFNESettings, pingDGI } from "../services/fneApi";

export default function FNESettings() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [settings, setSettings] = useState(null);
  const [pingResult, setPingResult] = useState(null);
  const [pinging, setPinging] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        setSettings(await getFNESettings());
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handlePing = async () => {
    setPinging(true);
    try {
      const r = await pingDGI();
      setPingResult(r);
      if (r.ok) toast.success(`API DGI joignable (${r.elapsed_ms} ms)`);
      else toast.error(`API DGI injoignable : ${r.error}`);
    } catch (e) {
      toast.error("Erreur ping");
    } finally {
      setPinging(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="fne-settings-page">
        <Button variant="ghost" onClick={() => navigate("/fne")} data-testid="btn-back">
          <ArrowLeft className="h-4 w-4 mr-2" /> Retour FNE
        </Button>

        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <ShieldCheck className="h-8 w-8 text-[#FF6200]" />
            Paramètres FNE
          </h1>
          <p className="text-muted-foreground mt-1">Configuration de l&apos;intégration DGI Côte d&apos;Ivoire</p>
        </div>

        {loading ? (
          <Skeleton className="h-96 w-full" />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Entreprise */}
            <Card>
              <CardHeader>
                <CardTitle>Entreprise (EDITIONS FABS-CI)</CardTitle>
                <CardDescription>Informations officielles transmises à la DGI</CardDescription>
              </CardHeader>
              <CardContent>
                <dl className="space-y-2 text-sm">
                  <Row label="Nom" value={settings?.company?.name} />
                  <Row label="NCC" value={settings?.company?.ncc} mono />
                  <Row label="IDU" value={settings?.company?.idu} mono />
                  <Row label="Régime d'imposition" value={settings?.company?.regime} />
                  <Row label="Secteur d'activité" value={settings?.company?.secteur} />
                  <Row label="Direction de rattachement" value={settings?.company?.dran} />
                  <Row label="Centre d'impôts" value={settings?.company?.centre_impots} />
                  <Row label="Point de vente" value={settings?.company?.point_of_sale} />
                  <Row label="Établissement" value={settings?.company?.establishment} />
                </dl>
              </CardContent>
            </Card>

            {/* API */}
            <Card>
              <CardHeader className="flex flex-row items-start justify-between">
                <div>
                  <CardTitle>API DGI</CardTitle>
                  <CardDescription>État de l&apos;intégration</CardDescription>
                </div>
                <Badge className={settings?.api?.use_production ? "bg-[#10B981] text-white" : "bg-[#F59E0B] text-white"}>
                  {settings?.api?.use_production ? "PRODUCTION" : "TEST / SANDBOX"}
                </Badge>
              </CardHeader>
              <CardContent>
                <dl className="space-y-2 text-sm">
                  <Row label="URL test" value={settings?.api?.base_url_test} mono />
                  <Row label="URL production" value={settings?.api?.base_url_prod || "— (non transmise par DGI)"} mono />
                  <Row label="API Key" value={
                    settings?.api?.api_key_configured
                      ? <span className="inline-flex items-center gap-1 text-[#10B981]"><CheckCircle2 className="h-4 w-4" /> Configurée ({settings.api.api_key_masked})</span>
                      : <span className="inline-flex items-center gap-1 text-[#F59E0B]"><AlertTriangle className="h-4 w-4" /> Non configurée — mode sandbox</span>
                  } />
                </dl>

                <div className="mt-6 space-y-3">
                  <Button onClick={handlePing} disabled={pinging} className="w-full" data-testid="btn-ping-dgi">
                    {pinging ? "Test en cours…" :
                     pingResult?.ok ? <><Wifi className="h-4 w-4 mr-2" /> Ping DGI</> :
                     pingResult?.ok === false ? <><WifiOff className="h-4 w-4 mr-2" /> Ping DGI</> :
                     <><Wifi className="h-4 w-4 mr-2" /> Tester la connexion DGI</>}
                  </Button>
                  {pingResult && (
                    <div className={`p-3 rounded-lg text-sm border ${pingResult.ok ? "bg-[#10B981]/10 border-[#10B981]/40" : "bg-[#EF4444]/10 border-[#EF4444]/40"}`} data-testid="ping-result">
                      <p className="font-semibold">{pingResult.ok ? "✓ API joignable" : "✗ Échec connexion"}</p>
                      <p className="text-xs text-muted-foreground mt-1">URL : <code>{pingResult.url}</code></p>
                      {pingResult.elapsed_ms != null && <p className="text-xs">Latence : {pingResult.elapsed_ms} ms</p>}
                      {pingResult.status != null && <p className="text-xs">Status HTTP : {pingResult.status}</p>}
                      {pingResult.error && <p className="text-xs text-[#EF4444]">{pingResult.error}</p>}
                    </div>
                  )}
                </div>

                {!settings?.api?.api_key_configured && (
                  <div className="mt-4 p-3 rounded-lg bg-[#F59E0B]/10 border border-[#F59E0B]/40 text-xs" data-testid="config-warning">
                    <p className="font-semibold flex items-center gap-1 text-[#0A2540] dark:text-white">
                      <AlertTriangle className="h-4 w-4 text-[#F59E0B]" />
                      Configuration requise
                    </p>
                    <p className="mt-1 text-muted-foreground">
                      Renseignez la variable d&apos;environnement <code className="bg-white dark:bg-[#0A2540] px-1 rounded">DGI_API_KEY</code> dans <code>/app/backend/.env</code> puis redémarrez le backend pour activer le mode production.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

function Row({ label, value, mono }) {
  return (
    <div className="flex items-center justify-between border-b py-2 gap-3">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className={`text-right ${mono ? "font-mono text-xs" : ""} text-[#0A2540] dark:text-white max-w-[60%] truncate`}>
        {value || "—"}
      </dd>
    </div>
  );
}
