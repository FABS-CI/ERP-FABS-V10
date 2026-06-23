/**
 * Page FNE — Nouvelle soumission (Sprint 2 V10)
 * Formulaire de création + prévisualisation JSON + soumission DGI
 */
import React, { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Send, Plus, Trash2, Eye, Code2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";
import { submitFNEInvoice } from "../services/fneApi";

const EMPTY_ITEM = { reference: "", description: "", quantity: 1, amount: 0, discount: 0, measurementUnit: "unité", taxes: ["TVA"] };

export default function FNEInvoiceNew() {
  const navigate = useNavigate();
  const [showJson, setShowJson] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    invoiceType: "sale",
    paymentMethod: "cash",
    template: "B2B",
    clientNcc: "",
    clientCompanyName: "",
    clientPhone: "",
    clientEmail: "",
    clientSellerName: "EDITIONS FABS-CI",
    pointOfSale: "01",
    establishment: "Siège Social",
    commercialMessage: "",
    footer: "",
    foreignCurrency: "",
    foreignCurrencyRate: 0,
    discount: 0,
    items: [{ ...EMPTY_ITEM }],
  });

  const totals = useMemo(() => {
    const subtotal = form.items.reduce((sum, it) => sum + (Number(it.quantity) || 0) * (Number(it.amount) || 0), 0);
    const itemDiscounts = form.items.reduce((sum, it) => sum + (Number(it.discount) || 0), 0);
    const afterItemDisc = subtotal - itemDiscounts;
    const globalDisc = Number(form.discount) || 0;
    const ht = afterItemDisc - globalDisc;
    const tva = Math.round(ht * 0.18);
    const ttc = ht + tva;
    return { subtotal, itemDiscounts, globalDisc, ht, tva, ttc };
  }, [form]);

  const updateItem = (idx, field, value) => {
    setForm((prev) => {
      const items = [...prev.items];
      items[idx] = { ...items[idx], [field]: value };
      return { ...prev, items };
    });
  };

  const addItem = () => setForm((p) => ({ ...p, items: [...p.items, { ...EMPTY_ITEM }] }));
  const removeItem = (idx) => setForm((p) => ({ ...p, items: p.items.filter((_, i) => i !== idx) }));

  const handleSubmit = async () => {
    if (!form.clientCompanyName || !form.clientPhone) {
      toast.error("Le nom et le téléphone du client sont obligatoires");
      return;
    }
    if (form.items.some((it) => !it.description || !it.amount)) {
      toast.error("Chaque ligne doit avoir une description et un montant");
      return;
    }
    setSubmitting(true);
    try {
      const r = await submitFNEInvoice(form);
      if (r.success) {
        toast.success("Facture soumise à la DGI avec succès");
        navigate(`/fne/invoices/${r.data?.invoice_id || r.data?.id || ""}`);
      } else {
        toast.error(r.message || "Échec de la soumission");
      }
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erreur lors de la soumission FNE");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="fne-invoice-new">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <Button variant="ghost" onClick={() => navigate("/fne")} data-testid="btn-back">
            <ArrowLeft className="h-4 w-4 mr-2" /> Retour FNE
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setShowJson((s) => !s)} data-testid="btn-toggle-json">
              {showJson ? <Eye className="h-4 w-4 mr-2" /> : <Code2 className="h-4 w-4 mr-2" />}
              {showJson ? "Vue formulaire" : "Prévisualiser JSON"}
            </Button>
            <Button
              className="bg-[#FF6200] hover:bg-[#FF6200]/90 text-white"
              onClick={handleSubmit}
              disabled={submitting}
              data-testid="btn-submit-fne"
            >
              <Send className="h-4 w-4 mr-2" />
              {submitting ? "Soumission…" : "Soumettre à la DGI"}
            </Button>
          </div>
        </div>

        {showJson ? (
          <Card>
            <CardHeader>
              <CardTitle>Prévisualisation JSON (format DGI)</CardTitle>
              <CardDescription>Payload qui sera envoyé à l&apos;API FNE</CardDescription>
            </CardHeader>
            <CardContent>
              <pre className="bg-[#0A2540] text-[#10B981] text-xs p-4 rounded-lg overflow-auto max-h-[600px]" data-testid="fne-json-preview">
                {JSON.stringify(form, null, 2)}
              </pre>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Informations client</CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <Field label="Type facture">
                  <Select value={form.invoiceType} onValueChange={(v) => setForm({ ...form, invoiceType: v })}>
                    <SelectTrigger data-testid="select-type"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="sale">Vente</SelectItem>
                      <SelectItem value="purchase">Achat</SelectItem>
                    </SelectContent>
                  </Select>
                </Field>
                <Field label="Template">
                  <Select value={form.template} onValueChange={(v) => setForm({ ...form, template: v })}>
                    <SelectTrigger data-testid="select-template"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="B2B">B2B</SelectItem>
                      <SelectItem value="B2F">B2F</SelectItem>
                    </SelectContent>
                  </Select>
                </Field>
                <Field label="Mode de paiement">
                  <Select value={form.paymentMethod} onValueChange={(v) => setForm({ ...form, paymentMethod: v })}>
                    <SelectTrigger data-testid="select-payment"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="cash">Espèces</SelectItem>
                      <SelectItem value="mobile-money">Mobile Money</SelectItem>
                      <SelectItem value="bank-transfer">Virement</SelectItem>
                    </SelectContent>
                  </Select>
                </Field>
                <Field label="NCC client (optionnel)">
                  <Input data-testid="input-client-ncc" value={form.clientNcc} onChange={(e) => setForm({ ...form, clientNcc: e.target.value })} />
                </Field>
                <Field label="Nom client *">
                  <Input data-testid="input-client-name" value={form.clientCompanyName} onChange={(e) => setForm({ ...form, clientCompanyName: e.target.value })} />
                </Field>
                <Field label="Téléphone client *">
                  <Input data-testid="input-client-phone" value={form.clientPhone} onChange={(e) => setForm({ ...form, clientPhone: e.target.value })} />
                </Field>
                <Field label="Email client (optionnel)">
                  <Input type="email" data-testid="input-client-email" value={form.clientEmail} onChange={(e) => setForm({ ...form, clientEmail: e.target.value })} />
                </Field>
                <Field label="Vendeur">
                  <Input data-testid="input-seller" value={form.clientSellerName} onChange={(e) => setForm({ ...form, clientSellerName: e.target.value })} />
                </Field>
                <Field label="Message commercial">
                  <Input data-testid="input-message" value={form.commercialMessage} onChange={(e) => setForm({ ...form, commercialMessage: e.target.value })} />
                </Field>
                <Field label="Pied de page">
                  <Input data-testid="input-footer" value={form.footer} onChange={(e) => setForm({ ...form, footer: e.target.value })} />
                </Field>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Récapitulatif</CardTitle>
                <CardDescription>Calcul automatique des totaux</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <Row label="Sous-total" value={totals.subtotal} />
                <Row label="Remises lignes" value={-totals.itemDiscounts} />
                <Row label="Remise globale" value={-totals.globalDisc} />
                <Row label="Total HT" value={totals.ht} bold />
                <Row label="TVA (18%)" value={totals.tva} />
                <div className="border-t pt-2 mt-2">
                  <Row label="TOTAL TTC" value={totals.ttc} bold large />
                </div>
                <Field label="Remise globale (FCFA)" className="mt-3">
                  <Input
                    type="number"
                    min={0}
                    data-testid="input-global-discount"
                    value={form.discount}
                    onChange={(e) => setForm({ ...form, discount: Number(e.target.value) || 0 })}
                  />
                </Field>
              </CardContent>
            </Card>

            <Card className="lg:col-span-3">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Lignes de facture</CardTitle>
                  <CardDescription>{form.items.length} ligne(s)</CardDescription>
                </div>
                <Button variant="outline" onClick={addItem} data-testid="btn-add-line">
                  <Plus className="h-4 w-4 mr-2" /> Ajouter une ligne
                </Button>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm" data-testid="fne-items-table">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2 px-2 w-32">Référence</th>
                        <th className="text-left py-2 px-2">Description</th>
                        <th className="text-right py-2 px-2 w-20">Qté</th>
                        <th className="text-right py-2 px-2 w-32">PU (FCFA)</th>
                        <th className="text-right py-2 px-2 w-28">Remise</th>
                        <th className="text-right py-2 px-2 w-32">Total</th>
                        <th className="py-2 px-2 w-10"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {form.items.map((it, idx) => (
                        <tr key={idx} className="border-b" data-testid={`fne-line-${idx}`}>
                          <td className="py-1 px-1">
                            <Input value={it.reference} onChange={(e) => updateItem(idx, "reference", e.target.value)} />
                          </td>
                          <td className="py-1 px-1">
                            <Input value={it.description} onChange={(e) => updateItem(idx, "description", e.target.value)} />
                          </td>
                          <td className="py-1 px-1">
                            <Input type="number" min={1} className="text-right" value={it.quantity} onChange={(e) => updateItem(idx, "quantity", Number(e.target.value) || 0)} />
                          </td>
                          <td className="py-1 px-1">
                            <Input type="number" min={0} className="text-right" value={it.amount} onChange={(e) => updateItem(idx, "amount", Number(e.target.value) || 0)} />
                          </td>
                          <td className="py-1 px-1">
                            <Input type="number" min={0} className="text-right" value={it.discount} onChange={(e) => updateItem(idx, "discount", Number(e.target.value) || 0)} />
                          </td>
                          <td className="py-2 px-2 text-right font-semibold tabular-nums">
                            {new Intl.NumberFormat("fr-FR").format((it.quantity * it.amount) - (it.discount || 0))}
                          </td>
                          <td className="py-1 px-1 text-center">
                            {form.items.length > 1 && (
                              <button onClick={() => removeItem(idx)} className="text-[#EF4444]" data-testid={`btn-remove-line-${idx}`}>
                                <Trash2 className="h-4 w-4" />
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

function Field({ label, children, className = "" }) {
  return (
    <div className={`space-y-1.5 ${className}`}>
      <Label className="text-xs text-muted-foreground">{label}</Label>
      {children}
    </div>
  );
}

function Row({ label, value, bold, large }) {
  return (
    <div className={`flex justify-between ${large ? "text-base" : ""}`}>
      <span className="text-muted-foreground">{label}</span>
      <span className={`tabular-nums ${bold ? "font-bold text-[#0A2540] dark:text-white" : ""}`}>
        {new Intl.NumberFormat("fr-FR").format(value)} FCFA
      </span>
    </div>
  );
}
