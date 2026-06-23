/**
 * Page Fournisseurs — Liste + Modale création/édition (Sprint 3 V10)
 */
import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Search, Building2, Phone, Mail, MapPin, Edit, Trash2, Eye } from "lucide-react";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "../components/ui/dialog";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";
import { useAuth } from "../hooks/useAuth";
import { can } from "../constants/permissions";
import {
  listFournisseurs, createFournisseur, updateFournisseur, deleteFournisseur,
} from "../services/fournisseursApi";

const EMPTY = { nom: "", contact: "", telephone: "", email: "", adresse: "" };

export default function Fournisseurs() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);

  const canWrite = user && can(user.role, "fournisseurs");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listFournisseurs({ limit: 200 });
      setItems(Array.isArray(data) ? data : data?.items || []);
    } catch (e) {
      console.error(e);
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = items.filter((f) => {
    if (!search) return true;
    const s = search.toLowerCase();
    return [f.nom, f.contact, f.email, f.telephone, f.reference, f.adresse]
      .some((v) => (v || "").toLowerCase().includes(s));
  });

  const openCreate = () => {
    setEditing(null);
    setForm(EMPTY);
    setShowModal(true);
  };

  const openEdit = (f) => {
    setEditing(f);
    setForm({
      nom: f.nom || "",
      contact: f.contact || "",
      telephone: f.telephone || "",
      email: f.email || "",
      adresse: f.adresse || "",
    });
    setShowModal(true);
  };

  const handleSave = async () => {
    if (!form.nom || form.nom.length < 2) {
      toast.error("Le nom du fournisseur est obligatoire (≥ 2 caractères)");
      return;
    }
    setSaving(true);
    try {
      if (editing) {
        await updateFournisseur(editing.fournisseur_id, form);
        toast.success("Fournisseur mis à jour");
      } else {
        await createFournisseur(form);
        toast.success("Fournisseur créé");
      }
      setShowModal(false);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erreur lors de l'enregistrement");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (f) => {
    if (!window.confirm(`Supprimer le fournisseur "${f.nom}" ?`)) return;
    try {
      await deleteFournisseur(f.fournisseur_id);
      toast.success("Fournisseur supprimé");
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erreur lors de la suppression");
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="fournisseurs-page">
        {/* Header */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
              <Building2 className="h-8 w-8 text-[#FF6200]" />
              Fournisseurs
            </h1>
            <p className="text-muted-foreground mt-1">
              Annuaire et suivi de vos partenaires d&apos;approvisionnement
            </p>
          </div>
          {canWrite && (
            <Button
              className="bg-blue-600 hover:bg-blue-600/90 text-white"
              onClick={openCreate}
              data-testid="btn-create-fournisseur"
            >
              <Plus className="h-4 w-4 mr-2" /> Nouveau fournisseur
            </Button>
          )}
        </div>

        {/* KPI rapides */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <KPICard label="Total" value={items.length} color="text-[#0A2540]" testId="kpi-total" />
          <KPICard
            label="Actifs"
            value={items.filter((f) => f.actif).length}
            color="text-[#10B981]"
            testId="kpi-actifs"
          />
          <KPICard
            label="Avec email"
            value={items.filter((f) => f.email).length}
            color="text-[#0A2540]"
            testId="kpi-emails"
          />
          <KPICard
            label="Avec téléphone"
            value={items.filter((f) => f.telephone).length}
            color="text-[#FF6200]"
            testId="kpi-telephones"
          />
        </div>

        {/* Search */}
        <Card>
          <CardContent className="pt-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                data-testid="fournisseurs-search"
                type="search"
                placeholder="Rechercher par nom, contact, email, téléphone, référence…"
                className="pl-9"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Liste */}
        <Card>
          <CardHeader>
            <CardTitle>Liste des fournisseurs</CardTitle>
            <CardDescription>
              {filtered.length} fournisseur{filtered.length > 1 ? "s" : ""} affiché{filtered.length > 1 ? "s" : ""}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
              </div>
            ) : filtered.length === 0 ? (
              <div className="text-center py-16 text-muted-foreground" data-testid="fournisseurs-empty">
                <Building2 className="h-12 w-12 mx-auto mb-3 opacity-30" />
                <p>{search ? "Aucun fournisseur ne correspond à la recherche." : "Aucun fournisseur enregistré pour l'instant."}</p>
                {!search && canWrite && (
                  <Button
                    onClick={openCreate}
                    className="mt-4 bg-blue-600 hover:bg-blue-600/90 text-white"
                    data-testid="btn-empty-create"
                  >
                    <Plus className="h-4 w-4 mr-2" /> Créer le premier fournisseur
                  </Button>
                )}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm" data-testid="fournisseurs-table">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-2 w-32">Référence</th>
                      <th className="text-left py-3 px-2">Nom</th>
                      <th className="text-left py-3 px-2">Contact</th>
                      <th className="text-left py-3 px-2">Téléphone</th>
                      <th className="text-left py-3 px-2">Email</th>
                      <th className="text-center py-3 px-2">Statut</th>
                      <th className="text-right py-3 px-2 w-32">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((f) => (
                      <tr key={f.fournisseur_id} className="border-b hover:bg-muted/50" data-testid={`fournisseur-row-${f.fournisseur_id}`}>
                        <td className="py-3 px-2 font-mono text-xs">{f.reference}</td>
                        <td className="py-3 px-2 font-medium text-[#0A2540] dark:text-white">{f.nom}</td>
                        <td className="py-3 px-2">{f.contact || "—"}</td>
                        <td className="py-3 px-2">
                          {f.telephone ? (
                            <a href={`tel:${f.telephone}`} className="hover:text-[#FF6200] inline-flex items-center gap-1">
                              <Phone className="h-3 w-3" /> {f.telephone}
                            </a>
                          ) : "—"}
                        </td>
                        <td className="py-3 px-2">
                          {f.email ? (
                            <a href={`mailto:${f.email}`} className="hover:text-[#FF6200] inline-flex items-center gap-1 truncate max-w-[200px]">
                              <Mail className="h-3 w-3" /> {f.email}
                            </a>
                          ) : "—"}
                        </td>
                        <td className="py-3 px-2 text-center">
                          <Badge className={f.actif ? "bg-[#10B981] text-white" : "bg-gray-400 text-white"}>
                            {f.actif ? "Actif" : "Inactif"}
                          </Badge>
                        </td>
                        <td className="py-3 px-2 text-right">
                          <div className="flex justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => navigate(`/fournisseurs/${f.fournisseur_id}`)}
                              data-testid={`btn-view-${f.fournisseur_id}`}
                              title="Voir la fiche"
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                            {canWrite && (
                              <>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => openEdit(f)}
                                  data-testid={`btn-edit-${f.fournisseur_id}`}
                                  title="Modifier"
                                >
                                  <Edit className="h-4 w-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleDelete(f)}
                                  data-testid={`btn-delete-${f.fournisseur_id}`}
                                  className="text-[#EF4444] hover:text-[#EF4444]"
                                  title="Supprimer"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Modale création / édition */}
        <Dialog open={showModal} onOpenChange={setShowModal}>
          <DialogContent className="sm:max-w-[560px]" data-testid="fournisseur-modal">
            <DialogHeader>
              <DialogTitle>{editing ? "Modifier le fournisseur" : "Nouveau fournisseur"}</DialogTitle>
              <DialogDescription>
                {editing ? `Référence : ${editing.reference}` : "Ajoutez un partenaire d'approvisionnement à votre annuaire."}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <Field label="Nom *" testId="input-nom">
                <Input
                  data-testid="input-nom"
                  value={form.nom}
                  onChange={(e) => setForm({ ...form, nom: e.target.value })}
                  placeholder="Ex : Papeterie Côte d'Ivoire"
                  maxLength={200}
                />
              </Field>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <Field label="Contact (personne)" testId="input-contact">
                  <Input
                    data-testid="input-contact"
                    value={form.contact}
                    onChange={(e) => setForm({ ...form, contact: e.target.value })}
                    placeholder="Nom du contact"
                    maxLength={120}
                  />
                </Field>
                <Field label="Téléphone" testId="input-telephone">
                  <Input
                    data-testid="input-telephone"
                    value={form.telephone}
                    onChange={(e) => setForm({ ...form, telephone: e.target.value })}
                    placeholder="+225 XX XX XX XX XX"
                    maxLength={20}
                  />
                </Field>
              </div>
              <Field label="Email" testId="input-email">
                <Input
                  data-testid="input-email"
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  placeholder="contact@fournisseur.ci"
                  maxLength={120}
                />
              </Field>
              <Field label="Adresse" testId="input-adresse">
                <Textarea
                  data-testid="input-adresse"
                  value={form.adresse}
                  onChange={(e) => setForm({ ...form, adresse: e.target.value })}
                  placeholder="Rue, ville, pays…"
                  maxLength={500}
                  rows={3}
                />
              </Field>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowModal(false)} data-testid="btn-cancel">
                Annuler
              </Button>
              <Button
                onClick={handleSave}
                disabled={saving}
                className="bg-blue-600 hover:bg-blue-600/90 text-white"
                data-testid="btn-save"
              >
                {saving ? "Enregistrement…" : editing ? "Mettre à jour" : "Créer"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}

function Field({ label, children, testId }) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={testId} className="text-sm">{label}</Label>
      {children}
    </div>
  );
}

function KPICard({ label, value, color, testId }) {
  return (
    <Card data-testid={testId}>
      <CardContent className="pt-5 pb-4">
        <p className="text-xs text-muted-foreground uppercase tracking-wide">{label}</p>
        <p className={`text-2xl font-bold mt-2 ${color}`}>{value}</p>
      </CardContent>
    </Card>
  );
}
