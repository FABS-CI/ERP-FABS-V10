# Tâche : Classification auto produits + stats + docs de vente

## Décisions
- Classif = règles déterministes (classification.py) ✅
- Backfill 56 produits ✅ (0 sans matière)
- Docs de vente : TOUS (facture, proforma, BL, commande) afficher matière + classe par ligne ✅
- Stats par ville = ville du client ✅

## TOUT FAIT ✅
- [x] classification.py (matière/cycle/niveau/catégorie)
- [x] Schéma ProductIn/Patch/Out + matiere/cycle
- [x] project_product expose matiere/cycle
- [x] create/update auto-classifient
- [x] backfill 56 produits en base
- [x] import_real_data.py classifie + section Littérature = autorité
- [x] BUG-01 : résolu — resolve_produit() + $or partout dans commandes/factures
- [x] Enrichissement lignes : matiere/niveau_scolaire/cycle dans commande_lignes et facture_lignes
- [x] PDF generator : colonnes Niveau/Matière par ligne, groupement par cycle (commande + facture + BL)
- [x] Stats analytics : /by-matiere, /by-niveau, /by-cycle, /by-ville → opérationnels
- [x] UI front : champs Catégorie/Matière/Cycle/Niveau dans ProductFormDialog.jsx
- [x] Test bout-en-bout : création commande → PDF ✅ | facture → PDF ✅ | stats par matière ✅

## BUGS CONNUS RESTANTS
- BUG-02 : non reproduit (pdf_generator ne crashe pas sur client sans adresse/ville) — surveiller en prod

## POINTS D'ATTENTION FUTURS
- 7 produits avec a_completer=true (prix_vente=1 FCFA) → à compléter manuellement
- classify() ne détecte pas seul les annales "RÉUSSIR MES..." → forcer matière à la saisie
- Stats analytics démarrent à la création réelle de commandes (base actuellement 0 commandes/factures)
