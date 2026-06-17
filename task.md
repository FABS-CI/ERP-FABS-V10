# TÂCHE : Anti-doublons workflow + Code Article/Niveau sur docs de vente

## CHANTIER 1 — Anti-doublons (CRITIQUE)
Empêcher actions multiples sur une commande/document. Backend + UI.

### Actions à protéger
- [ ] Générer facture (commande -> facture) : 1 seule facture principale/commande
- [ ] Générer avoir
- [ ] Préparer commande
- [ ] Valider préparation
- [ ] Générer BL
- [ ] Expédier
- [ ] Réceptionner (achats)
- [ ] Clôturer
- [ ] Annuler

### Backend
- [ ] Bloquer si transformation déjà faite -> 409/400 message clair
- [ ] Idempotence : vérifier existence avant création

### Frontend
- [ ] Masquer/désactiver bouton après action
- [ ] Badge "✓ Facture générée FAC-XXX"
- [ ] Bloc état des transformations sur fiche commande

## CHANTIER 2 — Code Article + Niveau docs de vente
- [ ] Chaque produit : code_article (FABS-CIxx) + niveau/section
- [ ] Afficher sur PDF : factures, BL, avoirs, proformas, commandes
- Fichier source: /home/user/Attachments/ARTICLES_FABS_CI_NUMEROTES_amavZT.txt (56 articles, 5 sections)

## AUDIT FAIT
### Backend
- Facture depuis commande : DÉJÀ protégé (unicité commande_id+type facture) ✓
- Préparer/valider/livrer/annuler : protégés par garde de STATUT ✓ (transition irréversible)
- Avoir : protégé (impossible avoir depuis avoir) ✓
- **BL : PAS protégé** -> on peut créer N bons de livraison pour 1 commande ❌ À FIXER
- Commande renvoie-t-elle facture_id/bl_id existants ? -> à enrichir pour l'UI

### Frontend (CommandeDetail.jsx)
- valider/preparer/livrer : conditionnés par statut, disparaissent OK ✓
- **"Générer Facture" : visible meme si facture deja creee** ❌ -> afficher badge "✓ Facture FAC-XX" + lien, masquer bouton
- Pas de bloc "état des transformations" ❌ À AJOUTER
- BL : voir où il est généré côté UI

## PLAN — AVANCEMENT
1. [x] Backend BL : bloque 2e BL si commande totalement livrée (409) ✓
2. [x] Backend commande detail : champ `transformations` (facture, bons_livraison, flags) ✓ testé
3. [x] Frontend : canGenerateFacture exclut facture existante + badge + bloc "État des transformations" ✓
4. [ ] Chantier 2 : code article + niveau sur docs vente (EN COURS)
   - [ ] Vérifier champs produits en base (code_article, niveau)
   - [ ] Importer/mapper depuis le catalogue txt si manquant
   - [ ] pdf_generator : colonnes Code Article + Niveau sur factures/BL/avoirs/proformas/commandes
