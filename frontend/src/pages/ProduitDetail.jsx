import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft, Pencil, PowerOff, BookOpen, Wallet, Package, Calendar, AlertCircle,
  FileText, History, ShoppingCart,
} from "lucide-react";
import { toast } from "sonner";

import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";
import ProductFormDialog from "../components/products/ProductFormDialog";
import StockBadge from "../components/products/StockBadge";
import { CATEGORIES_MAP, getProduct, disableProduct } from "../services/produitsApi";
import { formatFCFA } from "../utils/format";
import { useAuth } from "../hooks/useAuth";

const WRITE_ROLES = new Set(["super_admin", "directeur_general", "directeur_commercial", "gestionnaire_stock", "responsable_magasinier"]);
const FINANCIAL_ROLES = new Set(["super_admin", "directeur_general", "comptable"]);

const TABS = [
  { key: "info",      label: "Informations",       icon: FileText },
  { key: "mouvements", label: "Mouvements stock",  icon: History },
  { key: "commandes", label: "Historique commandes", icon: ShoppingCart },
];

export default function ProduitDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { role } = useAuth();
  const canWrite = WRITE_ROLES.has(role);
  const seePrixAchat = FINANCIAL_ROLES.has(role);

  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState("info");
  const [edit, setEdit] = useState(false);

  const refresh = async () => {
    setLoading(true); setError(null);
    try { setProduct(await getProduct(id)); }
    catch (e) { setError(e?.response?.data?.detail || "Produit introuvable"); }
    finally { setLoading(false); }
  };
  useEffect(() => { refresh(); /* eslint-disable-next-line */ }, [id]);

  const handleDisable = async () => {
    if (!window.confirm(`Désactiver le produit "${product.titre}" ?`)) return;
    try { setProduct(await disableProduct(product.product_id)); toast.success("Produit désactivé"); }
    catch (e) { toast.error(e?.response?.data?.detail || "Échec"); }
  };

  if (loading) return <DashboardLayout><div className="text-sm text-gray-500 dark:text-white/50 p-8">Chargement…</div></DashboardLayout>;

  if (error || !product) {
    return (
      <DashboardLayout>
        <div className="bg-red-50 border border-[#C62828]/30 text-[#C62828] rounded-lg p-4 text-sm flex items-center gap-2 max-w-2xl">
          <AlertCircle className="w-4 h-4" /> {error || "Produit introuvable"}
          <button onClick={() => navigate("/produits")} className="ml-auto text-xs font-semibold underline">← Retour</button>
        </div>
      </DashboardLayout>
    );
  }

  const cat = CATEGORIES_MAP[product.categorie] || CATEGORIES_MAP.primaire;
  const marge = seePrixAchat && product.prix_achat != null
    ? product.prix_vente - product.prix_achat
    : null;

  return (
    <DashboardLayout>
      <div data-testid="produit-detail-page" className="max-w-6xl mx-auto">
        <button data-testid="produit-detail-back" onClick={() => navigate("/produits")}
          className="inline-flex items-center gap-1.5 text-xs text-gray-500 dark:text-white/50 hover:text-[#FF6200] transition-colors mb-4">
          <ArrowLeft className="w-3.5 h-3.5" /> Catalogue produits
        </button>

        {/* Header */}
        <div className="bg-white dark:bg-white dark:bg-[#0b1e30]/5 rounded-xl border border-gray-200 dark:border-white/10 p-6 shadow-sm">
          <div className="flex flex-wrap items-start gap-4 justify-between">
            <div className="flex-1 min-w-0">
              <div className="flex items-center flex-wrap gap-3">
                <span className="inline-flex items-center text-[10px] uppercase tracking-wider font-bold px-2 py-0.5 rounded"
                  style={{ background: cat.bg, color: cat.color }}>{cat.label}</span>
                <span className="font-mono text-xs text-gray-500 dark:text-white/50">{product.reference}</span>
                <StockBadge statut={product.statut_stock} stock_actuel={product.stock_actuel} stock_minimum={product.stock_minimum} />
                {!product.actif && (
                  <span className="text-[10px] uppercase tracking-wider bg-gray-200 dark:bg-white dark:bg-[#0b1e30]/10 text-gray-500 dark:text-white/60 px-2 py-0.5 rounded">Désactivé</span>
                )}
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-[#0A2540] dark:text-white mt-2">{product.titre}</h1>
              <p className="text-sm text-gray-600 dark:text-white/70 mt-1">
                {[product.auteur, product.collection, product.niveau_scolaire].filter(Boolean).join(" · ")}
              </p>
              {product.isbn && (
                <p className="text-xs text-gray-500 dark:text-white/50 mt-1 font-mono">ISBN {product.isbn}</p>
              )}
            </div>
            {canWrite && product.actif && (
              <div className="flex gap-2">
                <button data-testid="produit-detail-edit" onClick={() => setEdit(true)}
                  className="inline-flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold text-[#0A2540] dark:text-white bg-gray-100 dark:bg-white dark:bg-[#0b1e30]/10 hover:bg-gray-200 dark:hover:bg-white dark:bg-[#0b1e30]/20">
                  <Pencil className="w-3.5 h-3.5" /> Modifier
                </button>
                <button data-testid="produit-detail-disable" onClick={handleDisable}
                  className="inline-flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold text-[#C62828] bg-[#C62828]/10 hover:bg-[#C62828]/20">
                  <PowerOff className="w-3.5 h-3.5" /> Désactiver
                </button>
              </div>
            )}
          </div>

          {/* KPI */}
          <div className={`grid grid-cols-2 sm:grid-cols-${seePrixAchat ? 4 : 3} gap-4 mt-6 pt-6 border-t border-gray-100 dark:border-white/10`}>
            <KPI icon={Wallet} accent="#FF6200" label="Prix de vente" value={formatFCFA(product.prix_vente)} />
            {seePrixAchat && (
              <KPI icon={Wallet} accent="#0A2540" label="Prix d'achat" value={product.prix_achat != null ? formatFCFA(product.prix_achat) : "—"} />
            )}
            {seePrixAchat && marge != null && (
              <KPI icon={Wallet} accent="#2E7D32" label={`Marge unitaire`} value={formatFCFA(marge)} />
            )}
            <KPI icon={Package} accent={product.statut_stock === "rupture" ? "#C62828" : product.statut_stock === "alerte" ? "#FF6200" : "#2E7D32"}
              label="Stock actuel" value={`${product.stock_actuel} u.`} />
            <KPI icon={Calendar} accent="#7C5BC4" label="Créé le" value={new Date(product.created_at).toLocaleDateString("fr-FR")} />
          </div>
        </div>

        {/* Tabs */}
        <div className="mt-6">
          <div data-testid="produit-detail-tabs" className="flex flex-wrap gap-1 border-b border-gray-200 dark:border-white/10">
            {TABS.map(({ key, label, icon: Icon }) => {
              const active = key === tab;
              return (
                <button key={key} data-testid={`produit-detail-tab-${key}`} onClick={() => setTab(key)}
                  className={`inline-flex items-center gap-1.5 px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors ${
                    active ? "border-[#FF6200] text-[#FF6200]" : "border-transparent text-gray-500 dark:text-white/60 hover:text-[#0A2540] dark:hover:text-white"
                  }`}>
                  <Icon className="w-3.5 h-3.5" /> {label}
                </button>
              );
            })}
          </div>

          <div className="mt-5">
            {tab === "info" && (
              <div data-testid="produit-detail-info" className="bg-white dark:bg-white dark:bg-[#0b1e30]/5 rounded-xl border border-gray-200 dark:border-white/10 p-6 shadow-sm">
                <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4">
                  {[
                    ["Référence",       product.reference],
                    ["Titre",           product.titre],
                    ["Auteur",          product.auteur || "—"],
                    ["Collection",      product.collection || "—"],
                    ["Catégorie",       cat.label],
                    ["Matière",         product.matiere || "—"],
                    ["Cycle",           product.cycle || "—"],
                    ["Niveau scolaire", product.niveau_scolaire || "—"],
                    ["ISBN",            product.isbn || "—"],
                    ["Prix de vente",   formatFCFA(product.prix_vente)],
                    ...(seePrixAchat ? [["Prix d'achat", product.prix_achat != null ? formatFCFA(product.prix_achat) : "—"]] : []),
                    ["Stock actuel",    `${product.stock_actuel} unité${product.stock_actuel > 1 ? "s" : ""}`],
                    ["Seuil alerte",    `${product.stock_minimum} unités`],
                    ["Créé le",         new Date(product.created_at).toLocaleString("fr-FR")],
                    ["Mis à jour",      new Date(product.updated_at).toLocaleString("fr-FR")],
                  ].map(([k, v]) => (
                    <div key={k}>
                      <dt className="text-[10px] uppercase tracking-wider font-semibold text-gray-500 dark:text-white/50">{k}</dt>
                      <dd className="text-sm text-[#0A2540] dark:text-white mt-1 break-words">{v}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            )}
            {tab === "mouvements" && <OngletMouvementsStock productId={id} />}
            {tab === "commandes" && <OngletHistoriqueCommandes productId={id} />}
          </div>
        </div>
      </div>

      <ProductFormDialog open={edit} onClose={() => setEdit(false)} product={product}
        onSaved={(saved) => { setProduct(saved); setEdit(false); }} />
    </DashboardLayout>
  );
}

// ============ ONGLET MOUVEMENTS STOCK ============
function OngletMouvementsStock({ productId }) {
  const [mouvements, setMouvements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState("");
  const [page, setPage] = useState(0);
  const limit = 20;

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // ✅ PHASE 3.2: fetch with credentials to include HttpOnly cookies
        const res = await fetch(`/api/stock/mouvements?produit_id=${productId}&type=${typeFilter}&skip=${page * limit}&limit=${limit}`, {
          credentials: "include"
        });
        if (res.ok) {
          const data = await res.json();
          setMouvements(data.items || []);
        }
      } catch (e) {
        console.error('Erreur mouvements:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [productId, typeFilter, page]);

  const typeColors = {
    entree: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100",
    sortie: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100",
    retour: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100",
    ajustement: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100",
  };

  return (
    <div className="space-y-4">
      {/* Filtres */}
      <div className="flex gap-2">
        <select 
          value={typeFilter} 
          onChange={(e) => { setTypeFilter(e.target.value); setPage(0); }}
          className="px-3 py-2 border border-gray-300 dark:border-white/10 rounded-lg bg-white dark:bg-[#0b1e30] text-sm"
        >
          <option value="">Tous les types</option>
          <option value="entree">Entrée</option>
          <option value="sortie">Sortie</option>
          <option value="retour">Retour</option>
          <option value="ajustement">Ajustement</option>
        </select>
      </div>

      {/* Tableau */}
      <div className="bg-white dark:bg-[#0b1e30]/5 rounded-xl border border-gray-200 dark:border-white/10 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Chargement...</div>
        ) : mouvements.length === 0 ? (
          <div className="p-8 text-center text-gray-500">Aucun mouvement trouvé</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-white/5 border-b border-gray-200 dark:border-white/10">
              <tr>
                <th className="px-4 py-3 text-left font-semibold text-gray-700 dark:text-white/70">Date</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700 dark:text-white/70">Type</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700 dark:text-white/70">Quantité</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700 dark:text-white/70">Motif</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700 dark:text-white/70">Utilisateur</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700 dark:text-white/70">Référence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-white/10">
              {mouvements.map((m) => (
                <tr key={m.mouvement_id} className="hover:bg-gray-50 dark:hover:bg-white/5">
                  <td className="px-4 py-3 text-gray-900 dark:text-white">{new Date(m.created_at).toLocaleString("fr-FR")}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${typeColors[m.type_mouvement] || 'bg-gray-100'}`}>
                      {m.type_mouvement}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-semibold text-gray-900 dark:text-white">{m.quantite}</td>
                  <td className="px-4 py-3 text-gray-700 dark:text-white/70 text-xs">{m.motif || "—"}</td>
                  <td className="px-4 py-3 text-gray-700 dark:text-white/70 text-xs">{m.utilisateur || "—"}</td>
                  <td className="px-4 py-3 text-gray-700 dark:text-white/70 text-xs font-mono">{m.commande_id || m.bl_id || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {mouvements.length > 0 && (
        <div className="flex justify-between items-center">
          <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0} className="px-3 py-2 bg-gray-200 dark:bg-white/10 rounded disabled:opacity-50">Précédent</button>
          <span className="text-sm text-gray-600 dark:text-white/60">Page {page + 1}</span>
          <button onClick={() => setPage(page + 1)} className="px-3 py-2 bg-gray-200 dark:bg-white/10 rounded">Suivant</button>
        </div>
      )}
    </div>
  );
}

// ============ ONGLET HISTORIQUE COMMANDES ============
function OngletHistoriqueCommandes({ productId }) {
  const [commandes, setCommandes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statutFilter, setStatutFilter] = useState("");
  const [page, setPage] = useState(0);
  const limit = 20;

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // ✅ PHASE 3.2: fetch with credentials to include HttpOnly cookies
        const res = await fetch(`/api/commandes?produit_id=${productId}&statut=${statutFilter}&skip=${page * limit}&limit=${limit}`, {
          credentials: "include"
        });
        if (res.ok) {
          const data = await res.json();
          setCommandes(data.items || []);
        }
      } catch (e) {
        console.error('Erreur commandes:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [productId, statutFilter, page]);

  const statutColors = {
    brouillon: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-100",
    confirmee: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100",
    en_cours: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100",
    livree: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100",
    annulee: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100",
  };

  return (
    <div className="space-y-4">
      {/* Filtres */}
      <div className="flex gap-2">
        <select 
          value={statutFilter} 
          onChange={(e) => { setStatutFilter(e.target.value); setPage(0); }}
          className="px-3 py-2 border border-gray-300 dark:border-white/10 rounded-lg bg-white dark:bg-[#0b1e30] text-sm"
        >
          <option value="">Tous les statuts</option>
          <option value="brouillon">Brouillon</option>
          <option value="confirmee">Confirmée</option>
          <option value="en_cours">En cours</option>
          <option value="livree">Livrée</option>
          <option value="annulee">Annulée</option>
        </select>
      </div>

      {/* Tableau */}
      <div className="bg-white dark:bg-[#0b1e30]/5 rounded-xl border border-gray-200 dark:border-white/10 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Chargement...</div>
        ) : commandes.length === 0 ? (
          <div className="p-8 text-center text-gray-500">Aucune commande trouvée</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-white/5 border-b border-gray-200 dark:border-white/10">
              <tr>
                <th className="px-4 py-3 text-left font-semibold text-gray-700 dark:text-white/70">Commande</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700 dark:text-white/70">Client</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700 dark:text-white/70">Date</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700 dark:text-white/70">Quantité</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700 dark:text-white/70">Statut</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-white/10">
              {commandes.map((c) => (
                <tr key={c.commande_id} className="hover:bg-gray-50 dark:hover:bg-white/5 cursor-pointer">
                  <td className="px-4 py-3 font-mono text-xs text-[#FF6200]">{c.reference || c.commande_id}</td>
                  <td className="px-4 py-3 text-gray-900 dark:text-white text-sm">{c.client_nom || c.client_id}</td>
                  <td className="px-4 py-3 text-gray-700 dark:text-white/70 text-sm">{new Date(c.date_commande).toLocaleDateString("fr-FR")}</td>
                  <td className="px-4 py-3 text-right font-semibold text-gray-900 dark:text-white">{c.quantite_produit || "—"}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${statutColors[c.statut] || 'bg-gray-100'}`}>
                      {c.statut}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {commandes.length > 0 && (
        <div className="flex justify-between items-center">
          <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0} className="px-3 py-2 bg-gray-200 dark:bg-white/10 rounded disabled:opacity-50">Précédent</button>
          <span className="text-sm text-gray-600 dark:text-white/60">Page {page + 1}</span>
          <button onClick={() => setPage(page + 1)} className="px-3 py-2 bg-gray-200 dark:bg-white/10 rounded">Suivant</button>
        </div>
      )}
    </div>
  );
}

function KPI({ icon: Icon, accent, label, value }) {
  return (
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: `${accent}18` }}>
        <Icon className="w-5 h-5" style={{ color: accent }} />
      </div>
      <div>
        <p className="text-[10px] uppercase tracking-wider text-gray-500 dark:text-white/50">{label}</p>
        <p className="text-sm font-bold text-[#0A2540] dark:text-white mt-0.5 whitespace-nowrap">{value}</p>
      </div>
    </div>
  );
}
