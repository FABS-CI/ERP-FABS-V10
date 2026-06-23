# Navigation Uniformization Task

## Objectif
Uniformiser la navigation entre tous les modules avec :
- ✅ Bouton Retour (ArrowLeft)
- ✅ Bouton Tableau de bord / Accueil
- ✅ Bouton Ajouter aux favoris
- ✅ PageHeader component réutilisable

## PageHeader Component
✅ Créé: `/frontend/src/components/PageHeader.jsx`
- Gère Retour, Tableau de bord, Favoris
- Supporte actions personnalisées (ex: Créer nouveau)
- Design responsive dark mode

---

## Pages à Uniformiser (44 fichiers)

### 🔴 CRITIQUES (Modules commerciaux) - À faire EN PRIORITÉ
- [ ] Clients.jsx - imports/structure
- [ ] Commandes.jsx
- [ ] CommandeDetail.jsx
- [ ] Factures.jsx
- [ ] FactureDetail.jsx
- [ ] Paiements.jsx
- [ ] Proformas.jsx
- [ ] BonsLivraison.jsx
- [ ] BonsRetour.jsx

### 🟡 IMPORTANT (Stocks & Logistique)
- [ ] Stock.jsx
- [ ] ProduitsInventaire.jsx
- [ ] Colis.jsx
- [ ] Expeditions.jsx
- [ ] Logistique.jsx
- [ ] LogistiqueHub.jsx

### 🟢 UTILES (Autres)
- [ ] Utilisateurs.jsx
- [ ] Parametres.jsx
- [ ] Conges.jsx
- [ ] Absences.jsx
- [ ] Comptabilite.jsx
- [ ] Notifications.jsx
- [ ] FNE.jsx
- [ ] Et autres...

---

## Pattern à Appliquer

### Import
```javascript
import PageHeader from "../components/PageHeader";
```

### Utilisation (Simple)
```jsx
<DashboardLayout>
  <PageHeader
    title="Titre de la page"
    subtitle="Description courte"
    pagePath="/path/to/page"
  />
  
  {/* Contenu */}
</DashboardLayout>
```

### Avec Actions Personnalisées
```jsx
<PageHeader
  title="Clients"
  subtitle="Gestion des clients"
  pagePath="/clients"
  actions={
    <Button onClick={() => navigate("/clients/new")}>
      <Plus className="w-4 h-4 mr-2" />
      Nouveau Client
    </Button>
  }
/>
```

---

## Commits
- ✅ 39e6e37 - Fix greeting (DADJE au lieu de AHOMAN)
- ✅ 6d91701 - Add EmployeForm component
- [ ] Next: Uniformize Clients.jsx
- [ ] Next: Uniformize Commandes.jsx
- [ ] Next: Uniformize core pages
- [ ] Final: Remaining pages

---

## Status: IN PROGRESS
Start: 2026-06-23 11:55 UTC
