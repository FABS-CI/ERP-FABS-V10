/**
 * Page Documents et Impression — Module Paramètres
 * Gestion des modèles de facture, logo et filigranes
 */
import React, { useState, useEffect } from "react";
import { FileText, Settings, Upload, Trash2, Eye, Save, X } from "lucide-react";
import { toast } from "sonner";

import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Label } from "../components/ui/label";
import { Input } from "../components/ui/input";
import { Switch } from "../components/ui/switch";
import { Slider } from "../components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";

import { useAuth } from "../hooks/useAuth";

const API_BASE = process.env.REACT_APP_BACKEND_URL || "";

export default function DocumentsImpression() {
  const { user } = useAuth();
  const isAdmin = user?.role === "super_admin" || user?.role === "directeur_general";

  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [logoPreview, setLogoPreview] = useState(null);
  const [selectedTemplate, setSelectedTemplate] = useState("classique_professionnel");

  // Charger les paramètres
  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/document-settings/settings`);
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
        setSelectedTemplate(data.selected_template || "classique_professionnel");
        if (data.logo_url) {
          setLogoPreview(data.logo_url);
        }
      }
    } catch (e) {
      toast.error("Erreur chargement paramètres");
    } finally {
      setLoading(false);
    }
  };

  // Sauvegarder les paramètres
  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await fetch(`${API_BASE}/api/document-settings/settings`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings)
      });
      if (response.ok) {
        toast.success("Paramètres sauvegardés");
      } else {
        throw new Error("Erreur sauvegarde");
      }
    } catch (e) {
      toast.error("Erreur lors de la sauvegarde");
    } finally {
      setSaving(false);
    }
  };

  // Upload logo
  const handleLogoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.type.match(/image\/(png|jpeg|jpg)/)) {
      toast.error("Format non supporté. Utilisez PNG ou JPG.");
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      toast.error("Fichier trop volumineux. Maximum 2MB.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_BASE}/api/document-settings/logo/upload`, {
        method: "POST",
        body: formData
      });
      if (response.ok) {
        const data = await response.json();
        setLogoPreview(data.logo_url);
        setSettings({ ...settings, logo_url: data.logo_url });
        toast.success("Logo téléchargé avec succès");
      }
    } catch (e) {
      toast.error("Erreur lors du téléchargement");
    }
  };

  // Supprimer logo
  const handleDeleteLogo = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/document-settings/logo`, {
        method: "DELETE"
      });
      if (response.ok) {
        setLogoPreview(null);
        setSettings({ ...settings, logo_url: null });
        toast.success("Logo supprimé");
      }
    } catch (e) {
      toast.error("Erreur lors de la suppression");
    }
  };

  // Mettre à jour un champ
  const updateField = (field, value) => {
    setSettings({ ...settings, [field]: value });
  };

  // Mettre à jour les paramètres de filigrane
  const updateWatermark = (field, value) => {
    setSettings({
      ...settings,
      watermark_settings: { ...settings.watermark_settings, [field]: value }
    });
  };

  // Modèles disponibles
  const templates = [
    {
      id: "classique_professionnel",
      name: "Classique Professionnel",
      description: "Logo à gauche, coordonnées sous le logo, informations facture à droite",
      colors: ["#0A2540", "#000000"],
      style: "Administratif, sobre"
    },
    {
      id: "moderne_bleu",
      name: "Moderne Bleu",
      description: "Logo centré, bandeau bleu, informations sous forme de cartes",
      colors: ["#0A2540", "#6B7280"],
      style: "Moderne, épuré"
    },
    {
      id: "premium",
      name: "Premium",
      description: "Logo centré, nom entreprise centré, totaux encadré élégant",
      colors: ["#FF6200", "#0A2540", "#000000"],
      style: "Haut de gamme"
    },
    {
      id: "corporate_orange",
      name: "Corporate Orange",
      description: "Bandeau orange, logo à gauche, totaux fond orange",
      colors: ["#FF6200", "#6B7280", "#000000"],
      style: "Entreprise, distribution"
    },
    {
      id: "elegant_administratif",
      name: "Élégant Administratif",
      description: "Logo à gauche, coordonnées en colonnes, bloc total encadré",
      colors: ["#DC2626", "#0A2540", "#6B7280"],
      style: "Institutionnel"
    }
  ];

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#FF6200]" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-[#0A2540] dark:text-white">
            Documents et Impression
          </h1>
          <p className="text-gray-600 dark:text-white/60 mt-1">
            Personnalisation des modèles de facture, logo et filigranes
          </p>
        </div>

        <Tabs defaultValue="templates" className="space-y-6">
          <TabsList>
            <TabsTrigger value="templates">Modèles</TabsTrigger>
            <TabsTrigger value="logo">Logo</TabsTrigger>
            <TabsTrigger value="watermark">Filigranes</TabsTrigger>
            <TabsTrigger value="company">Entreprise</TabsTrigger>
          </TabsList>

          {/* Onglet Modèles */}
          <TabsContent value="templates" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <FileText className="h-5 w-5 mr-2" />
                  Sélection du modèle de facture
                </CardTitle>
                <CardDescription>
                  Choisissez parmi 5 modèles professionnels pour vos documents
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {templates.map((template) => (
                    <div
                      key={template.id}
                      className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
                        selectedTemplate === template.id
                          ? "border-[#FF6200] bg-orange-50"
                          : "border-gray-200 dark:border-white/10 hover:border-gray-300 dark:border-white/10"
                      }`}
                      onClick={() => {
                        setSelectedTemplate(template.id);
                        updateField("selected_template", template.id);
                      }}
                    >
                      <div className="flex items-center gap-2 mb-3">
                        <div className="flex gap-1">
                          {template.colors.map((color, i) => (
                            <div
                              key={i}
                              className="w-4 h-4 rounded-full"
                              style={{ backgroundColor: color }}
                            />
                          ))}
                        </div>
                        <span className="text-sm font-medium">{template.name}</span>
                      </div>
                      <p className="text-xs text-gray-600 dark:text-white/70 mb-2">{template.description}</p>
                      <p className="text-xs text-gray-500 dark:text-white/50 italic">{template.style}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Onglet Logo */}
          <TabsContent value="logo" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Settings className="h-5 w-5 mr-2" />
                  Gestion du logo
                </CardTitle>
                <CardDescription>
                  Téléchargez le logo de l'entreprise pour vos documents
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {logoPreview ? (
                  <div className="space-y-4">
                    <div className="border rounded-lg p-4">
                      <img
                        src={logoPreview}
                        alt="Logo entreprise"
                        className="max-w-xs max-h-32 mx-auto"
                      />
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="destructive"
                        onClick={handleDeleteLogo}
                        disabled={!isAdmin}
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Supprimer
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="border-2 border-dashed rounded-lg p-8 text-center">
                    <Upload className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                    <p className="text-sm text-gray-600 dark:text-white/70 mb-4">
                      Glissez-déposez ou cliquez pour télécharger
                    </p>
                    <input
                      type="file"
                      accept="image/png,image/jpeg,image/jpg"
                      onChange={handleLogoUpload}
                      disabled={!isAdmin}
                      className="hidden"
                      id="logo-upload"
                    />
                    <label htmlFor="logo-upload">
                      <Button disabled={!isAdmin} as="span">
                        Choisir un fichier
                      </Button>
                    </label>
                    <p className="text-xs text-gray-500 dark:text-white/50 mt-2">
                      PNG ou JPG, maximum 2MB
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Onglet Filigranes */}
          <TabsContent value="watermark" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <FileText className="h-5 w-5 mr-2" />
                  Paramètres des filigranes
                </CardTitle>
                <CardDescription>
                  Configurez les filigranes automatiques selon le statut des documents
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <Label htmlFor="watermark-enabled">Activer les filigranes</Label>
                  <Switch
                    id="watermark-enabled"
                    checked={settings?.watermark_settings?.enabled}
                    onCheckedChange={(checked) => updateWatermark("enabled", checked)}
                    disabled={!isAdmin}
                  />
                </div>

                <div className="space-y-4">
                  <Label>Couleur du filigrane</Label>
                  <div className="flex gap-2">
                    {["#FF0000", "#000000", "#FF6200", "#0A2540", "#DC2626"].map((color) => (
                      <button
                        key={color}
                        className={`w-8 h-8 rounded-full border-2 ${
                          settings?.watermark_settings?.color === color
                            ? "border-[#FF6200]"
                            : "border-gray-300 dark:border-white/10"
                        }`}
                        style={{ backgroundColor: color }}
                        onClick={() => updateWatermark("color", color)}
                        disabled={!isAdmin}
                      />
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Taille: {settings?.watermark_settings?.size}px</Label>
                  <Slider
                    value={[settings?.watermark_settings?.size || 48]}
                    onValueChange={([value]) => updateWatermark("size", value)}
                    min={24}
                    max={72}
                    step={4}
                    disabled={!isAdmin}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Opacité: {Math.round((settings?.watermark_settings?.opacity || 0.3) * 100)}%</Label>
                  <Slider
                    value={[settings?.watermark_settings?.opacity || 0.3]}
                    onValueChange={([value]) => updateWatermark("opacity", value)}
                    min={0.1}
                    max={1}
                    step={0.1}
                    disabled={!isAdmin}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Position</Label>
                  <Select
                    value={settings?.watermark_settings?.position || "center"}
                    onValueChange={(value) => updateWatermark("position", value)}
                    disabled={!isAdmin}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="center">Centre</SelectItem>
                      <SelectItem value="top_left">Haut gauche</SelectItem>
                      <SelectItem value="top_right">Haut droite</SelectItem>
                      <SelectItem value="bottom_left">Bas gauche</SelectItem>
                      <SelectItem value="bottom_right">Bas droite</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Rotation: {settings?.watermark_settings?.rotation}°</Label>
                  <Slider
                    value={[settings?.watermark_settings?.rotation || 45]}
                    onValueChange={([value]) => updateWatermark("rotation", value)}
                    min={0}
                    max={90}
                    step={15}
                    disabled={!isAdmin}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Onglet Entreprise */}
          <TabsContent value="company" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Informations entreprise</CardTitle>
                <CardDescription>
                  Coordonnées et informations bancaires de EDITIONS FABS-CI
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Nom de l'entreprise</Label>
                  <Input
                    value={settings?.company_info?.nom || ""}
                    onChange={(e) => updateField("company_info", { ...settings?.company_info, nom: e.target.value })}
                    disabled={!isAdmin}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Adresse</Label>
                  <Input
                    value={settings?.company_info?.adresse || ""}
                    onChange={(e) => updateField("company_info", { ...settings?.company_info, adresse: e.target.value })}
                    disabled={!isAdmin}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Téléphone</Label>
                  <Input
                    value={settings?.company_info?.telephone || ""}
                    onChange={(e) => updateField("company_info", { ...settings?.company_info, telephone: e.target.value })}
                    disabled={!isAdmin}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input
                    value={settings?.company_info?.email || ""}
                    onChange={(e) => updateField("company_info", { ...settings?.company_info, email: e.target.value })}
                    disabled={!isAdmin}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Siège social</Label>
                  <Input
                    value={settings?.company_info?.siege_social || ""}
                    onChange={(e) => updateField("company_info", { ...settings?.company_info, siege_social: e.target.value })}
                    disabled={!isAdmin}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Bouton sauvegarder */}
        {isAdmin && (
          <div className="flex justify-end">
            <Button onClick={handleSave} disabled={saving}>
              <Save className="h-4 w-4 mr-2" />
              {saving ? "Sauvegarde..." : "Sauvegarder"}
            </Button>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
