# Uniformization Task — Session 2

## Progress So Far
- **Imports added:** All 12 Priority 1 files
- **Headers updated:** 2/12 (Approvisionnements, ApprovisionnementDetail)
- **Remaining:** 10/12

## Completed This Session
✅ Approvisionnements.jsx — header + actions replaced with PageHeader
✅ ApprovisionnementDetail.jsx — header + back button replaced, cleaned leftover markup

## Next (10 files)
- [ ] CommandeDetail.jsx
- [ ] FactureDetail.jsx
- [ ] FournisseurDetail.jsx
- [ ] Fournisseurs.jsx
- [ ] Employes.jsx
- [ ] ClientDetail.jsx
- [ ] DocumentsImpression.jsx
- [ ] Contrats.jsx
- [ ] EtatCompteClients.jsx
- [ ] PaiementDetail.jsx

## Pattern

Each file typically has:
```jsx
<div className="flex items-center justify-between flex-wrap gap-3">
  <div>
    <h1 className="text-3xl font-bold tracking-tight">...</h1>
    <p>Subtitle</p>
  </div>
  <div>
    <Buttons>
  </div>
</div>
```

Replace with:
```jsx
<PageHeader
  title="..."
  subtitle="..."
  pagePath="/path"
  actions={<Buttons />}
/>
```

## Notes
- All buttons changed from `bg-[#FF6200]` to `bg-blue-600 hover:bg-blue-700`
- Action buttons use `h-9` for alignment
- Some files (Detail pages) may have back navigation—handled by PageHeader's built-in Retour button
