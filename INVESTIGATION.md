# Investigation: Bouton "Générer Facture" ne marche pas

## Symptôme
L'utilisateur rapporte que le bouton "valider une commande pour la transformer en facture" ne marche pas.

## Analyse

### Frontend (CommandeDetail.jsx)
- ✅ Bouton "Valider" affiche si `commande.statut === 'en_attente'` ET utilisateur a droits
- ✅ Bouton "Générer Facture" affiche si `canGenerateFacture()` retourne true
- Condition `canGenerateFacture()`:
  - statut doit être dans ['validee', 'preparee', 'livree']
  - `transformations.facture_generee` ne doit PAS être true
  - Rôle doit être dans ['super_admin', 'directeur_general', 'directeur_commercial', 'comptable']

### Backend (commandes_module.py)
- ✅ Endpoint POST /factures/generer-depuis-commande existe
- ✅ Retourne `transformations.facture_generee: facture is not None`

## Causes possibles

1. **Pas de commande en statut "validée"**
   - Les commandes de test sont en statut "brouillon" ou "en_attente"
   - Faut d'abord cliquer sur "Valider" pour que la commande passe en "validée"
   - Puis le bouton "Générer Facture" s'affichera

2. **Utilisateur n'a pas les droits**
   - Utilisateur doit être: super_admin, directeur_general, directeur_commercial, comptable
   - L'assistante ne peut pas générer de facture

3. **Erreur d'API silencieuse**
   - Vérifier les logs du backend
   - Vérifier la console du navigateur

## Tests à faire
- [ ] Créer une commande en statut "en_attente"
- [ ] Cliquer sur "Valider" (passer en "validée")
- [ ] Vérifier que le bouton "Générer Facture" apparaît
- [ ] Cliquer sur le bouton pour générer la facture
