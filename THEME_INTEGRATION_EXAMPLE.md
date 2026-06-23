# 🎨 Exemples d'Intégration — Thème Dynamique par Module

## Cas Réel 1: Page Clients (Gestion Commerciale)

### Avant (sans thème)

```jsx
// Clients.jsx
import { Plus, Edit2, Trash2, Eye } from "lucide-react";

export default function Clients() {
  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Gestion des clients</h1>
        <button className="px-4 py-2 bg-blue-600 text-white rounded">
          + Nouveau client
        </button>
      </div>

      <table className="w-full">
        <thead>
          <tr className="border-b">
            <th>Nom</th>
            <th>Email</th>
            <th>Statut</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {clients.map(client => (
            <tr key={client.id} className="border-b">
              <td>{client.nom}</td>
              <td>{client.email}</td>
              <td>
                <span className={`px-2 py-1 rounded text-sm ${
                  client.actif ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"
                }`}>
                  {client.actif ? "Actif" : "Inactif"}
                </span>
              </td>
              <td className="flex gap-2">
                <button className="p-1 hover:bg-gray-100">
                  <Eye className="w-4 h-4" />
                </button>
                <button className="p-1 hover:bg-gray-100">
                  <Edit2 className="w-4 h-4" />
                </button>
                <button className="p-1 hover:bg-gray-100">
                  <Trash2 className="w-4 h-4" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### Après (avec thème)

```jsx
// Clients.jsx
import { Plus, Edit2, Trash2, Eye } from "lucide-react";
import { ThemedButton, ThemedBadge } from "../components/themed";
import { useTheme } from "../hooks/useTheme";
import PageHeader from "../components/PageHeader";

export default function Clients() {
  const { themeColor, themeVariants } = useTheme();

  return (
    <div>
      {/* Header avec couleur de thème */}
      <PageHeader
        title="Gestion des clients"
        subtitle="Consultez et gérez tous vos clients"
        pagePath="/clients"
      />

      {/* Bouton primaire avec thème (Orange pour Gestion Commerciale) */}
      <div className="mb-6">
        <ThemedButton variant="primary" onClick={handleCreate}>
          <Plus className="w-4 h-4 mr-2 inline" />
          Nouveau client
        </ThemedButton>
      </div>

      {/* Table avec badges themés */}
      <div className="overflow-x-auto rounded-lg border" style={{ borderColor: themeVariants.light }}>
        <table className="w-full">
          <thead>
            <tr style={{ backgroundColor: themeVariants.lighter }}>
              <th className="px-4 py-3 text-left" style={{ color: themeVariants.darker }}>
                Nom
              </th>
              <th className="px-4 py-3 text-left" style={{ color: themeVariants.darker }}>
                Email
              </th>
              <th className="px-4 py-3 text-left" style={{ color: themeVariants.darker }}>
                Téléphone
              </th>
              <th className="px-4 py-3 text-left" style={{ color: themeVariants.darker }}>
                Statut
              </th>
              <th className="px-4 py-3 text-center" style={{ color: themeVariants.darker }}>
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {clients.map(client => (
              <tr
                key={client.id}
                className="border-b hover:bg-gray-50"
                style={{ borderColor: themeVariants.light }}
              >
                <td className="px-4 py-3 font-medium">{client.nom}</td>
                <td className="px-4 py-3">{client.email}</td>
                <td className="px-4 py-3">{client.telephone}</td>
                <td className="px-4 py-3">
                  {/* Badge avec couleur de thème */}
                  <ThemedBadge variant={client.actif ? "solid" : "outline"}>
                    {client.actif ? "Actif" : "Inactif"}
                  </ThemedBadge>
                </td>
                <td className="px-4 py-3 flex justify-center gap-2">
                  {/* Icônes avec couleur de thème */}
                  <button
                    className="p-2 rounded hover:bg-gray-100 transition"
                    onClick={() => handleView(client.id)}
                    title="Voir"
                  >
                    <Eye className="w-4 h-4" style={{ color: themeColor }} />
                  </button>
                  <button
                    className="p-2 rounded hover:bg-gray-100 transition"
                    onClick={() => handleEdit(client.id)}
                    title="Modifier"
                  >
                    <Edit2 className="w-4 h-4" style={{ color: themeColor }} />
                  </button>
                  <button
                    className="p-2 rounded hover:bg-red-100 transition"
                    onClick={() => handleDelete(client.id)}
                    title="Supprimer"
                  >
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

**Résultat :**
- Tout est en Orange (couleur de Gestion Commerciale)
- Bouton "Nouveau client" → Orange avec hover plus foncé
- Badge "Actif" → Orange clair/solid selon statut
- Icônes de vue/edit → Orange
- Bordures → Orange clair (20% opacité)
- En-tête table → Orange très clair (20% opacité)
- Au changement vers `/produits` → tout devient Vert automatiquement

---

## Cas Réel 2: Dashboard avec StatCards (Tableau de Bord)

### Intégration Complète

```jsx
// Dashboard.jsx
import { Users, ShoppingCart, TrendingUp, Package } from "lucide-react";
import { ThemedStatCard } from "../components/themed";
import { useTheme } from "../hooks/useTheme";

export default function Dashboard() {
  const { themeColor, themeVariants, activeModule } = useTheme();

  return (
    <div>
      <h1 className="text-3xl font-bold mb-2">Tableau de bord</h1>
      <p className="text-gray-600 mb-8">
        Bienvenue! Voici un aperçu de votre activité.
      </p>

      {/* Grid de StatCards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <ThemedStatCard
          icon={<Users className="w-8 h-8" />}
          label="Total clients"
          value="1,245"
          trend="+5.2%"
        />
        <ThemedStatCard
          icon={<ShoppingCart className="w-8 h-8" />}
          label="Commandes ce mois"
          value="324"
          trend="+12.1%"
        />
        <ThemedStatCard
          icon={<TrendingUp className="w-8 h-8" />}
          label="Chiffre d'affaires"
          value="$125,430"
          trend="+8.2%"
        />
        <ThemedStatCard
          icon={<Package className="w-8 h-8" />}
          label="Produits en stock"
          value="3,456"
        />
      </div>

      {/* Section Graphiques */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Carte Revenus */}
        <div
          className="p-6 rounded-lg border"
          style={{
            borderColor: themeVariants.light,
            backgroundColor: themeVariants.lighter,
          }}
        >
          <h3 className="text-lg font-bold mb-4" style={{ color: themeColor }}>
            Revenus ({new Date().getFullYear()})
          </h3>
          {/* Graphique ApexChart avec couleur thème */}
          <RevenueChart color={themeColor} />
        </div>

        {/* Carte Tendances */}
        <div
          className="p-6 rounded-lg border"
          style={{
            borderColor: themeVariants.light,
            backgroundColor: themeVariants.lighter,
          }}
        >
          <h3 className="text-lg font-bold mb-4" style={{ color: themeColor }}>
            Tendances
          </h3>
          {/* Graphique trends */}
          <TrendsChart color={themeColor} />
        </div>
      </div>

      {/* Section Rapides Actions */}
      <div className="mt-8">
        <h3 className="text-lg font-bold mb-4">Actions rapides</h3>
        <div className="flex flex-wrap gap-3">
          <ThemedButton variant="primary">+ Nouveau client</ThemedButton>
          <ThemedButton variant="outline">Voir les commandes</ThemedButton>
          <ThemedButton variant="ghost">Télécharger rapport</ThemedButton>
        </div>
      </div>
    </div>
  );
}

function RevenueChart({ color }) {
  // Configuration ApexCharts avec couleur de thème
  const options = {
    chart: { type: "line" },
    colors: [color],
    stroke: { colors: [color] },
  };
  return <ApexChart options={options} />;
}

function TrendsChart({ color }) {
  const options = {
    chart: { type: "bar" },
    colors: [color],
  };
  return <ApexChart options={options} />;
}
```

**Résultat :**
- Tous les StatCards héritent du thème Bleu (Dashboard)
- Les graphiques utilisent le Bleu
- Les cartes ont bordures + background avec variantes du Bleu
- Boutons au bas → Bleu

---

## Cas Réel 3: Produits (Stocks & Logistique)

```jsx
// Produits.jsx
import { ThemedButton, ThemedBadge } from "../components/themed";
import { useTheme } from "../hooks/useTheme";

export default function Produits() {
  const { themeColor, themeVariants } = useTheme();

  return (
    <div>
      <PageHeader
        title="Gestion des produits"
        pagePath="/produits"
      />

      <div className="mb-6">
        <ThemedButton variant="primary">+ Nouveau produit</ThemedButton>
      </div>

      {/* Cartes produits en grille */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {products.map(product => (
          <div
            key={product.id}
            className="p-6 rounded-lg border hover:shadow-lg transition"
            style={{
              borderColor: themeVariants.light,
              borderLeftWidth: "4px",
              borderLeftColor: themeColor,
            }}
          >
            {/* Image */}
            <img
              src={product.image}
              alt={product.nom}
              className="w-full h-40 object-cover rounded mb-4"
            />

            {/* Info */}
            <h3 className="font-bold text-lg">{product.nom}</h3>
            <p className="text-gray-600 text-sm mb-3">{product.description}</p>

            {/* Stock badge */}
            <div className="mb-4">
              <ThemedBadge variant={product.stock > 10 ? "solid" : "outline"}>
                Stock: {product.stock}
              </ThemedBadge>
            </div>

            {/* Prix */}
            <p className="text-2xl font-bold mb-4" style={{ color: themeColor }}>
              ${product.prix}
            </p>

            {/* Actions */}
            <div className="flex gap-2">
              <ThemedButton variant="primary" className="flex-1">
                Voir
              </ThemedButton>
              <ThemedButton variant="outline" className="flex-1">
                Éditer
              </ThemedButton>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Résultat :**
- Tout en Vert (couleur Stocks & Logistique)
- Bordure gauche des cartes en Vert
- Prix en Vert
- Boutons en Vert

---

## Cas Réel 4: Employés (RH)

```jsx
// Employes.jsx
import { ThemedButton, ThemedBadge } from "../components/themed";
import { useTheme } from "../hooks/useTheme";

export default function Employes() {
  const { themeColor, themeVariants } = useTheme();

  return (
    <div>
      <PageHeader
        title="Gestion des employés"
        pagePath="/employes"
      />

      <ThemedButton variant="primary">+ Nouvel employé</ThemedButton>

      {/* Onglets */}
      <div className="flex gap-4 mt-6 border-b" style={{ borderColor: themeVariants.light }}>
        <button
          className="px-4 py-2 border-b-2 transition"
          style={{
            borderColor: themeColor,
            color: themeColor,
            fontWeight: "600",
          }}
        >
          Tous ({employees.length})
        </button>
        <button
          className="px-4 py-2 border-b-2 transition text-gray-500"
          style={{ borderColor: "transparent" }}
        >
          Congés ({onLeave.length})
        </button>
        <button
          className="px-4 py-2 border-b-2 transition text-gray-500"
          style={{ borderColor: "transparent" }}
        >
          En arrêt ({onSick.length})
        </button>
      </div>

      {/* Table employés */}
      <table className="w-full mt-6">
        <thead>
          <tr style={{ backgroundColor: themeVariants.lighter }}>
            <th style={{ color: themeVariants.darker }}>Nom</th>
            <th style={{ color: themeVariants.darker }}>Poste</th>
            <th style={{ color: themeVariants.darker }}>Département</th>
            <th style={{ color: themeVariants.darker }}>Statut</th>
          </tr>
        </thead>
        <tbody>
          {employees.map(emp => (
            <tr key={emp.id} className="border-b">
              <td className="px-4 py-3">{emp.nom}</td>
              <td className="px-4 py-3">{emp.poste}</td>
              <td className="px-4 py-3">{emp.departement}</td>
              <td className="px-4 py-3">
                <ThemedBadge variant="solid">{emp.statut}</ThemedBadge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

**Résultat :**
- Tout en Violet (couleur RH)
- Onglet actif avec bordure Violet
- Table avec header Violet clair
- Badges Violet

---

## Checklist d'Intégration dans une Page

1. **Import hooks et composants**
   ```jsx
   import { useTheme } from "../hooks/useTheme";
   import { ThemedButton, ThemedBadge, ThemedStatCard } from "../components/themed";
   ```

2. **Utiliser useTheme()**
   ```jsx
   const { themeColor, themeVariants, activeModule } = useTheme();
   ```

3. **Remplacer couleurs hardcoded**
   - `bg-blue-600` → `style={{ backgroundColor: themeColor }}`
   - `text-blue-600` → `style={{ color: themeColor }}`
   - `border-blue-200` → `style={{ borderColor: themeVariants.light }}`

4. **Utiliser composants themés**
   - Boutons → `<ThemedButton>`
   - Badges → `<ThemedBadge>`
   - Cartes stat → `<ThemedStatCard>`

5. **Utiliser CSS classes**
   - Pour rapide → ajouter classe `btn-theme-primary` au lieu de style inline

6. **Tester navigation**
   - Naviguer entre modules
   - Vérifier transition fluide 0.3s
   - Vérifier localStorage persistance

---

## Performance Tips

✅ **Bon** : Utiliser CSS variables
```css
.my-element {
  color: var(--theme-primary);
}
```

❌ **Mauvais** : Utiliser inline styles avec hook à chaque render
```jsx
const { themeColor } = useTheme();
// ❌ Éviter si possible → re-render
return <div style={{ color: themeColor }} />;
```

✅ **Optimal** : Classes CSS + hook occasionnellement
```jsx
<div className="btn-theme-primary" />
// Hook seulement pour logique complexe ou gradients
```

---

**Fin des exemples**
