/**
 * Page Paie — Sprint 6b V10
 * Calculs ITS / CNPS / CMU + bulletins de paie Côte d'Ivoire
 */
import React, { useState, useEffect, useMemo, useCallback } from "react";
import { Plus, Wallet, Calculator, FileText, RefreshCw, Receipt, Building2 } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "../components/ui/dialog";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";
import API_BASE_URL from "../config/api";
import { calculerPaie, creerBulletin, listerBulletins } from "../services/paieApi";

const fmt = (v) => new Intl.NumberFormat("fr-FR").format(Math.round(v || 0)) + " FCFA";

const currentPeriod = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
};

const EMPTY_FORM = {
  employe_id: "",
  periode: currentPeriod(),
  salaire_brut: 200000,
  primes: 0,
  avantages_nature: 0,
  retenues_diverses: 0,
  notes: "",
};

export default function Paie() {
  const [bulletins, setBulletins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [employes, setEmployes] = useState([]);
  const [preview, setPreview] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await listerBulletins({ limit: 100 });
      setBulletins(r.items || []);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openCreate = async () => {
    setForm(EMPTY_FORM);
    setPreview(null);
    try {
      const r = await axios.get(`${API_BASE_URL}/rh/employes`);
      const data = Array.isArray(r.data) ? r.data : r.data?.items || [];
      setEmployes(data);
    } catch { setEmployes([]); }
    setShowModal(true);
  };

  // Live preview du calcul (debounced)
  useEffect(() => {
    if (!showModal) return;
    if (!form.salaire_brut || form.salaire_brut <= 0) {
      setPreview(null); return;
    }
    const handle = setTimeout(async () => {
      setPreviewLoading(true);
      try {
        const r = await calculerPaie({
          salaire_brut: Number(form.salaire_brut),
          primes: Number(form.primes),
          avantages_nature: Number(form.avantages_nature),
          retenues_diverses: Number(form.retenues_diverses),
        });
        setPreview(r);
      } catch (e) {
        setPreview(null);
      } finally { setPreviewLoading(false); }
    }, 350);
    return () => clearTimeout(handle);
  }, [form.salaire_brut, form.primes, form.avantages_nature, form.retenues_diverses, showModal]);

  const handleSave = async () => {
    if (!form.employe_id) return toast.error("Sélectionnez un employé");
    if (!form.salaire_brut || form.salaire_brut <= 0) return toast.error("Salaire brut requis");
    setSaving(true);
    try {
      const b = await creerBulletin({
        employe_id: form.employe_id,
        periode: form.periode,
        salaire_brut: Number(form.salaire_brut),
        primes: Number(form.primes),
        avantages_nature: Number(form.avantages_nature),
        retenues_diverses: Number(form.retenues_diverses),
        notes: form.notes || undefined,
      });
      toast.success(`Bulletin ${b.bulletin_id} créé`);
      setShowModal(false);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erreur création bulletin");
    } finally { setSaving(false); }
  };

  // KPI agrégés
  const kpi = useMemo(() => {
    const totalNet = bulletins.reduce((s, b) => s + (b.calcul?.net_a_payer || 0), 0);
    const totalBrut = bulletins.reduce((s, b) => s + (b.calcul?.brut_imposable || 0), 0);
    const totalCharges = bulletins.reduce(
      (s, b) => s + (b.calcul?.charges_patronales?.total || 0), 0,
    );
    return {
      count: bulletins.length,
      totalBrut, totalNet, totalCharges,
      coutTotal: totalBrut + totalCharges,
    };
  }, [bulletins]);

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="paie-page">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
              <Wallet className="h-8 w-8 text-[#FF6200]" />
              Paie
            </h1>
            <p className="text-muted-foreground mt-1">
              Bulletins de paie · Calculs <strong>ITS / CNPS / CMU</strong> conformes à la fiscalité ivoirienne
            </p>
          </div>
          <Button onClick={openCreate} className="bg-[#FF6200] hover:bg-[#FF6200]/90 text-white" data-testid="btn-new-bulletin">
            <Plus className="h-4 w-4 mr-2" /> Nouveau bulletin
          </Button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <KPI label="Bulletins" value={kpi.count} icon={Receipt} color="#0A2540" testId="kpi-count" />
          <KPI label="Masse salariale brute" value={fmt(kpi.totalBrut)} icon={Wallet} color="#0A2540" testId="kpi-brut" small />
          <KPI label="Net versé" value={fmt(kpi.totalNet)} icon={Calculator} color="#10B981" testId="kpi-net" small />
          <KPI label="Coût employeur" value={fmt(kpi.coutTotal)} icon={Building2} color="#FF6200" testId="kpi-cout" small />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Bulletins émis</CardTitle>
            <CardDescription>Historique des bulletins de paie générés</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? <Skeleton className="h-40 w-full" /> :
             bulletins.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground" data-testid="bulletins-empty">
                <FileText className="h-12 w-12 mx-auto mb-3 opacity-30" />
                <p>Aucun bulletin de paie pour l&apos;instant.</p>
                <Button onClick={openCreate} className="mt-4 bg-[#FF6200] text-white hover:bg-[#FF6200]/90" data-testid="btn-empty-create">
                  <Plus className="h-4 w-4 mr-2" /> Émettre le premier bulletin
                </Button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm" data-testid="bulletins-table">
                  <thead><tr className="border-b">
                    <th className="text-left py-3 px-2">Bulletin</th>
                    <th className="text-left py-3 px-2">Employé</th>
                    <th className="text-left py-3 px-2">Période</th>
                    <th className="text-right py-3 px-2">Brut</th>
                    <th className="text-right py-3 px-2">CNPS</th>
                    <th className="text-right py-3 px-2">ITS</th>
                    <th className="text-right py-3 px-2 font-bold">Net</th>
                    <th className="text-center py-3 px-2">Statut</th>
                  </tr></thead>
                  <tbody>
                    {bulletins.map((b) => (
                      <tr key={b.bulletin_id} className="border-b hover:bg-muted/30" data-testid={`bulletin-${b.bulletin_id}`}>
                        <td className="py-3 px-2 font-mono text-xs">{b.bulletin_id}</td>
                        <td className="py-3 px-2 font-medium">{b.employe_nom}</td>
                        <td className="py-3 px-2"><Badge className="bg-[#0A2540] text-white">{b.periode}</Badge></td>
                        <td className="py-3 px-2 text-right tabular-nums">{fmt(b.calcul?.brut_imposable)}</td>
                        <td className="py-3 px-2 text-right tabular-nums text-[#F59E0B]">{fmt(b.calcul?.cnps_salarial)}</td>
                        <td className="py-3 px-2 text-right tabular-nums text-[#F59E0B]">{fmt(b.calcul?.its)}</td>
                        <td className="py-3 px-2 text-right tabular-nums font-bold text-[#10B981]">{fmt(b.calcul?.net_a_payer)}</td>
                        <td className="py-3 px-2 text-center"><Badge className="bg-gray-400 text-white">{b.statut}</Badge></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Modale création */}
        <Dialog open={showModal} onOpenChange={setShowModal}>
          <DialogContent className="sm:max-w-[920px] max-h-[92vh] overflow-y-auto" data-testid="bulletin-modal">
            <DialogHeader>
              <DialogTitle>Nouveau bulletin de paie</DialogTitle>
              <DialogDescription>
                Calcul automatique ITS / CNPS (6,3 % salarié) / CMU (1 000 FCFA) selon la fiscalité ivoirienne
              </DialogDescription>
            </DialogHeader>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 py-2">
              <div className="space-y-3">
                <div className="space-y-1.5">
                  <Label>Employé *</Label>
                  <Select value={form.employe_id} onValueChange={(v) => setForm({ ...form, employe_id: v })}>
                    <SelectTrigger data-testid="select-employe"><SelectValue placeholder="Choisir un employé" /></SelectTrigger>
                    <SelectContent>
                      {employes.map((e) => (
                        <SelectItem key={e.employe_id} value={e.employe_id}>
                          {e.matricule} — {e.nom} {e.prenoms}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label>Période *</Label>
                  <Input type="month" data-testid="input-periode" value={form.periode} onChange={(e) => setForm({ ...form, periode: e.target.value })} />
                </div>
                <div className="space-y-1.5">
                  <Label>Salaire brut (FCFA) *</Label>
                  <Input type="number" min={0} data-testid="input-brut" value={form.salaire_brut} onChange={(e) => setForm({ ...form, salaire_brut: e.target.value })} />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1.5">
                    <Label>Primes</Label>
                    <Input type="number" min={0} data-testid="input-primes" value={form.primes} onChange={(e) => setForm({ ...form, primes: e.target.value })} />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Avantages nature</Label>
                    <Input type="number" min={0} data-testid="input-avantages" value={form.avantages_nature} onChange={(e) => setForm({ ...form, avantages_nature: e.target.value })} />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <Label>Retenues diverses (acomptes, prêts…)</Label>
                  <Input type="number" min={0} data-testid="input-retenues" value={form.retenues_diverses} onChange={(e) => setForm({ ...form, retenues_diverses: e.target.value })} />
                </div>
                <div className="space-y-1.5">
                  <Label>Notes (optionnel)</Label>
                  <Textarea rows={2} data-testid="input-notes" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
                </div>
              </div>

              {/* Live preview */}
              <Card className="bg-gradient-to-br from-[#0A2540] to-[#0A2540]/80 text-white border-0" data-testid="preview-card">
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2 text-white">
                    <Calculator className="h-5 w-5 text-[#FF6200]" />
                    Calcul en temps réel
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {previewLoading && !preview ? (
                    <Skeleton className="h-72 w-full bg-white dark:bg-[#0b1e30]/10" />
                  ) : !preview ? (
                    <p className="text-white/60 text-sm py-8 text-center">Saisissez un salaire brut pour voir le calcul</p>
                  ) : (
                    <div className="space-y-1.5 text-sm">
                      <PreviewRow label="Salaire brut" value={fmt(preview.salaire_brut)} />
                      {preview.primes > 0 && <PreviewRow label="Primes" value={`+${fmt(preview.primes)}`} />}
                      {preview.avantages_nature > 0 && <PreviewRow label="Avantages nature" value={`+${fmt(preview.avantages_nature)}`} />}
                      <div className="border-t border-white/20 my-2"></div>
                      <PreviewRow label="Brut imposable" value={fmt(preview.brut_imposable)} bold />
                      <div className="border-t border-white/20 my-2"></div>
                      <PreviewRow label="CNPS salarié (6,3 %)" value={`−${fmt(preview.cnps_salarial)}`} color="#F59E0B" />
                      <PreviewRow label="ITS (barème progressif)" value={`−${fmt(preview.its)}`} color="#F59E0B" />
                      <PreviewRow label="CMU" value={`−${fmt(preview.cmu)}`} color="#F59E0B" />
                      {preview.retenues_diverses > 0 && (
                        <PreviewRow label="Retenues diverses" value={`−${fmt(preview.retenues_diverses)}`} color="#F59E0B" />
                      )}
                      <PreviewRow label="Total retenues" value={`−${fmt(preview.total_retenues)}`} color="#F59E0B" bold />
                      <div className="border-t-2 border-[#FF6200] my-2"></div>
                      <div className="flex justify-between items-center py-2">
                        <span className="font-semibold">NET À PAYER</span>
                        <span className="text-2xl font-bold text-[#10B981] tabular-nums" data-testid="preview-net">
                          {fmt(preview.net_a_payer)}
                        </span>
                      </div>
                      <div className="border-t border-white/20 my-2"></div>
                      <p className="text-xs text-white/60 uppercase mt-3">Charges employeur</p>
                      <PreviewRow label="CNPS patronal (7,7 %)" value={fmt(preview.charges_patronales.cnps_patronal)} small />
                      <PreviewRow label="Accidents travail (2 %)" value={fmt(preview.charges_patronales.accidents_travail)} small />
                      <PreviewRow label="Prestations famille (5,75 %)" value={fmt(preview.charges_patronales.prestations_famille)} small />
                      <div className="flex justify-between pt-2 mt-2 border-t border-white/20">
                        <span className="text-xs font-semibold">Coût total employeur</span>
                        <span className="font-bold text-[#FF6200] tabular-nums" data-testid="preview-cout">
                          {fmt(preview.cout_total_employeur)}
                        </span>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowModal(false)} data-testid="btn-cancel">Annuler</Button>
              <Button onClick={handleSave} disabled={saving || !form.employe_id} className="bg-[#FF6200] hover:bg-[#FF6200]/90 text-white" data-testid="btn-save">
                {saving ? "Enregistrement…" : "Émettre le bulletin"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}

function KPI({ label, value, icon: Icon, color, testId, small }) {
  return (
    <Card data-testid={testId}>
      <CardContent className="pt-5 pb-4 flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${color}20` }}>
          <Icon className="h-5 w-5" style={{ color }} />
        </div>
        <div className="flex-1">
          <p className="text-xs text-muted-foreground uppercase">{label}</p>
          <p className={`${small ? "text-base" : "text-2xl"} font-bold text-[#0A2540] dark:text-white`}>{value}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function PreviewRow({ label, value, color, bold, small }) {
  return (
    <div className={`flex justify-between ${small ? "text-xs" : "text-sm"}`}>
      <span className="text-white/80">{label}</span>
      <span className={`tabular-nums ${bold ? "font-bold" : ""}`} style={color ? { color } : {}}>{value}</span>
    </div>
  );
}
