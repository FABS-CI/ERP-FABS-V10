# ✅ Thème Dynamique — Checklist de Test

## 1️⃣ Tests Basiques

### 1.1 Installation & Build

```bash
# Vérifier que le build passe
cd /tmp/ERP-FABS-V10/frontend
npm run build

# ✅ Devrait compiler sans erreurs (max 0 warnings)
```

**Status:** [ ] Pass / [ ] Fail

---

### 1.2 ThemeProvider intégré dans App.js

```jsx
// Vérifier dans App.js
import { ThemeProvider } from "./contexts/ThemeContext";
import "./styles/theme.css";

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ThemeProvider>  // ← Présent?
          <AppWithIdle>
            ...
          </AppWithIdle>
        </ThemeProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
```

**Status:** [ ] Confirmé / [ ] À ajouter

---

### 1.3 Fichiers créés

- [ ] `/frontend/src/contexts/ThemeContext.jsx`
- [ ] `/frontend/src/hooks/useTheme.js`
- [ ] `/frontend/src/utils/themeUtils.js`
- [ ] `/frontend/src/styles/theme.css`
- [ ] `/frontend/src/components/themed/ThemedButton.jsx`
- [ ] `/frontend/src/components/themed/ThemedBadge.jsx`
- [ ] `/frontend/src/components/themed/ThemedStatCard.jsx`
- [ ] `/frontend/src/components/themed/index.js`
- [ ] `/frontend/src/config/theme.config.js`

**Status:** [ ] Tous présents / [ ] Manquants (lesquels?)

---

## 2️⃣ Tests de Détection Module

### 2.1 Navigation Dashboard (Bleu)

```
Allez à : http://localhost:3000/dashboard
Vérifiez :
- [ ] Page charge sans erreur
- [ ] Couleur dans devtools : --theme-primary = #3B82F6 (Bleu)
- [ ] localStorage contient : fabs.theme.activeModule = "dashboard"
```

**Screenshot utile :**
```javascript
// Console navigateur
{
  console.log("Couleur actuelle:", getComputedStyle(document.documentElement).getPropertyValue("--theme-primary"));
  console.log("Module actif:", localStorage.getItem("fabs.theme.activeModule"));
}
```

**Status:** [ ] Pass / [ ] Fail

---

### 2.2 Navigation Gestion Commerciale (Orange)

```
Allez à : http://localhost:3000/clients
Vérifiez :
- [ ] Transition fluide 0.3s vers Orange
- [ ] --theme-primary = #F97316 (Orange)
- [ ] fabs.theme.activeModule = "commerciale"
```

Testez aussi :
- http://localhost:3000/commandes → Orange ✓
- http://localhost:3000/factures → Orange ✓
- http://localhost:3000/paiements → Orange ✓

**Status:** [ ] Pass / [ ] Fail

---

### 2.3 Navigation Stocks (Vert)

```
Allez à : http://localhost:3000/produits
Vérifiez :
- [ ] Transition fluide vers Vert
- [ ] --theme-primary = #10B981 (Vert)
- [ ] fabs.theme.activeModule = "stocks"
```

Testez aussi :
- http://localhost:3000/stock → Vert ✓
- http://localhost:3000/colis → Vert ✓
- http://localhost:3000/logistique → Vert ✓

**Status:** [ ] Pass / [ ] Fail

---

### 2.4 Navigation Finances (Teal)

```
Allez à : http://localhost:3000/comptabilite
Vérifiez :
- [ ] Transition fluide vers Teal
- [ ] --theme-primary = #14B8A6 (Teal)
- [ ] fabs.theme.activeModule = "finances"
```

Testez aussi :
- http://localhost:3000/rapports → Teal ✓
- http://localhost:3000/fne → Teal ✓

**Status:** [ ] Pass / [ ] Fail

---

### 2.5 Navigation RH (Violet)

```
Allez à : http://localhost:3000/employes
Vérifiez :
- [ ] Transition fluide vers Violet
- [ ] --theme-primary = #8B5CF6 (Violet)
- [ ] fabs.theme.activeModule = "rh"
```

Testez aussi :
- http://localhost:3000/contrats → Violet ✓
- http://localhost:3000/paie → Violet ✓

**Status:** [ ] Pass / [ ] Fail

---

### 2.6 Navigation Admin (Gris)

```
Allez à : http://localhost:3000/parametres
Vérifiez :
- [ ] Transition fluide vers Gris
- [ ] --theme-primary = #9CA3AF (Gris)
- [ ] fabs.theme.activeModule = "admin"
```

Testez aussi :
- http://localhost:3000/utilisateurs → Gris ✓
- http://localhost:3000/documents → Gris ✓

**Status:** [ ] Pass / [ ] Fail

---

## 3️⃣ Tests des Composants Themés

### 3.1 ThemedButton

Créer une page de test :

```jsx
// pages/ThemeTest.jsx
import { ThemedButton } from "../components/themed";

export default function ThemeTest() {
  return (
    <div className="p-8">
      <h1>Teste Theme</h1>
      
      {/* Dashboard (Bleu) */}
      <h2>Dashboard (Bleu)</h2>
      <ThemedButton variant="primary">Primary</ThemedButton>
      <ThemedButton variant="outline">Outline</ThemedButton>
      <ThemedButton variant="ghost">Ghost</ThemedButton>
      <ThemedButton variant="light">Light</ThemedButton>
      
      {/* Clicker sur /clients → Orange */}
      {/* Vérifier que couleur change dynamiquement */}
    </div>
  );
}
```

**Tests :**

```
1. Aller à http://localhost:3000/theme-test?module=dashboard
   [ ] Tous les boutons sont Bleus
   [ ] Hover change couleur

2. Aller à http://localhost:3000/clients (puis retour au test)
   [ ] Boutons changent à Orange
   [ ] Transition fluide 0.3s

3. Aller à http://localhost:3000/produits (puis retour au test)
   [ ] Boutons changent à Vert
```

**Status:** [ ] Pass / [ ] Fail

---

### 3.2 ThemedBadge

```jsx
<div className="p-8">
  <ThemedBadge variant="solid">Solid</ThemedBadge>
  <ThemedBadge variant="outline">Outline</ThemedBadge>
  <ThemedBadge variant="light">Light</ThemedBadge>
</div>
```

**Tests :**
- [ ] Fond + texte changent avec le thème
- [ ] Transition fluide

**Status:** [ ] Pass / [ ] Fail

---

### 3.3 ThemedStatCard

```jsx
import { Users } from "lucide-react";
import { ThemedStatCard } from "../components/themed";

<ThemedStatCard
  icon={<Users className="w-8 h-8" />}
  label="Clients"
  value="1,245"
  trend="+5%"
/>
```

**Tests :**
- [ ] Bordure gauche avec couleur thème
- [ ] Icône avec couleur thème
- [ ] Gradient background avec couleur thème
- [ ] Transition fluide

**Status:** [ ] Pass / [ ] Fail

---

### 3.4 CSS Classes

```html
<!-- Test des classes CSS -->
<button class="btn-theme-primary">Primary</button>
<button class="btn-theme-outline">Outline</button>
<button class="btn-theme-ghost">Ghost</button>

<span class="badge-theme">Light</span>
<span class="badge-theme-solid">Solid</span>
<span class="badge-theme-outline">Outline</span>

<span class="status-indicator"></span>
<span class="status-dot"></span>

<div class="stat-card">...</div>

<a class="link-theme">Link</a>
```

**Tests :**
- [ ] Tous les boutons utilisent la couleur thème
- [ ] Tous les badges utilisent la couleur thème
- [ ] Indicateurs utilisent la couleur thème
- [ ] Liens utilisent la couleur thème

**Status:** [ ] Pass / [ ] Fail

---

## 4️⃣ Tests de Transition

### 4.1 Transition Fluide 0.3s

```bash
# Ouvrir DevTools → Console
# Naviguer rapidement entre pages
```

**Test rapide :**
1. Dashboard → Clients (Bleu → Orange)
2. Clients → Produits (Orange → Vert)
3. Produits → Comptabilité (Vert → Teal)

**Vérifier :**
- [ ] Transition fluide, pas de flash
- [ ] Durée ~0.3s
- [ ] Tous les éléments changent ensemble

**Status:** [ ] Pass / [ ] Fail

---

### 4.2 Timing (300ms)

```javascript
// Console
const start = performance.now();
// Naviguer vers autre page
// Vérifier que --theme-primary change dans 300ms
```

**Status:** [ ] < 400ms / [ ] > 400ms

---

## 5️⃣ Tests localStorage

### 5.1 Persistance du Module

```javascript
// Console
// 1. Aller à /clients
localStorage.getItem("fabs.theme.activeModule")
// → "commerciale" ✓

// 2. Rafraîchir la page (F5)
// Vérifier que couleur reste Orange
localStorage.getItem("fabs.theme.activeModule")
// → "commerciale" ✓

// 3. Aller à /produits
localStorage.getItem("fabs.theme.activeModule")
// → "stocks" ✓

// 4. Fermer et rouvrir le navigateur
// Vérifier que couleur est encore Vert
localStorage.getItem("fabs.theme.activeModule")
// → "stocks" ✓
```

**Status:** [ ] Pass / [ ] Fail

---

## 6️⃣ Tests de Performance

### 6.1 Lighthouse

```bash
# Ouvrir Chrome DevTools → Lighthouse
# Run audit → Performance
```

**Cibles :**
- [ ] Performance: > 90
- [ ] First Contentful Paint: < 1.5s
- [ ] Time to Interactive: < 3.5s

**Note:** Thème CSS variables ne devraient pas impacter score.

---

### 6.2 CPU Impact (DevTools Performance)

```bash
# DevTools → Performance tab
# Enregistrer navigation entre 2 pages
# Vérifier CPU usage
```

**Attente :**
- [ ] Pas de layout shift
- [ ] Pas de re-layout forcé
- [ ] CPU usage < 50% during transition

---

## 7️⃣ Tests de Compatibilité

### 7.1 Navigateurs

- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

**Vérifier :** Couleurs changent correctement sur tous les navigateurs

---

### 7.2 Appareils

- [ ] Desktop (1920x1080)
- [ ] Laptop (1366x768)
- [ ] Tablet (768x1024)
- [ ] Mobile (375x667)

**Vérifier :** Responsive design marche avec thème

---

### 7.3 Dark Mode

```bash
# Système → Activer Dark Mode
# Vérifier que couleurs restent lisibles
```

**Status:** [ ] Lisible / [ ] Illisible

---

## 8️⃣ Tests d'Intégration Réelle

### 8.1 Page Clients avec Thème (Orange)

**À intégrer :**
```jsx
import { ThemedButton, ThemedBadge } from "../components/themed";
import { useTheme } from "../hooks/useTheme";

export default function Clients() {
  const { themeColor, themeVariants } = useTheme();
  
  return (
    <div>
      <ThemedButton variant="primary">Nouveau</ThemedButton>
      <table>
        <tr>
          <td><ThemedBadge>Actif</ThemedBadge></td>
        </tr>
      </table>
    </div>
  );
}
```

**Tests :**
- [ ] Page charge correctement
- [ ] Bouton est Orange
- [ ] Badge est Orange
- [ ] Transition fluide vers/depuis page

**Status:** [ ] Pass / [ ] Fail

---

### 8.2 Page Produits avec Thème (Vert)

Même intégration que Clients, vérifier que couleur = Vert

**Status:** [ ] Pass / [ ] Fail

---

### 8.3 Page RH avec Thème (Violet)

Même intégration, vérifier que couleur = Violet

**Status:** [ ] Pass / [ ] Fail

---

## 9️⃣ Tests Edge Cases

### 9.1 Route Invalide

```
Allez à : http://localhost:3000/invalid-page
Vérifier :
- [ ] Couleur revient à Dashboard (Bleu)
- [ ] Pas d'erreur console
```

**Status:** [ ] Pass / [ ] Fail

---

### 9.2 Refresh Page Rapide

```bash
# Naviguer rapidement : Clients → Produits → Clients
# Appuyer F5 pendant la transition
```

**Vérifier :**
- [ ] Pas d'erreur
- [ ] Couleur finale est correcte

**Status:** [ ] Pass / [ ] Fail

---

### 9.3 localStorage Désactivé

```javascript
// Console
localStorage.clear()
// Naviguer entre pages
// Vérifier que thème marche quand même (via URL detection)
```

**Status:** [ ] Pass / [ ] Fail

---

### 9.4 Utilisateur sans permission pour module

```
Si user n'a pas accès à /clients
- [ ] Page redirect correctement
- [ ] Couleur n'est pas appliquée à une page vierge
```

**Status:** [ ] Pass / [ ] Fail

---

## 🔟 Documentation & Code Quality

### 10.1 Fichiers documentés

- [ ] `ThemeContext.jsx` : Commentaires clairs
- [ ] `themeUtils.js` : Fonction documentée
- [ ] `theme.css` : Sections commentées
- [ ] `THEME_SYSTEM_GUIDE.md` : Complet et à jour
- [ ] `THEME_INTEGRATION_EXAMPLE.md` : Exemples clairs

**Status:** [ ] Tous ok / [ ] À corriger

---

### 10.2 Pas de Warnings

```bash
npm run build 2>&1 | grep -i warning
```

**Attente :** 0 warnings (ou acceptables)

**Status:** [ ] Pass / [ ] Fail (lesquels?)

---

### 10.3 Pas d'Erreurs Console

Naviguer entre pages → Vérifier que console est vierge

**Status:** [ ] Vierge / [ ] Erreurs (lesquelles?)

---

## 📋 Résumé Final

| Section | Status | Notes |
|---------|--------|-------|
| Installation | [ ] | |
| Détection Module | [ ] | |
| Composants Themés | [ ] | |
| Transitions | [ ] | |
| localStorage | [ ] | |
| Performance | [ ] | |
| Compatibilité | [ ] | |
| Intégration Réelle | [ ] | |
| Edge Cases | [ ] | |
| Documentation | [ ] | |

**Date de test :** _______________

**Testeur :** _______________

**Verdict final :** [ ] ✅ Production-Ready / [ ] 🔴 À corriger

---

## 🐛 Bugs Trouvés

```markdown
### Bug 1: [Description]
**Route affected:** /path
**Severity:** High/Medium/Low
**Fix:** [Solution]
**Status:** [ ] Ouvert / [ ] Fermé

### Bug 2: [Description]
...
```

---

**Fin du checklist de test — À remplir progressivement**
