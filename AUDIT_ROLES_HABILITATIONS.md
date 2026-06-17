# AUDIT ROLES & HABILITATIONS — ERP FABS-CI V10
**Date :** 17 juin 2026  
**Auteur :** Fabs Cl / Runable  
**Version :** 2.0 — Matrice validée production  
**Statut :** ✅ Appliqué (rbac_constants.py + modules + frontend)

---

## 1. PRINCIPE DIRECTEUR

> **Le DG ne touche pas au cycle opérationnel.**  
> Accès DG = `dashboard` (lecture) + `paiements` (lecture) + `rh` (lecture). Tout le reste est **0**.

Toute modification de cette règle nécessite validation explicite de Fabs.

---

## 2. MATRICE COMPLÈTE MODULE_PERMISSIONS

Légende : `0` = refusé · `1` = lecture · `2` = écriture · `—` = 0 implicite

| Module                     | super_admin | DG | comptable | dir_com | gest_stock | resp_mag | secretariat | svc_log | assistante |
|----------------------------|:-----------:|:--:|:---------:|:-------:|:----------:|:--------:|:-----------:|:-------:|:----------:|
| **dashboard**              | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 |
| **clients**                | 2 | **0** | 1 | 2 | 0 | 0 | 2 | 0 | 2 |
| **produits**               | 2 | **0** | 0 | 2 | 2 | 0 | **2** | 0 | **2** |
| **commandes**              | 2 | **0** | 2 | **1** | 1 | 1 | 2 | 0 | 2 |
| **factures**               | 2 | **0** | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| **paiements**              | 2 | **1** | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| **livraisons**             | 2 | **0** | **0** | **1** | **1** | 1 | 0 | 2 | 0 |
| **retours**                | 2 | **0** | 0 | **1** | 2 | **1** | 0 | 0 | 0 |
| **stock**                  | 2 | **0** | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| **colis**                  | 2 | **0** | 0 | **0** | **0** | 2 | 0 | 1 | 0 |
| **expeditions**            | 2 | **0** | 0 | **0** | 0 | 0 | 0 | 2 | 0 |
| **logistique**             | 2 | **0** | 0 | **0** | 0 | 0 | 0 | 2 | 0 |
| **notifications**          | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| **comptabilite**           | 2 | **0** | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| **comptabilite_avancee**   | 2 | **0** | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| **rh**                     | 2 | **1** | 1 | 1 | 0 | 0 | 2 | 0 | 0 |
| **bi_analytics**           | 2 | **0** | 0 | **0** | 0 | 0 | 0 | 0 | 0 |
| **workflow_approvals**     | 2 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **file_storage**           | 2 | **0** | **0** | 0 | 0 | 0 | **0** | 0 | 0 |
| **backup**                 | 2 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **rapports**               | 2 | **0** | 2 | **0** | 0 | 0 | 0 | 0 | 0 |
| **utilisateurs**           | 2 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **parametres**             | 2 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **fleet**                  | 2 | **0** | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| **logistics_costs**        | 2 | **0** | 1 | 0 | 0 | 0 | 0 | 2 | 0 |
| **multi_channel_notif.**   | 2 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

> **Gras** = changement par rapport à la version E1 précédente.

---

## 3. RÈGLES D'ACTIONS PAR MODULE

### 3.1 Commandes (`commandes_module.py`)

| Action       | Rôles autorisés |
|--------------|-----------------|
| READ         | super_admin, directeur_commercial, secretariat, comptable, assistante(_commerciale), gestionnaire_stock, responsable_magasinier |
| WRITE        | super_admin, secretariat, assistante(_commerciale), comptable |
| VALIDATE     | super_admin, secretariat, comptable |
| CANCEL       | super_admin, comptable, secretariat |
| PREPARE      | super_admin, responsable_magasinier |
| DELIVER      | super_admin, service_logistique |
| DELETE       | super_admin uniquement |

> DG retiré de toutes les actions. directeur_commercial = READ uniquement (via MODULE_PERMISSIONS commandes=1).

### 3.2 Factures (`factures_module.py`)

| Action       | Rôles autorisés |
|--------------|-----------------|
| READ         | super_admin, comptable |
| WRITE        | super_admin, comptable |
| PAYMENT      | super_admin, comptable |
| Relances     | super_admin, comptable |

> DG totalement retiré. Bug C1 corrigé : `"DG"` (string invalide) → `"comptable"`.

### 3.3 Proformas (`proformas_module.py`)

| Action       | Rôles autorisés |
|--------------|-----------------|
| READ         | super_admin, directeur_commercial, comptable, secretariat, assistante(_commerciale) |
| WRITE        | super_admin, secretariat, comptable, assistante(_commerciale) |
| SEND         | super_admin, secretariat, comptable, assistante(_commerciale) |
| CONVERT      | super_admin, comptable, secretariat |

> DG et directeur_commercial retirés de WRITE/SEND/CONVERT.

---

## 4. RÉCAPITULATIF DES CHANGEMENTS (vs version E1)

| # | Fichier | Changement |
|---|---------|------------|
| R01 | rbac_constants.py | DG → 0 sur : clients, produits, commandes, factures, livraisons, retours, stock, colis, expeditions, logistique, comptabilite, comptabilite_avancee, bi_analytics, workflow_approvals, file_storage, backup, rapports, utilisateurs, parametres, fleet, logistics_costs, multi_channel_notifications |
| R02 | rbac_constants.py | produits : secretariat 0→**2**, assistante 1→**2** |
| R03 | rbac_constants.py | commandes : dir_com 2→**1** (lecture seule) |
| R04 | rbac_constants.py | livraisons : comptable 2→**0**, dir_com 2→**1**, gest_stock 2→**1** |
| R05 | rbac_constants.py | retours : dir_com 2→**1**, resp_mag 2→**1** |
| R06 | rbac_constants.py | colis : dir_com 2→**0**, gest_stock 2→**0** |
| R07 | rbac_constants.py | expeditions : dir_com 2→**0** |
| R08 | rbac_constants.py | logistique : dir_com 2→**0** |
| R09 | rbac_constants.py | bi_analytics : dir_com 1→**0** |
| R10 | rbac_constants.py | file_storage : DG→0, comptable 1→**0**, secretariat 1→**0** |
| R11 | rbac_constants.py | rapports : dir_com 1→**0** |
| R12 | commandes_module.py | DG + dir_com retirés de WRITE/VALIDATE/CANCEL/PREPARE/DELIVER |
| R13 | factures_module.py | DG retiré de READ/WRITE/PAYMENT/RELANCES |
| **C1** | factures_module.py | **BUG CRITIQUE** : `"DG"` invalide ligne 1365 → corrigé en `{"super_admin","comptable"}` |
| R14 | proformas_module.py | DG + dir_com retirés de WRITE/SEND/CONVERT |
| R15 | frontend/permissions.js | Matrice frontend synchronisée |

---

## 5. RÔLES SYSTÈME — RÉSUMÉ ACCÈS

| Rôle | Accès résumé |
|------|-------------|
| **super_admin** | Tout (niveau 2 partout) |
| **directeur_general** | dashboard(R) · paiements(R) · rh(R) · notifications(R) — RIEN d'autre |
| **comptable** | factures(W) · paiements(W) · commandes(W) · comptabilite(W) · compta_avancee(W) · rh(R) · rapports(W) · clients(R) · logistics_costs(R) |
| **directeur_commercial** | clients(W) · produits(W) · commandes(R) · livraisons(R) · retours(R) · proformas(R) |
| **gestionnaire_stock** | produits(W) · stock(W) · commandes(R) · livraisons(R) · retours(W) |
| **responsable_magasinier** | commandes(R) · livraisons(R) · colis(W) · retours(R) · PREPARE commandes |
| **secretariat** | clients(W) · produits(W) · commandes(W) · rh(W) · WRITE proformas/commandes |
| **service_logistique** | livraisons(W) · expeditions(W) · logistique(W) · colis(R) · fleet(W) · logistics_costs(W) |
| **assistante** | clients(W) · produits(W) · commandes(W) · proformas WRITE/SEND |

---

## 6. NOTES FNE / DGI

- Module `fne` : accès `super_admin` + `comptable` (simulation DGI backend)
- Route spéciale simulation DGI : `super_admin` uniquement en production
- Frontend `fne` : DG = 0 (aucun accès interface)

---

## 7. FICHIERS MODIFIÉS

```
backend/rbac_constants.py          — MODULE_PERMISSIONS complet
backend/commandes_module.py        — READ/WRITE/VALIDATE/CANCEL/PREPARE/DELIVER_ROLES
backend/factures_module.py         — READ/WRITE/PAYMENT_ROLES + bug C1 ligne ~1365
backend/proformas_module.py        — READ/WRITE/SEND/CONVERT_ROLES
frontend/src/constants/permissions.js — Matrice frontend
```

---

*Dernière mise à jour : 2026-06-17 — Matrice RBAC v2.0 production*
