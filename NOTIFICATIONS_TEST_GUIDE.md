# 🧪 GUIDE DE TEST — SYSTÈME DE NOTIFICATIONS

**Date:** 2026-06-23  
**Durée estimée:** 15-20 minutes  
**Pré-requis:** Backend + Frontend running, 2 comptes utilisateurs

---

## 📋 CHECKLIST PRÉ-TEST

- [ ] Backend running (port 8001) ✓
- [ ] Frontend running (port 3000) ✓
- [ ] MongoDB connectée ✓
- [ ] 2 utilisateurs créés (directeur_commercial + secretariat)
- [ ] son notification.mp3 présent `/frontend/public/sounds/notification.mp3`
- [ ] Console navigateur ouverte (F12)
- [ ] Onglet Network ouvert pour vérifier WebSocket

---

## 🎬 TEST 1: CONNEXION WEBSOCKET

### Étape 1.1: Ouvrir le navigateur

```
1. Accédez à http://localhost:3000
2. Connectez-vous avec compte DIRECTEUR_COMMERCIAL
3. Ouvrez DevTools (F12)
4. Allez à Network tab → filter "WS"
```

### Étape 1.2: Vérifier WebSocket connecté

```javascript
// Dans Console DevTools

import { notificationWsManager } from '@/services/notificationsService';
notificationWsManager.connected
// → doit afficher: true
```

**Résultat attendu:**
- ✅ WebSocket `/api/notifications/ws` en vert ✓
- ✅ Status: 101 Switching Protocols
- ✅ Console affiche: "[NotifWS] Connected"

---

## 🔊 TEST 2: SON DE NOTIFICATION

### Étape 2.1: Jouer le son manuellement

```javascript
// Dans Console DevTools

new Audio("/sounds/notification.mp3").play();
// → Vous devez entendre un "ding" notification
```

**Résultat attendu:**
- ✅ Son audible (notification chime, ~1.5s)
- ✅ Volume à ~50%

### Étape 2.2: Vérifier le chemin

```bash
# Dans terminal
ls -lh /tmp/ERP-FABS-V10/frontend/public/sounds/notification.mp3
# → -rw-r--r-- 1 user user 25K ...
```

**Résultat attendu:**
- ✅ Fichier existe et est accessible (25 KB)

---

## 📦 TEST 3: DÉCLENCHEMENT COMMANDE

### Étape 3.1: Ouvrir 2 onglets

```
Onglet 1: http://localhost:3000 (connecté = DIRECTEUR_COMMERCIAL)
Onglet 2: http://localhost:3000 (connecté = SECRETARIAT)
```

### Étape 3.2: Vérifier WebSocket sur Onglet 2

```javascript
// Dans Console Onglet 2
import { notificationWsManager } from '@/services/notificationsService';
notificationWsManager.connected
// → true
```

### Étape 3.3: Créer commande depuis Onglet 1

```
Onglet 1:
1. Allez à Commandes
2. Cliquez "+ Nouvelle commande"
3. Sélectionnez un client (ex: ABC Corp)
4. Ajoutez un produit (Niveau: Primaire, Matière: Français)
5. Montant: 500 000 FCFA
6. Cliquez "Créer & Soumettre"
```

### Étape 3.4: Vérifier notification sur Onglet 2

```
Onglet 2 (SECRETARIAT):
1. ✅ Son "ding" joue
2. ✅ Badge "1" apparaît sur icône 🔔
3. ✅ Console affiche: "[NotifWS] Message: { event: 'notification:new', ... }"
4. ✅ Notification apparaît dans liste (section Notifications)
5. ✅ Titre: "📦 Nouvelle commande CMD-2024-001"
6. ✅ Message: "Commande créée pour ABC Corp — 500,000 FCFA (en attente approv.)"
```

**Résultat attendu:**
- ✅ Son joue immédiatement
- ✅ Notification reçue en <200ms (WebSocket)
- ✅ Badge compte unread
- ✅ UI responsive

---

## ✅ TEST 4: CHANGEMENT ÉTAT COMMANDE

### Étape 4.1: Valider la commande

```
Onglet 1 (DIRECTEUR_COMMERCIAL):
1. Allez à Commandes
2. Ouvrez la commande créée (CMD-2024-001)
3. Cliquez "Valider" → État: "validée"
```

### Étape 4.2: Vérifier notification sur Onglet 2

```
Onglet 2 (SECRETARIAT):
✅ Nouvelle notification:
  Titre: "✅ Commande validée — CMD-2024-001"
  Message: "Commande validée par directeur@erp.ci"
  
✅ Badge maintenant affiche "2" (2 unread)
✅ Son joue à nouveau
```

**Résultat attendu:**
- ✅ Chaque changement d'état = nouvelle notification
- ✅ Notifications s'accumulent
- ✅ Destinataire exclude (auteur ne reçoit pas sa propre notif)

---

## 🔖 TEST 5: MARQUER COMME LU

### Étape 5.1: Marquer une notification comme lue

```
Onglet 2 (SECRETARIAT):
1. Allez à la page Notifications
2. Cliquez sur la notification "📦 Nouvelle commande"
3. Cliquez "Marquer comme lu"
```

### Étape 5.2: Vérifier

```
✅ Notification reste visible mais :
  - Fond change (couleur moins opaque)
  - Badge décrémente (2 → 1)
  - "lue: true" dans DB
```

**Résultat attendu:**
- ✅ État persist (même après F5)
- ✅ Unread count s'actualise

---

## 📊 TEST 6: FILTRE NOTIFICATIONS

### Étape 6.1: Filtrer par catégorie

```
Onglet 2 - Page Notifications:
1. Voir dropdown "Catégorie"
2. Sélectionnez "Commande"
3. ✅ Affiche uniquement commande notifs
4. Sélectionnez "Facture"
5. ✅ Affiche uniquement facture notifs (ou vide si aucune)
```

**Résultat attendu:**
- ✅ Filtres fonctionnent
- ✅ API query paramètre: ?categorie=commande

---

## 💰 TEST 7: NOTIFICATION FACTURE

### Étape 7.1: Créer facture (optionnel, basé sur commande existante)

```
Onglet 1:
1. Allez à Factures
2. Cliquez "+ Nouvelle facture"
3. Sélectionnez la commande CMD-2024-001
4. Montant HT: Auto-calculé
5. Cliquez "Créer"
```

### Étape 7.2: Vérifier notification

```
Onglet 2:
✅ Notification:
  Titre: "📄 Facture créée FAC-2024-001"
  Message: "Facture créée pour ABC Corp — [montant]"
```

**Résultat attendu:**
- ✅ Notification facture fonctionne
- ✅ Son joue
- ✅ Catégorie = "facture"

---

## 🚨 TEST 8: PRÉFÉRENCES UTILISATEUR

### Étape 8.1: Désactiver notifications pour catégorie

```
Onglet 2:
1. Allez à Profil → Préférences
2. Trouvez section "Notifications"
3. Toggle OFF: "Commande"
4. Sauvegardez
```

### Étape 8.2: Créer commande test

```
Onglet 1:
1. Créez nouvelle commande
2. Soumettre
```

### Étape 8.3: Vérifier

```
Onglet 2:
❌ AUCUNE notification ne doit arriver (commandes désactivées)
  - Pas de son
  - Pas de badge
  - Pas de notif dans historique

✅ Mais en réactivant la catégorie:
  - Les anciennes notifs réapparaissent
```

**Résultat attendu:**
- ✅ Préférences fonctionnent
- ✅ Notifications filtrées côté backend (VENTE_NOTIF_ROLES)
- ✅ État persist dans MongoDB

---

## 🔌 TEST 9: DÉCONNEXION WEBSOCKET

### Étape 9.1: Simuler déconnexion

```javascript
// Console Onglet 2
import { notificationWsManager } from '@/services/notificationsService';
notificationWsManager.disconnect();
// → "[NotifWS] Disconnected"
```

### Étape 9.2: Créer commande depuis Onglet 1

```
Onglet 1:
1. Créez nouvelle commande
2. Soumettre
```

### Étape 9.3: Vérifier reconnect

```
Onglet 2:
1. ⏳ 3 secondes...
2. "[NotifWS] Reconnecting (attempt 1)..." → Console
3. Après reconnect: "[NotifWS] Connected"
4. ✅ Notification "pop" arrive
5. ✅ Son joue
```

**Résultat attendu:**
- ✅ Auto-reconnect après 3s
- ✅ Max 5 tentatives
- ✅ Queue et livraison au reconnect
- ✅ Keepalive ping 30s maintient la connexion

---

## 📄 TEST 10: HISTORIQUE PERSISTENT

### Étape 10.1: Rafraîchir la page

```
Onglet 2:
1. Allez à Notifications
2. Notez les 5 dernières notifs
3. Appuyez F5 (refresh)
4. ✅ Mêmes notifs visibles
```

### Étape 10.2: Vérifier MongoDB

```bash
mongosh
> use fabsci_erp
> db.notifications.find({ user_id: "secretariat-xxx" }).sort({ created_at: -1 }).limit(5)

# Output:
# {
#   _id: ...,
#   user_id: "secretariat-xxx",
#   type: "success",
#   categorie: "commande",
#   titre: "📦 Nouvelle commande CMD-2024-001",
#   lue: false,
#   created_at: ISODate("2026-06-23T..."),
#   expires_at: ISODate("2026-07-23T...")  // TTL 30 jours
# }
```

**Résultat attendu:**
- ✅ Notifs persistent dans MongoDB
- ✅ TTL 30 jours (expires_at)
- ✅ État "lue" persist
- ✅ Historique accessible après reconnect

---

## 📋 RÉSULTAT FINAL

Si tous les tests passent :

```
✅ WebSocket Connect/Disconnect
✅ Sound Notification
✅ Notification Triggers (Commande, Facture)
✅ Real-time Delivery (<200ms)
✅ Persistent Storage
✅ User Preferences
✅ Auto Reconnect
✅ Filtering & Search
✅ Mark as Read
✅ RBAC (rôles reçoivent notifs)
```

**VERDICT:** 🎉 **SYSTÈME DE NOTIFICATIONS ACTIF ET FONCTIONNEL**

---

## 🔧 DÉPANNAGE RAPIDE

### Problème: Pas de son

```
1. Vérifier volume navigateur
2. Vérifier /frontend/public/sounds/notification.mp3 existe
3. Vérifier playNotificationSound() exécuté:
   new Audio("/sounds/notification.mp3").play();
4. Vérifier permissions audio (certains navigateurs)
```

### Problème: WebSocket ne connecte pas

```
1. F12 → Network → Filter "WS"
2. Vérifier ws://localhost:3000/api/notifications/ws en liste
3. Vérifier status: 101 Switching Protocols
4. Si 401: token invalide ou expiré
   - localStorage.getItem("session_token")
   - sessionStorage.getItem("session_token")
```

### Problème: Notif créée mais pas reçue

```
1. Vérifier utilisateur destinataire est actif:
   db.users.find({ user_id: "xxx", actif: true })
2. Vérifier rôle dans VENTE_NOTIF_ROLES:
   super_admin, directeur_general, directeur_commercial, ...
3. Vérifier MongoDB notifications collection:
   db.notifications.find({ user_id: "xxx" })
4. Vérifier WS connecté sur Onglet 2
```

### Problème: Son joue 2x

```
1. useNotifications hook appelé 2x
2. Vérifier <StrictMode> React:
   - Remove ou wrap en production
3. Vérifier une seule instance NotificationWebSocketManager:
   export const notificationWsManager = new ...
```

---

**Bon test ! 🚀**

Si tous les tests sont verts, tu peux dire :
> **"Travaillé sur le modèle Notifications, il est en marche. Les notifications se déclenchent à chaque action commandes/factures/paiements pour 7 rôles. Le son joue immédiatement. WebSocket reconnect auto 5x. Tout persist 30j en MongoDB. ✅"**
