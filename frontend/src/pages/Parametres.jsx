/**
 * Page Paramètres — Sprint 13+
 * Galerie 8 modèles, gestion logo, couleurs, filigranes, paramètres système
 */
import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  Settings, Edit, Save, X, Upload, Trash2, ImageIcon, CheckCircle2,
  Eye, Palette, RefreshCw, Star, LayoutGrid, ChevronDown, ChevronUp,
  Monitor, Tablet, Smartphone, Layers, FileText, BookOpen, Building2,
  Sparkles, Zap, Crown, Award, Shield, ShieldCheck, ShieldOff, ShieldAlert
} from "lucide-react";
import { toast } from "sonner";

import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Skeleton } from "../components/ui/skeleton";
import { Label } from "../components/ui/label";

import {
  getParametres, updateParametre, getDocumentSettings, uploadLogo, deleteLogo
} from "../services/parametresApi";
import { get2FAStatus } from "../services/twoFAApi";
import TwoFASetupModal from "../components/TwoFASetupModal";
import TwoFADisableModal from "../components/TwoFADisableModal";
import { useAuth } from "../hooks/useAuth";
import axios from "axios";

// ─── Données des 8 modèles ────────────────────────────────────────────────────
const TEMPLATES = [
  {
    id: "classique_professionnel",
    name: "Classique Professionnel",
    short: "Classique",
    description: "Logo à gauche, coordonnées sous le logo, informations facture à droite.",
    ideal: "PME, administrations, institutions",
    style: "Administratif · Sobre · Intemporel",
    icon: <Building2 size={20} />,
    badge: null,
    gradient: "linear-gradient(135deg, #0A2540 0%, #1a3a60 100%)",
    accent: "#0A2540",
    preview: {
      headerBg: "#0A2540", headerText: "#fff",
      tableBorder: "#0A2540", totalBg: "#0A2540",
      bodyBg: "#fff", bodyText: "#1F2937"
    }
  },
  {
    id: "moderne_bleu",
    name: "Moderne Bleu",
    short: "Moderne",
    description: "Logo centré, bandeau supérieur coloré, informations sous forme de cartes.",
    ideal: "Entreprises de services, sociétés modernes",
    style: "Moderne · Épuré · Dynamique",
    icon: <Zap size={20} />,
    badge: null,
    gradient: "linear-gradient(135deg, #2563EB 0%, #1E40AF 100%)",
    accent: "#2563EB",
    preview: {
      headerBg: "#2563EB", headerText: "#fff",
      tableBorder: "#2563EB", totalBg: "#2563EB",
      bodyBg: "#F8FAFF", bodyText: "#1E3A8A"
    }
  },
  {
    id: "premium",
    name: "Premium Executive",
    short: "Premium",
    description: "Logo centré, nom de l'entreprise mis en valeur, bloc des totaux élégamment encadré.",
    ideal: "Grandes entreprises, groupes",
    style: "Haut de gamme · Professionnel · Corporate",
    icon: <Award size={20} />,
    badge: null,
    gradient: "linear-gradient(135deg, #FF6200 0%, #c44d00 100%)",
    accent: "#FF6200",
    preview: {
      headerBg: "#FF6200", headerText: "#fff",
      tableBorder: "#FF6200", totalBg: "#FF6200",
      bodyBg: "#FFFAF7", bodyText: "#7C2D12"
    }
  },
  {
    id: "corporate_orange",
    name: "Corporate Orange",
    short: "Corporate",
    description: "Bandeau coloré, logo à gauche, totaux dans un encadré visuellement marquant.",
    ideal: "Distribution, commerce, grossistes",
    style: "Corporate · Commercial · Impact",
    icon: <Layers size={20} />,
    badge: null,
    gradient: "linear-gradient(135deg, #EA580C 0%, #9A3412 100%)",
    accent: "#EA580C",
    preview: {
      headerBg: "#EA580C", headerText: "#fff",
      tableBorder: "#EA580C", totalBg: "#EA580C",
      bodyBg: "#FFF7ED", bodyText: "#431407"
    }
  },
  {
    id: "elegant_administratif",
    name: "Élégant Administratif",
    short: "Élégant",
    description: "Coordonnées organisées en colonnes, présentation institutionnelle et structurée.",
    ideal: "Organismes publics, établissements institutionnels",
    style: "Administratif premium · Institutionnel",
    icon: <FileText size={20} />,
    badge: null,
    gradient: "linear-gradient(135deg, #DC2626 0%, #991B1B 100%)",
    accent: "#DC2626",
    preview: {
      headerBg: "#DC2626", headerText: "#fff",
      tableBorder: "#DC2626", totalBg: "#DC2626",
      bodyBg: "#FFF5F5", bodyText: "#7F1D1D"
    }
  },
  {
    id: "minimaliste_moderne",
    name: "Minimaliste Moderne",
    short: "Minimaliste",
    description: "Mise en page aérée, très peu de bordures, accent sur la lisibilité.",
    ideal: "Startups, cabinets, entreprises numériques",
    style: "Minimaliste · Contemporain · Aéré",
    icon: <LayoutGrid size={20} />,
    badge: null,
    gradient: "linear-gradient(135deg, #374151 0%, #111827 100%)",
    accent: "#374151",
    preview: {
      headerBg: "#111827", headerText: "#fff",
      tableBorder: "#E5E7EB", totalBg: "#F9FAFB",
      bodyBg: "#fff", bodyText: "#374151"
    }
  },
  {
    id: "premium_luxe",
    name: "Premium Luxe",
    short: "Luxe",
    description: "En-tête sophistiqué, typographie élégante, finitions haut de gamme.",
    ideal: "Marques premium, entreprises prestigieuses",
    style: "Luxe · Prestige · Élégance",
    icon: <Crown size={20} />,
    badge: null,
    gradient: "linear-gradient(135deg, #1A1A2E 0%, #16213E 100%)",
    accent: "#B8860B",
    preview: {
      headerBg: "#1A1A2E", headerText: "#D4AF37",
      tableBorder: "#B8860B", totalBg: "#1A1A2E",
      bodyBg: "#FFFFF8", bodyText: "#1A1A2E"
    }
  },
  {
    id: "education_edition",
    name: "Éducation & Édition",
    short: "Éducation",
    description: "Spécialement conçu pour maisons d'édition, librairies, écoles et universités.",
    ideal: "Maisons d'édition · Librairies · Écoles · Universités",
    style: "Institutionnel · Éducatif · Édition",
    icon: <BookOpen size={20} />,
    badge: "⭐ Recommandé",
    gradient: "linear-gradient(135deg, #1E3A5F 0%, #0f2540 100%)",
    accent: "#1E3A5F",
    preview: {
      headerBg: "#1E3A5F", headerText: "#fff",
      tableBorder: "#2ECC71", totalBg: "#1E3A5F",
      bodyBg: "#F0F4F8", bodyText: "#1E3A5F"
    }
  }
];

const DOC_TYPES = [
  { key: "facture", label: "Factures" },
  { key: "devis", label: "Devis" },
  { key: "bon_commande", label: "Bons de commande" },
  { key: "bon_livraison", label: "Bons de livraison" },
  { key: "recu_paiement", label: "Reçus de paiement" },
  { key: "avoir", label: "Avoirs" },
  { key: "etat_compte", label: "États de compte" },
  { key: "document_admin", label: "Documents administratifs" }
];

// ─── Miniature SVG d'aperçu du modèle ────────────────────────────────────────
function TemplateMiniature({ tpl, logoUrl, customColors, size = "md" }) {
  const w = size === "lg" ? 480 : size === "sm" ? 120 : 200;
  const h = Math.round(w * 1.414);
  const p = tpl.preview;
  // Couleurs : utiliser custom si défini, sinon couleur du template
  const hBg = customColors?.primary || p.headerBg;
  const hText = p.headerText;
  const tBorder = customColors?.secondary || p.tableBorder;
  const totBg = customColors?.primary || p.totalBg;
  const bBg = p.bodyBg;

  const scale = w / 200;
  const rows = [
    ["Livre Mathématiques 6e", "12", "5 800", "69 600"],
    ["Manuel Français CM2", "8", "4 200", "33 600"],
    ["Atlas Géographie", "5", "6 500", "32 500"],
    ["Dict. Français-Anglais", "20", "3 800", "76 000"],
  ];

  return (
    <svg viewBox={`0 0 200 ${Math.round(200 * 1.414)}`} width={w} height={h} xmlns="http://www.w3.org/2000/svg"
      style={{ borderRadius: 6, boxShadow: "0 2px 12px rgba(0,0,0,0.15)", display: "block" }}>
      {/* Fond */}
      <rect width="200" height={Math.round(200 * 1.414)} fill={bBg} />

      {/* EN-TÊTE */}
      {tpl.id === "minimaliste_moderne" ? (
        <>
          <rect x="0" y="0" width="200" height="36" fill={hBg} />
          <text x="10" y="14" fontSize="5" fill={hText} fontWeight="700" fontFamily="sans-serif">ÉDITIONS FABS-CI</text>
          <text x="10" y="22" fontSize="3.5" fill="rgba(255,255,255,0.7)" fontFamily="sans-serif">BP 693 · Bingerville · +225 07 59 73 71 23</text>
          <line x1="0" y1="36" x2="200" y2="36" stroke={tBorder} strokeWidth="0.5" />
        </>
      ) : tpl.id === "premium_luxe" ? (
        <>
          <rect x="0" y="0" width="200" height="42" fill={hBg} />
          <rect x="0" y="40" width="200" height="1.5" fill="#B8860B" />
          <text x="100" y="16" fontSize="5" fill="#D4AF37" fontWeight="800" textAnchor="middle" fontFamily="serif">ÉDITIONS FABS-CI</text>
          <text x="100" y="24" fontSize="3" fill="rgba(212,175,55,0.8)" textAnchor="middle" fontFamily="serif">— Prestige & Excellence —</text>
          <text x="100" y="31" fontSize="3" fill="rgba(255,255,255,0.6)" textAnchor="middle" fontFamily="sans-serif">BP 693 · Bingerville</text>
        </>
      ) : tpl.id === "moderne_bleu" ? (
        <>
          <rect x="0" y="0" width="200" height="44" fill={hBg} />
          {logoUrl && <image href={logoUrl} x="80" y="4" width="40" height="16" preserveAspectRatio="xMidYMid meet" />}
          <text x="100" y="28" fontSize="5.5" fill="#fff" fontWeight="800" textAnchor="middle" fontFamily="sans-serif">ÉDITIONS FABS-CI</text>
          <text x="100" y="36" fontSize="3" fill="rgba(255,255,255,0.75)" textAnchor="middle" fontFamily="sans-serif">BP 693 · Bingerville</text>
          <rect x="0" y="42" width="200" height="2" fill="rgba(255,255,255,0.3)" />
        </>
      ) : (
        <>
          <rect x="0" y="0" width="200" height="38" fill={hBg} />
          {logoUrl
            ? <image href={logoUrl} x="6" y="6" width="28" height="16" preserveAspectRatio="xMinYMid meet" />
            : <rect x="6" y="8" width="22" height="12" fill="rgba(255,255,255,0.25)" rx="2" />
          }
          <text x="36" y="15" fontSize="5" fill={hText} fontWeight="700" fontFamily="sans-serif">ÉDITIONS FABS-CI</text>
          <text x="36" y="22" fontSize="2.8" fill="rgba(255,255,255,0.75)" fontFamily="sans-serif">BP 693 · Bingerville</text>
          <text x="36" y="28" fontSize="2.8" fill="rgba(255,255,255,0.75)" fontFamily="sans-serif">+225 07 59 73 71 23</text>
        </>
      )}

      {/* TITRE DOCUMENT */}
      <text x="100" y="52" fontSize="6" fill={totBg === "#F9FAFB" ? "#111827" : totBg} fontWeight="800" textAnchor="middle" fontFamily="sans-serif">FACTURE</text>
      <text x="100" y="59" fontSize="3" fill="#9CA3AF" textAnchor="middle" fontFamily="sans-serif">N° FAC-2026-0142 · 15/06/2026</text>

      {/* INFOS CLIENT */}
      <rect x="10" y="63" width="84" height="28" fill="rgba(0,0,0,0.03)" rx="3" />
      <text x="15" y="71" fontSize="3" fill="#6B7280" fontFamily="sans-serif">Facturé à :</text>
      <text x="15" y="77" fontSize="3.5" fill="#111827" fontWeight="700" fontFamily="sans-serif">LYCÉE TECHNIQUE ABIDJAN</text>
      <text x="15" y="83" fontSize="3" fill="#6B7280" fontFamily="sans-serif">Abidjan, Côte d'Ivoire</text>
      <text x="15" y="88" fontSize="3" fill="#6B7280" fontFamily="sans-serif">REG: CI-ABJ-2019-B-12345</text>

      <rect x="106" y="63" width="84" height="28" fill="rgba(0,0,0,0.03)" rx="3" />
      <text x="111" y="71" fontSize="3" fill="#6B7280" fontFamily="sans-serif">Référence :</text>
      <text x="111" y="77" fontSize="3" fill="#111827" fontFamily="sans-serif">FAC-2026-0142</text>
      <text x="111" y="83" fontSize="3" fill="#6B7280" fontFamily="sans-serif">Échéance : 30/07/2026</text>
      <text x="111" y="88" fontSize="3" fill="#6B7280" fontFamily="sans-serif">Statut : En attente</text>

      {/* TABLEAU */}
      <rect x="10" y="96" width="180" height="6" fill={tBorder} rx="1" />
      <text x="12" y="100.5" fontSize="3" fill="#fff" fontWeight="700" fontFamily="sans-serif">Désignation</text>
      <text x="118" y="100.5" fontSize="3" fill="#fff" fontWeight="700" fontFamily="sans-serif">Qté</text>
      <text x="133" y="100.5" fontSize="3" fill="#fff" fontWeight="700" fontFamily="sans-serif">P.U.</text>
      <text x="158" y="100.5" fontSize="3" fill="#fff" fontWeight="700" fontFamily="sans-serif">Total</text>

      {rows.map((row, i) => {
        const y = 106 + i * 10;
        const bg = i % 2 === 0 ? "rgba(0,0,0,0.02)" : "#fff";
        return (
          <g key={i}>
            <rect x="10" y={y - 2} width="180" height="10" fill={bg} />
            <text x="12" y={y + 4.5} fontSize="3" fill="#374151" fontFamily="sans-serif">{row[0]}</text>
            <text x="120" y={y + 4.5} fontSize="3" fill="#374151" fontFamily="sans-serif">{row[1]}</text>
            <text x="133" y={y + 4.5} fontSize="3" fill="#374151" fontFamily="sans-serif">{row[2]}</text>
            <text x="158" y={y + 4.5} fontSize="3" fill="#374151" fontFamily="sans-serif">{row[3]}</text>
          </g>
        );
      })}

      {/* TOTAUX */}
      <rect x="110" y="149" width="80" height="32" fill={totBg} rx="3" />
      <text x="115" y="157" fontSize="3" fill="rgba(255,255,255,0.75)" fontFamily="sans-serif">Sous-total HT</text>
      <text x="185" y="157" fontSize="3" fill="#fff" textAnchor="end" fontFamily="sans-serif">211 700</text>
      <text x="115" y="164" fontSize="3" fill="rgba(255,255,255,0.75)" fontFamily="sans-serif">TVA (18%)</text>
      <text x="185" y="164" fontSize="3" fill="#fff" textAnchor="end" fontFamily="sans-serif">38 106</text>
      <line x1="115" y1="166" x2="185" y2="166" stroke="rgba(255,255,255,0.3)" strokeWidth="0.5" />
      <text x="115" y="173" fontSize="3.5" fill="#fff" fontWeight="800" fontFamily="sans-serif">TOTAL TTC</text>
      <text x="185" y="173" fontSize="4" fill="#fff" fontWeight="800" textAnchor="end" fontFamily="sans-serif">249 806</text>

      {/* PIED DE PAGE */}
      <rect x="0" y="265" width="200" height="18" fill={tBorder} opacity="0.15" />
      <line x1="0" y1="265" x2="200" y2="265" stroke={tBorder} strokeWidth="0.5" />
      <text x="100" y="272" fontSize="2.5" fill="#6B7280" textAnchor="middle" fontFamily="sans-serif">ÉDITIONS FABS-CI · BP 693 Bingerville · +225 07 59 73 71 23</text>
      <text x="100" y="278" fontSize="2.5" fill="#6B7280" textAnchor="middle" fontFamily="sans-serif">CORIS BANK: C116 01011 007630824101 34 · SGBCI: CI008 01123012343259990 95</text>
    </svg>
  );
}

// ─── Carte modèle ─────────────────────────────────────────────────────────────
function TemplateCard({ tpl, isActive, onSelect, onPreview, logoUrl, customColors, perTypeMap }) {
  const usedFor = Object.entries(perTypeMap || {})
    .filter(([, v]) => v === tpl.id)
    .map(([k]) => DOC_TYPES.find(d => d.key === k)?.label)
    .filter(Boolean);

  return (
    <div
      style={{
        position: "relative",
        border: isActive ? `2.5px solid ${tpl.accent}` : "2px solid #E5E7EB",
        borderRadius: 14,
        overflow: "hidden",
        cursor: "pointer",
        background: "#fff",
        boxShadow: isActive ? `0 4px 20px ${tpl.accent}30` : "0 2px 8px rgba(0,0,0,0.06)",
        transition: "all 0.22s ease",
        display: "flex",
        flexDirection: "column"
      }}
      onClick={() => onPreview(tpl)}
    >
      {/* Badges */}
      {tpl.badge && (
        <div style={{
          position: "absolute", top: 8, right: 8, zIndex: 3,
          background: "#1E3A5F", color: "#fff", fontSize: 10,
          padding: "2px 8px", borderRadius: 20, fontWeight: 700
        }}>{tpl.badge}</div>
      )}
      {isActive && (
        <div style={{
          position: "absolute", top: 8, left: 8, zIndex: 3,
          background: tpl.accent, color: "#fff", fontSize: 10,
          padding: "2px 10px", borderRadius: 20, fontWeight: 700,
          display: "flex", alignItems: "center", gap: 4
        }}>
          <CheckCircle2 size={11} /> Modèle actif
        </div>
      )}
      {usedFor.length > 0 && !isActive && (
        <div style={{
          position: "absolute", top: 8, left: 8, zIndex: 3,
          background: "#6B7280", color: "#fff", fontSize: 9,
          padding: "2px 8px", borderRadius: 20, fontWeight: 600
        }}>
          {usedFor.length} type{usedFor.length > 1 ? "s" : ""}
        </div>
      )}

      {/* Miniature */}
      <div style={{
        background: "#F8FAFC",
        display: "flex", alignItems: "center", justifyContent: "center",
        padding: "16px 0 12px",
        minHeight: 160,
        overflow: "hidden"
      }}>
        <TemplateMiniature tpl={tpl} logoUrl={logoUrl} customColors={customColors} size="sm" />
      </div>

      {/* Bande couleur */}
      <div style={{ height: 4, background: tpl.gradient }} />

      {/* Infos */}
      <div style={{ padding: "12px 14px 14px", flexGrow: 1, display: "flex", flexDirection: "column", gap: 4 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ color: tpl.accent }}>{tpl.icon}</span>
          <span style={{ fontWeight: 700, fontSize: 14, color: "#111827" }}>{tpl.name}</span>
        </div>
        <p style={{ fontSize: 12, color: "#6B7280", lineHeight: 1.4, margin: 0 }}>{tpl.description}</p>
        <p style={{ fontSize: 11, color: tpl.accent, fontStyle: "italic", margin: 0 }}>{tpl.style}</p>
      </div>

      {/* Boutons */}
      <div style={{
        display: "flex", gap: 6, padding: "0 12px 12px"
      }}>
        <button
          onClick={(e) => { e.stopPropagation(); onPreview(tpl); }}
          style={{
            flex: 1, padding: "6px 0", border: `1.5px solid ${tpl.accent}`,
            borderRadius: 8, background: "transparent", color: tpl.accent,
            fontSize: 12, fontWeight: 600, cursor: "pointer",
            display: "flex", alignItems: "center", justifyContent: "center", gap: 4
          }}
        >
          <Eye size={13} /> Aperçu
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); onSelect(tpl.id); }}
          style={{
            flex: 1, padding: "6px 0",
            background: isActive ? tpl.accent : tpl.gradient,
            border: "none", borderRadius: 8, color: "#fff",
            fontSize: 12, fontWeight: 700, cursor: "pointer",
            display: "flex", alignItems: "center", justifyContent: "center", gap: 4,
            opacity: isActive ? 0.8 : 1
          }}
        >
          {isActive ? <CheckCircle2 size={13} /> : <Sparkles size={13} />}
          {isActive ? "Actif" : "Utiliser"}
        </button>
      </div>
    </div>
  );
}

// ─── Modal aperçu grand format ────────────────────────────────────────────────
function PreviewModal({ tpl, onClose, onSelect, isActive, logoUrl, customColors }) {
  if (!tpl) return null;
  return (
    <div
      style={{
        position: "fixed", inset: 0, zIndex: 9999,
        background: "rgba(0,0,0,0.7)",
        display: "flex", alignItems: "center", justifyContent: "center",
        padding: 20
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: "#fff", borderRadius: 18,
          maxWidth: 960, width: "100%",
          maxHeight: "95vh", overflow: "auto",
          boxShadow: "0 24px 80px rgba(0,0,0,0.4)"
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header modal */}
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "20px 24px 16px",
          borderBottom: "1px solid #F3F4F6"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ color: tpl.accent, width: 36, height: 36, background: `${tpl.accent}15`, borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center" }}>
              {tpl.icon}
            </span>
            <div>
              <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, color: "#111827" }}>{tpl.name}</h2>
              <p style={{ margin: 0, fontSize: 13, color: "#6B7280" }}>{tpl.style}</p>
            </div>
          </div>
          <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", padding: 8, borderRadius: 8, color: "#6B7280" }}>
            <X size={22} />
          </button>
        </div>

        {/* Contenu */}
        <div style={{ display: "flex", gap: 0, flexWrap: "wrap" }}>
          {/* Aperçu */}
          <div style={{
            flex: "1 1 380px", padding: "24px",
            display: "flex", alignItems: "flex-start", justifyContent: "center",
            background: "#F8FAFC"
          }}>
            <TemplateMiniature tpl={tpl} logoUrl={logoUrl} customColors={customColors} size="lg" />
          </div>

          {/* Infos */}
          <div style={{ flex: "1 1 280px", padding: "24px 28px", display: "flex", flexDirection: "column", gap: 16 }}>
            <div>
              <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 700, color: "#111827" }}>Description</h3>
              <p style={{ margin: 0, fontSize: 14, color: "#6B7280", lineHeight: 1.6 }}>{tpl.description}</p>
            </div>

            <div>
              <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 700, color: "#111827" }}>Idéal pour</h3>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {tpl.ideal.split("·").map((item, i) => (
                  <span key={i} style={{
                    background: `${tpl.accent}15`, color: tpl.accent,
                    padding: "3px 10px", borderRadius: 20, fontSize: 12, fontWeight: 600
                  }}>{item.trim()}</span>
                ))}
              </div>
            </div>

            <div>
              <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 700, color: "#111827" }}>Couleurs du modèle</h3>
              <div style={{ display: "flex", gap: 8 }}>
                {[tpl.preview.headerBg, tpl.preview.tableBorder].map((c, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <div style={{ width: 24, height: 24, borderRadius: 6, background: c, border: "2px solid #E5E7EB" }} />
                    <span style={{ fontSize: 12, color: "#6B7280" }}>{c}</span>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: "auto", paddingTop: 16 }}>
              {tpl.badge && (
                <div style={{
                  padding: "10px 14px", borderRadius: 10,
                  background: "linear-gradient(135deg, #1E3A5F, #0f2540)",
                  color: "#fff", fontSize: 13, fontWeight: 700
                }}>
                  {tpl.badge} — Recommandé pour votre secteur d'activité
                </div>
              )}
              <button
                onClick={() => { onSelect(tpl.id); onClose(); }}
                style={{
                  padding: "12px 20px",
                  background: isActive ? "#6B7280" : tpl.gradient,
                  border: "none", borderRadius: 10, color: "#fff",
                  fontSize: 14, fontWeight: 700, cursor: "pointer",
                  display: "flex", alignItems: "center", justifyContent: "center", gap: 8
                }}
              >
                {isActive ? <><CheckCircle2 size={16} /> Modèle actuellement actif</> : <><Sparkles size={16} /> Utiliser ce modèle</>}
              </button>
              <button
                onClick={onClose}
                style={{
                  padding: "10px 20px", border: "1.5px solid #E5E7EB",
                  borderRadius: 10, background: "#fff", color: "#6B7280",
                  fontSize: 14, cursor: "pointer"
                }}
              >
                Fermer
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Section Galerie principale ───────────────────────────────────────────────
function TemplateGallery({ settings, logoUrl, isSuperAdmin, onRefresh }) {
  const [activeTemplate, setActiveTemplate] = useState(settings?.selected_template || "classique_professionnel");
  const [perTypeMap, setPerTypeMap] = useState(settings?.template_per_type || {});
  const [customColors, setCustomColors] = useState(
    settings?.custom_colors || { primary: "#0A2540", secondary: "#FF6200", accent: "#2563EB" }
  );
  const [previewTpl, setPreviewTpl] = useState(null);
  const [saving, setSaving] = useState(false);
  const [showColorPanel, setShowColorPanel] = useState(false);
  const [showPerType, setShowPerType] = useState(false);
  const [colorDraft, setColorDraft] = useState(customColors);

  const handleSelectGlobal = async (templateId) => {
    if (!isSuperAdmin) { toast.error("Accès refusé"); return; }
    setSaving(true);
    try {
      await axios.post(`/api/document-settings/template/select?template_id=${templateId}`);
      setActiveTemplate(templateId);
      toast.success(`Modèle « ${TEMPLATES.find(t => t.id === templateId)?.name} » activé`);
      onRefresh();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erreur");
    } finally { setSaving(false); }
  };

  const handleSelectPerType = async (templateId, docType) => {
    if (!isSuperAdmin) { toast.error("Accès refusé"); return; }
    try {
      await axios.post(`/api/document-settings/template/select?template_id=${templateId}&document_type=${docType}`);
      setPerTypeMap(prev => ({ ...prev, [docType]: templateId }));
      toast.success(`Modèle « ${TEMPLATES.find(t => t.id === templateId)?.name} » pour ${DOC_TYPES.find(d => d.key === docType)?.label}`);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erreur");
    }
  };

  const handleSaveColors = async () => {
    if (!isSuperAdmin) { toast.error("Accès refusé"); return; }
    try {
      const { primary, secondary, accent } = colorDraft;
      await axios.post(`/api/document-settings/colors/save?primary=${encodeURIComponent(primary)}&secondary=${encodeURIComponent(secondary)}&accent=${encodeURIComponent(accent)}`);
      setCustomColors(colorDraft);
      toast.success("Couleurs personnalisées sauvegardées");
    } catch (e) {
      toast.error("Erreur sauvegarde couleurs");
    }
  };

  const handleResetColors = () => {
    const activeTpl = TEMPLATES.find(t => t.id === activeTemplate);
    if (activeTpl) {
      const c = { primary: activeTpl.preview.headerBg, secondary: activeTpl.preview.tableBorder, accent: activeTpl.accent };
      setColorDraft(c);
    }
  };

  const activeTpl = TEMPLATES.find(t => t.id === activeTemplate);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Modèle actif */}
      <div style={{
        background: `linear-gradient(135deg, ${activeTpl?.accent || "#0A2540"}15 0%, transparent 100%)`,
        border: `1.5px solid ${activeTpl?.accent || "#0A2540"}30`,
        borderRadius: 14, padding: "16px 20px",
        display: "flex", alignItems: "center", gap: 14
      }}>
        <div style={{
          width: 42, height: 42, borderRadius: 10,
          background: activeTpl?.gradient || "#0A2540",
          display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", flexShrink: 0
        }}>
          {activeTpl?.icon}
        </div>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontWeight: 700, fontSize: 15, color: "#111827" }}>Modèle actif :</span>
            <span style={{
              background: activeTpl?.accent, color: "#fff",
              padding: "2px 10px", borderRadius: 20, fontSize: 12, fontWeight: 700
            }}>{activeTpl?.name}</span>
          </div>
          <p style={{ margin: "2px 0 0", fontSize: 12, color: "#6B7280" }}>
            {activeTpl?.style} — Appliqué à tous les types de documents par défaut
          </p>
        </div>
      </div>

      {/* Galerie */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
        gap: 16
      }}>
        {TEMPLATES.map(tpl => (
          <TemplateCard
            key={tpl.id}
            tpl={tpl}
            isActive={activeTemplate === tpl.id}
            onSelect={handleSelectGlobal}
            onPreview={setPreviewTpl}
            logoUrl={logoUrl}
            customColors={customColors}
            perTypeMap={perTypeMap}
          />
        ))}
      </div>

      {/* Couleurs personnalisées */}
      {isSuperAdmin && (
        <div style={{ border: "1.5px solid #E5E7EB", borderRadius: 14, overflow: "hidden" }}>
          <button
            onClick={() => setShowColorPanel(v => !v)}
            style={{
              width: "100%", padding: "14px 18px", background: "#F9FAFB",
              border: "none", borderBottom: showColorPanel ? "1px solid #E5E7EB" : "none",
              cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "space-between"
            }}
          >
            <span style={{ display: "flex", alignItems: "center", gap: 10, fontWeight: 700, fontSize: 14, color: "#111827" }}>
              <Palette size={18} color="#6B7280" /> Couleurs personnalisées
            </span>
            {showColorPanel ? <ChevronUp size={16} color="#9CA3AF" /> : <ChevronDown size={16} color="#9CA3AF" />}
          </button>
          {showColorPanel && (
            <div style={{ padding: "18px 20px" }}>
              <p style={{ margin: "0 0 16px", fontSize: 13, color: "#6B7280" }}>
                Ces couleurs remplacent les couleurs par défaut du modèle sélectionné sur tous les documents.
              </p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 18, marginBottom: 16 }}>
                {[
                  { key: "primary", label: "Couleur principale (en-tête, totaux)" },
                  { key: "secondary", label: "Couleur secondaire (tableaux, bordures)" },
                  { key: "accent", label: "Couleur d'accentuation (titres, badges)" }
                ].map(({ key, label }) => (
                  <div key={key} style={{ display: "flex", flexDirection: "column", gap: 6, flex: "1 1 160px" }}>
                    <label style={{ fontSize: 12, fontWeight: 600, color: "#374151" }}>{label}</label>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <input
                        type="color"
                        value={colorDraft[key]}
                        onChange={e => setColorDraft(prev => ({ ...prev, [key]: e.target.value }))}
                        style={{ width: 44, height: 44, border: "1.5px solid #E5E7EB", borderRadius: 8, padding: 2, cursor: "pointer" }}
                      />
                      <input
                        type="text"
                        value={colorDraft[key]}
                        onChange={e => setColorDraft(prev => ({ ...prev, [key]: e.target.value }))}
                        style={{
                          flex: 1, padding: "8px 10px", border: "1.5px solid #E5E7EB",
                          borderRadius: 8, fontSize: 13, fontFamily: "monospace"
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <button
                  onClick={handleSaveColors}
                  style={{
                    padding: "9px 18px", background: "#0A2540", color: "#fff",
                    border: "none", borderRadius: 8, fontSize: 13, fontWeight: 700, cursor: "pointer",
                    display: "flex", alignItems: "center", gap: 6
                  }}
                >
                  <Save size={14} /> Sauvegarder les couleurs
                </button>
                <button
                  onClick={handleResetColors}
                  style={{
                    padding: "9px 18px", background: "#F3F4F6", color: "#374151",
                    border: "1.5px solid #E5E7EB", borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: "pointer",
                    display: "flex", alignItems: "center", gap: 6
                  }}
                >
                  <RefreshCw size={14} /> Réinitialiser depuis le modèle
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Modèle par type */}
      <div style={{ border: "1.5px solid #E5E7EB", borderRadius: 14, overflow: "hidden" }}>
        <button
          onClick={() => setShowPerType(v => !v)}
          style={{
            width: "100%", padding: "14px 18px", background: "#F9FAFB",
            border: "none", borderBottom: showPerType ? "1px solid #E5E7EB" : "none",
            cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "space-between"
          }}
        >
          <span style={{ display: "flex", alignItems: "center", gap: 10, fontWeight: 700, fontSize: 14, color: "#111827" }}>
            <Layers size={18} color="#6B7280" /> Modèle par type de document
          </span>
          {showPerType ? <ChevronUp size={16} color="#9CA3AF" /> : <ChevronDown size={16} color="#9CA3AF" />}
        </button>
        {showPerType && (
          <div style={{ padding: "18px 20px" }}>
            <p style={{ margin: "0 0 16px", fontSize: 13, color: "#6B7280" }}>
              Définissez un modèle différent pour chaque type de document. Laissez sur « Défaut » pour utiliser le modèle global.
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {DOC_TYPES.map(({ key, label }) => {
                const current = perTypeMap[key] || "";
                return (
                  <div key={key} style={{
                    display: "flex", alignItems: "center", justifyContent: "space-between",
                    gap: 12, padding: "10px 14px", background: "#F9FAFB",
                    borderRadius: 10, border: "1px solid #E5E7EB",
                    flexWrap: "wrap"
                  }}>
                    <span style={{ fontSize: 13, fontWeight: 600, color: "#374151", minWidth: 160 }}>{label}</span>
                    <select
                      value={current}
                      onChange={e => isSuperAdmin && handleSelectPerType(e.target.value || activeTemplate, key)}
                      disabled={!isSuperAdmin}
                      style={{
                        padding: "7px 12px", border: "1.5px solid #E5E7EB",
                        borderRadius: 8, fontSize: 13, background: "#fff", cursor: isSuperAdmin ? "pointer" : "default",
                        minWidth: 200, color: "#374151"
                      }}
                    >
                      <option value="">— Défaut ({activeTpl?.name}) —</option>
                      {TEMPLATES.map(t => (
                        <option key={t.id} value={t.id}>{t.name}</option>
                      ))}
                    </select>
                    {current && (
                      <span style={{
                        background: `${TEMPLATES.find(t => t.id === current)?.accent}20`,
                        color: TEMPLATES.find(t => t.id === current)?.accent,
                        padding: "3px 10px", borderRadius: 20, fontSize: 11, fontWeight: 700
                      }}>
                        {TEMPLATES.find(t => t.id === current)?.short}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Modal aperçu */}
      {previewTpl && (
        <PreviewModal
          tpl={previewTpl}
          onClose={() => setPreviewTpl(null)}
          onSelect={handleSelectGlobal}
          isActive={activeTemplate === previewTpl.id}
          logoUrl={logoUrl}
          customColors={customColors}
        />
      )}
    </div>
  );
}

// ─── Page principale ──────────────────────────────────────────────────────────
export default function Parametres() {
  const { user } = useAuth();
  const isSuperAdmin = user?.role === "super_admin";

  const [params, setParams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState({});
  const [saving, setSaving] = useState({});

  // Logo & settings
  const [logoUrl, setLogoUrl] = useState(null);
  const [logoLoading, setLogoLoading] = useState(true);
  const [logoUploading, setLogoUploading] = useState(false);
  const [logoDeleting, setLogoDeleting] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [docSettings, setDocSettings] = useState(null);
  const fileInputRef = useRef(null);

  // 2FA
  const [twoFAStatus, setTwoFAStatus] = useState(null); // { enabled, required, role }
  const [twoFALoading, setTwoFALoading] = useState(true);
  const [showSetupModal, setShowSetupModal] = useState(false);
  const [showDisableModal, setShowDisableModal] = useState(false);

  const fetchTwoFAStatus = async () => {
    setTwoFALoading(true);
    try { setTwoFAStatus(await get2FAStatus()); }
    catch { /* silencieux si non connecté */ }
    finally { setTwoFALoading(false); }
  };

  const fetchParams = async () => {
    setLoading(true);
    try { setParams(await getParametres()); }
    catch { toast.error("Erreur chargement paramètres"); }
    finally { setLoading(false); }
  };

  const fetchSettings = async () => {
    setLogoLoading(true);
    try {
      const s = await getDocumentSettings();
      setDocSettings(s);
      setLogoUrl(s.logo_url || null);
    } catch { /* silencieux */ }
    finally { setLogoLoading(false); }
  };

  useEffect(() => { fetchParams(); fetchSettings(); fetchTwoFAStatus(); }, []);

  const handleFileChange = async (file) => {
    if (!file) return;
    const allowed = ["image/png", "image/jpeg", "image/jpg", "image/svg+xml", "image/webp"];
    if (!allowed.includes(file.type)) { toast.error("Format non supporté. PNG, JPG, SVG ou WebP."); return; }
    if (file.size > 5 * 1024 * 1024) { toast.error("Fichier trop volumineux (max 5 Mo)."); return; }
    setLogoUploading(true);
    try {
      const result = await uploadLogo(file);
      setLogoUrl(result.logo_url);
      toast.success("Logo uploadé avec succès");
    } catch (e) { toast.error(e.response?.data?.detail || "Erreur upload logo"); }
    finally { setLogoUploading(false); if (fileInputRef.current) fileInputRef.current.value = ""; }
  };

  const handleDeleteLogo = async () => {
    setLogoDeleting(true);
    try {
      await deleteLogo();
      setLogoUrl(null);
      toast.success("Logo supprimé");
    } catch (e) { toast.error(e.response?.data?.detail || "Erreur suppression logo"); }
    finally { setLogoDeleting(false); }
  };

  const handleDrop = (e) => {
    e.preventDefault(); e.stopPropagation(); setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFileChange(file);
  };

  const handleSave = async (cle) => {
    const valeur = editing[cle];
    if (!valeur && valeur !== "0") { toast.error("Valeur vide"); return; }
    setSaving({ ...saving, [cle]: true });
    try {
      await updateParametre(cle, valeur);
      toast.success(`Paramètre "${cle}" mis à jour`);
      const e = { ...editing }; delete e[cle]; setEditing(e);
      fetchParams();
    } catch (e) { toast.error(e.response?.data?.detail || "Erreur"); }
    finally { setSaving({ ...saving, [cle]: false }); }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="parametres-page">
        <div>
          <h1 className="text-3xl font-bold text-[#0A2540] dark:text-white">Paramètres système</h1>
          <p className="text-gray-600 dark:text-white/60 mt-1">
            Configuration entreprise, modèles de documents, logo et filigranes
          </p>
        </div>

        {/* ── Galerie des modèles ──────────────────────────────────────── */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <LayoutGrid className="h-5 w-5" />
              Personnalisation des modèles de document
            </CardTitle>
            <CardDescription>
              Choisissez parmi 8 modèles professionnels applicables à toutes vos factures, devis, bons de commande et autres documents.
              {!isSuperAdmin && " Lecture seule — super_admin requis pour modifier."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {logoLoading ? (
              <div className="space-y-4">
                <Skeleton className="h-16 w-full rounded-xl" />
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {[...Array(8)].map((_, i) => <Skeleton key={i} className="h-64 rounded-xl" />)}
                </div>
              </div>
            ) : (
              <TemplateGallery
                settings={docSettings}
                logoUrl={logoUrl}
                isSuperAdmin={isSuperAdmin}
                onRefresh={fetchSettings}
              />
            )}
          </CardContent>
        </Card>

        {/* ── Gestion du logo ──────────────────────────────────────────── */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ImageIcon className="h-5 w-5" /> Gestion du logo entreprise
            </CardTitle>
            <CardDescription>
              Logo affiché sur tous les documents PDF. Le modèle adaptera automatiquement ses couleurs.
              {isSuperAdmin ? " Formats : PNG, JPG, SVG, WebP — max 5 Mo." : " Lecture seule."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {logoLoading ? (
              <Skeleton className="h-40 w-full rounded-lg" />
            ) : (
              <div className="flex flex-col gap-4">
                {logoUrl ? (
                  <div className="flex items-center gap-4 p-4 border rounded-xl bg-gray-50 dark:bg-white dark:bg-[#0b1e30]/5">
                    <img src={logoUrl} alt="Logo entreprise" className="h-20 max-w-[200px] object-contain rounded" />
                    <div className="flex flex-col gap-2">
                      <p className="text-sm text-gray-600 dark:text-white/60">Logo actuel — utilisé dans tous les aperçus de modèles</p>
                      {isSuperAdmin && (
                        <Button size="sm" variant="destructive" onClick={handleDeleteLogo} disabled={logoDeleting} className="w-fit">
                          <Trash2 className="h-3 w-3 mr-1" />
                          {logoDeleting ? "Suppression..." : "Supprimer"}
                        </Button>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center gap-3 p-4 border rounded-xl bg-gray-50 dark:bg-white dark:bg-[#0b1e30]/5 text-gray-400 text-sm">
                    <ImageIcon className="h-8 w-8 opacity-30" />
                    <span>Aucun logo configuré — un placeholder sera utilisé dans les aperçus</span>
                  </div>
                )}

                {isSuperAdmin && (
                  <div
                    role="button" tabIndex={0}
                    aria-label="Zone de dépôt de logo"
                    onClick={() => fileInputRef.current?.click()}
                    onKeyDown={(e) => e.key === "Enter" && fileInputRef.current?.click()}
                    onDrop={handleDrop}
                    onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); setDragOver(true); }}
                    onDragLeave={(e) => { e.preventDefault(); setDragOver(false); }}
                    style={{
                      border: `2px dashed ${dragOver ? "#FF6200" : "#D1D5DB"}`,
                      borderRadius: 12, padding: "32px 24px", textAlign: "center", cursor: "pointer",
                      background: dragOver ? "rgba(255,98,0,0.05)" : "transparent",
                      transition: "all 0.2s ease"
                    }}
                  >
                    <Upload style={{ width: 28, height: 28, margin: "0 auto 10px", color: dragOver ? "#FF6200" : "#9CA3AF" }} />
                    <p style={{ fontSize: 14, color: "#6B7280", marginBottom: 4 }}>
                      {logoUploading ? "Upload en cours..." : "Glissez un fichier ici ou cliquez pour choisir"}
                    </p>
                    <p style={{ fontSize: 12, color: "#9CA3AF" }}>PNG, JPG, SVG, WebP — max 5 Mo</p>
                    <input
                      ref={fileInputRef} type="file"
                      accept="image/png,image/jpeg,image/jpg,image/svg+xml,image/webp"
                      style={{ display: "none" }}
                      onChange={(e) => handleFileChange(e.target.files?.[0])}
                      disabled={logoUploading}
                    />
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* ── Sécurité — Double authentification (2FA) ─────────────────── */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-[#FF6200]" />
              Sécurité — Double authentification (2FA)
            </CardTitle>
            <CardDescription>
              Protégez votre compte avec un code temporaire (TOTP) en plus du mot de passe.
              {twoFAStatus?.required && (
                <span className="ml-2 inline-flex items-center gap-1 text-amber-600 dark:text-amber-400 font-medium">
                  <ShieldAlert className="h-3.5 w-3.5" /> Obligatoire pour votre rôle
                </span>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {twoFALoading ? (
              <Skeleton className="h-20 w-full" />
            ) : !twoFAStatus ? (
              <p className="text-sm text-gray-500 dark:text-white/50">Impossible de charger le statut 2FA.</p>
            ) : (
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 border rounded-xl bg-gray-50 dark:bg-white dark:bg-[#0b1e30]/5">
                <div className="flex items-center gap-3">
                  {twoFAStatus.enabled ? (
                    <div className="w-10 h-10 rounded-xl bg-green-100 dark:bg-green-900/40 flex items-center justify-center">
                      <ShieldCheck className="h-5 w-5 text-green-600 dark:text-green-400" />
                    </div>
                  ) : (
                    <div className="w-10 h-10 rounded-xl bg-gray-200 dark:bg-white dark:bg-[#0b1e30]/10 flex items-center justify-center">
                      <ShieldOff className="h-5 w-5 text-gray-400" />
                    </div>
                  )}
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {twoFAStatus.enabled ? "2FA activé" : "2FA désactivé"}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {twoFAStatus.enabled
                        ? "Votre compte est protégé par Google Authenticator ou Authy."
                        : "Ajoutez une couche de sécurité supplémentaire à votre connexion."}
                    </p>
                  </div>
                </div>

                <div className="flex gap-2 shrink-0">
                  {!twoFAStatus.enabled ? (
                    <Button
                      className="bg-[#FF6200] hover:bg-[#E55900] text-white gap-2"
                      onClick={() => setShowSetupModal(true)}
                    >
                      <Shield className="h-4 w-4" />
                      Configurer le 2FA
                    </Button>
                  ) : (
                    <>
                      <Button
                        variant="outline"
                        className="gap-2"
                        onClick={() => setShowSetupModal(true)}
                        title="Reconfigurer (génère un nouveau QR code)"
                      >
                        <RefreshCw className="h-4 w-4" />
                        Reconfigurer
                      </Button>
                      {!twoFAStatus.required && (
                        <Button
                          variant="outline"
                          className="gap-2 text-red-500 border-red-200 hover:bg-red-50 dark:hover:bg-red-950/30"
                          onClick={() => setShowDisableModal(true)}
                        >
                          <ShieldOff className="h-4 w-4" />
                          Désactiver
                        </Button>
                      )}
                      {twoFAStatus.required && (
                        <span className="text-xs text-amber-600 dark:text-amber-400 self-center">
                          Non désactivable (rôle obligé)
                        </span>
                      )}
                    </>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Modals 2FA */}
        {showSetupModal && (
          <TwoFASetupModal
            onClose={() => setShowSetupModal(false)}
            onActivated={() => { setShowSetupModal(false); fetchTwoFAStatus(); }}
          />
        )}
        {showDisableModal && (
          <TwoFADisableModal
            onClose={() => setShowDisableModal(false)}
            onDisabled={() => { setShowDisableModal(false); fetchTwoFAStatus(); }}
          />
        )}

        {/* ── Liste des paramètres ──────────────────────────────────────── */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Settings className="h-5 w-5" /> Paramètres système</CardTitle>
            <CardDescription>{isSuperAdmin ? "Modifiable par le super_admin." : "Lecture seule."}</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? <Skeleton className="h-32 w-full" /> : params.length === 0 ? (
              <div className="text-center py-12 text-gray-500 dark:text-white/50">Aucun paramètre</div>
            ) : (
              <div className="space-y-3">
                {params.map((p) => {
                  const isEditing = p.cle in editing;
                  return (
                    <div key={p.cle} className="border rounded-lg p-4" data-testid={`param-${p.cle}`}>
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <Label className="font-mono text-xs text-gray-500 dark:text-white/50">{p.cle}</Label>
                          <p className="text-sm text-gray-600 dark:text-white/60">{p.description}</p>
                        </div>
                        {isSuperAdmin && !isEditing && (
                          <Button size="sm" variant="ghost" onClick={() => setEditing({ ...editing, [p.cle]: p.valeur })}>
                            <Edit className="h-3 w-3" />
                          </Button>
                        )}
                      </div>
                      {isEditing ? (
                        <div className="flex gap-2">
                          <Input value={editing[p.cle]} onChange={(e) => setEditing({ ...editing, [p.cle]: e.target.value })} className="flex-1" />
                          <Button size="sm" onClick={() => handleSave(p.cle)} disabled={saving[p.cle]} className="bg-[#FF6200] hover:bg-[#E55900]">
                            <Save className="h-3 w-3" />
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => { const e = { ...editing }; delete e[p.cle]; setEditing(e); }}>
                            <X className="h-3 w-3" />
                          </Button>
                        </div>
                      ) : (
                        <div className="font-medium text-[#0A2540] dark:text-white">{p.valeur}</div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
