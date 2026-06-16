# Détection Doublons Commandes

## Plan
1. **Backend** — endpoint `POST /api/commandes/check-doublon`
   - Reçoit : client_id, lignes (produit_id, quantite), représentant, téléphone
   - Cherche commandes des 48h avec mêmes critères
   - Retourne : { doublon: bool, commande?: {...}, score: 'certain'|'probable' }
   - Log dans collection `doublon_logs`

2. **Frontend** — hook `useDoublonCheck` dans CommandeForm
   - Debounce 800ms sur changement client/lignes
   - Appel silencieux en background
   - Si doublon → Dialog d'alerte avec 3 actions

## Fichiers à modifier
- BACKEND: `commandes_module.py` → ajouter route check-doublon
- FRONTEND: `CommandeForm.jsx` → hook + dialog alerte
- FRONTEND: nouveau composant `DoublonAlert.jsx`

## État
- [ ] Backend endpoint
- [ ] Frontend hook debounce
- [ ] Dialog alerte
- [ ] Test
