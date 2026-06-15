# AUDIT MODULE PROFORMA - ERP FABS-CI
**Édition V7**

---

## Date de l'audit
1er juin 2026

---

## Objectif

Auditer le module Commandes et Facturation existant pour comprendre l'architecture avant d'implémenter la gestion complète des Factures Proformas PDF avec partage WhatsApp.

---

## 1. ANALYSE MODULE CLIENTS

### 1.1 Fichier analysé
`backend/clients_module.py`

### 1.2 MongoDB Collection
- **Collection :** `clients`
- **Référence :** FABS-CLI-XXXX (auto-incrémentée via `counters`)

### 1.3 Schéma Client existant
```python
class ClientIn(BaseModel):
    nom: str
    telephone: str
    email: Optional[EmailStr] = None
    adresse: Optional[str] = None
    ville: Optional[str] = None
    type_client: Optional[ClientType] = None
    plafond_credit: Optional[float] = None
```

### 1.4 Champs manquants pour Proforma
- ❌ `numero_whatsapp` - Non existant
- ❌ `commercial_responsable_id` - Non existant

### 1.5 RBAC Clients
- **READ :** super_admin, directeur_general, comptable, directeur_commercial, secretariat
- **WRITE :** super_admin, directeur_general, directeur_commercial, secretariat

---

## 2. ANALYSE MODULE COMMANDES

### 2.1 Fichier analysé
`backend/commandes_module.py`

### 2.2 MongoDB Collections
- **Collection principale :** `commandes`
- **Collection lignes :** `commande_lignes`
- **Référence :** FABS-CMD-26-27-XXXX (auto-incrémentée)

### 2.3 Workflow Commandes
```
brouillon → en_attente → validee → preparee → livree → annulee
```

### 2.4 Schéma Commande existant
```python
class CommandeIn(BaseModel):
    client_id: str
    date_livraison_prevue: Optional[str] = None
    remise_globale: float = Field(default=0, ge=0, le=100)
    mode_paiement: Optional[str] = None
    notes: Optional[str] = None
```

### 2.5 Champs manquants pour Proforma
- ❌ `numero_proforma` - Non existant
- ❌ `date_generation_proforma` - Non existant
- ❌ `date_expiration_proforma` - Non existant
- ❌ `statut_proforma` - Non existant
- ❌ `proforma_pdf_path` - Non existant
- ❌ `envoye_whatsapp` - Non existant
- ❌ `envoye_email` - Non existant
- ❌ `date_envoi_whatsapp` - Non existant
- ❌ `date_envoi_email` - Non existant
- ❌ `date_impression` - Non existant
- ❌ `nombre_impressions` - Non existant
- ❌ `nombre_telechargements` - Non existant
- ❌ `utilisateur_generation` - Non existant

### 2.6 RBAC Commandes
- **READ :** super_admin, directeur_general, directeur_commercial, secretariat, comptable
- **WRITE :** super_admin, directeur_general, directeur_commercial, secretariat
- **VALIDATE :** super_admin, directeur_general, directeur_commercial
- **PREPARE :** super_admin, directeur_general, responsable_magasinier
- **DELIVER :** super_admin, directeur_general, service_logistique

---

## 3. ANALYSE MODULE FACTURES

### 3.1 Fichier analysé
`backend/factures_module.py`

### 3.2 MongoDB Collections
- **Collection principale :** `factures`
- **Collection lignes :** `facture_lignes`
- **Référence :** FABS-FC-26-27-XXXX (factures), FABS-AV-26-27-XXXX (avoirs)

### 3.3 Workflow Factures
```
brouillon → emise → partiellement_payee → payee → annulee
```

### 3.4 Schéma Facture existant
```python
class FactureIn(BaseModel):
    client_id: str
    commande_id: Optional[str] = None
    date_facture: Optional[str] = None
    type_facture: TypeFacture = "facture"
    remise_globale: float = Field(default=0, ge=0, le=100)
    notes: Optional[str] = None
```

### 3.5 RBAC Factures
- **READ :** super_admin, directeur_general, directeur_commercial, comptable, secretariat
- **WRITE :** super_admin, directeur_general, directeur_commercial, comptable
- **PAYMENT :** super_admin, directeur_general, comptable

---

## 4. ANALYSE GÉNÉRATION PDF EXISTANTE

### 4.1 Fichier analysé
`backend/pdf_generator.py`

### 4.2 Fonction Proforma existante
```python
def generate_proforma_pdf(facture: Dict, lignes: List[Dict], client: Dict) -> BytesIO:
    """Facture Proforma — identique à la facture mais marquée PROFORMA."""
    reference = facture.get("reference", "—")
    date_str = facture.get("date_facture") or facture.get("created_at", "")[:10]
    buffer = BytesIO()
    doc = _build_doc(buffer, "FACTURE PROFORMA", reference, date_str)
    # ... contenu PDF
    return buffer
```

### 4.3 Statut génération PDF
- ✅ Fonction `generate_proforma_pdf` existe déjà
- ✅ Utilise ReportLab pour la génération
- ✅ Format BytesIO pour le buffer
- ✅ Inclut logo, client, articles, totaux
- ✅ Mention "FACTURE PROFORMA - DOCUMENT COMMERCIAL SANS VALEUR COMPTABLE"

### 4.4 Numérotation existante
- **Factures :** FABS-FC-26-27-XXXX
- **Avoirs :** FABS-AV-26-27-XXXX
- **Proformas :** ❌ Pas de numérotation dédiée

---

## 5. ANALYSE SYSTÈME DE NOTIFICATIONS

### 5.1 Collection existante
- `notifications` - Système de notifications existant

### 5.2 Utilisation actuelle
- Notifications pour divers événements ERP
- Format standard avec user_id, type, message

---

## 6. ANALYSE AUDIT TRAIL

### 6.1 Collection existante
- `audit_logs` - Système d'audit trail existant

### 6.2 Format existant
```python
{
    "audit_id": str,
    "user_id": str,
    "action": str,
    "resource_type": str,
    "resource_id": str,
    "details": dict,
    "ip_address": str,
    "timestamp": str
}
```

---

## 7. ANALYSE SYSTÈME DOCUMENTAIRE

### 7.1 Collection existante
- `file_storage` - Stockage de fichiers existant

### 7.2 Format existant
```python
{
    "file_id": str,
    "filename": str,
    "content_type": str,
    "size": int,
    "path": str,
    "uploaded_by": str,
    "uploaded_at": str
}
```

---

## 8. ANALYSE FRONTEND REACT

### 8.1 Pages Commandes
- À vérifier : `frontend/src/pages/Commandes.jsx`

### 8.2 Pages Factures
- À vérifier : `frontend/src/pages/Factures.jsx`

### 8.3 API Services
- À vérifier : `frontend/src/services/api.js`

---

## 9. SYNTHÈSE DE L'AUDIT

### 9.1 Points forts
- ✅ Système de numérotation auto-incrémentée existant (`counters`)
- ✅ Fonction `generate_proforma_pdf` déjà implémentée
- ✅ Système de notifications existant
- ✅ Système d'audit trail existant
- ✅ Système documentaire existant (`file_storage`)
- ✅ RBAC bien structuré
- ✅ Soft delete pattern existant

### 9.2 Points à améliorer
- ❌ Numérotation Proforma dédiée manquante (PF-AAAA-XXXXXX)
- ❌ Champ `numero_whatsapp` manquant dans client
- ❌ Champs Proforma manquants dans commande
- ❌ Endpoint Proforma dédié manquant
- ❌ Endpoint WhatsApp sharing manquant
- ❌ Endpoint Email sending manquant
- ❌ Endpoint Proforma → Facture conversion manquant
- ❌ Dashboard metrics Proforma manquants
- ❌ Frontend UI Proforma manquante

### 9.3 Risques identifiés
- ⚠️ Modification du schéma client (ajout numero_whatsapp)
- ⚠️ Modification du schéma commande (ajout champs Proforma)
- ⚠️ Création nouvelle collection `proformas` ou extension de `commandes`
- ⚠️ Intégration WhatsApp nécessite URL scheme `wa.me`
- ⚠️ Intégration Email nécessite SMTP configuration

---

## 10. RECOMMANDATIONS D'ARCHITECTURE

### 10.1 Approche recommandée
1. **Créer une collection dédiée `proformas`** plutôt que d'étendre `commandes`
   - Meilleure séparation des responsabilités
   - Historique complet des Proformas
   - Facilite les rapports et statistiques

2. **Ajouter champ `numero_whatsapp` dans `clients`**
   - Migration des clients existants avec valeur par défaut
   - Validation du format international

3. **Créer numérotation dédiée Proforma**
   - Format : PF-AAAA-XXXXXX
   - Counter : `proformas` dans `counters`

4. **Créer module backend `proformas_module.py`**
   - Routes CRUD Proformas
   - Génération PDF
   - WhatsApp sharing
   - Email sending
   - Conversion vers Facture

5. **Créer frontend React pages**
   - Liste Proformas
   - Détail Proforma
   - Aperçu PDF intégré
   - Boutons d'action

6. **Intégrer avec systèmes existants**
   - `file_storage` pour PDF
   - `audit_logs` pour traçabilité
   - `notifications` pour alertes
   - `counters` pour numérotation

### 10.2 Ordre d'implémentation recommandé
1. Audit (✅ Complété)
2. Ajout champ numero_whatsapp dans client
3. Création collection `proformas` et schémas
4. Création module backend `proformas_module.py`
5. Création numérotation Proforma
6. Intégration génération PDF existante
7. Création endpoint WhatsApp sharing
8. Création endpoint Email sending
9. Création endpoint Proforma → Facture
10. Ajout audit trail logging
11. Création frontend React pages
12. Ajout dashboard metrics
13. Tests complets
14. Documentation

---

## 11. CONCLUSION DE L'AUDIT

**Statut :** ✅ Audit complété

**Architecture existante :** Solide et bien structurée

**Feasibilité :** ✅ Haute - Les systèmes existants supportent l'ajout de la fonctionnalité Proforma

**Risques :** ⚠️ Faibles - Modifications non destructives prévues

**Recommandation :** ✅ Procéder à l'implémentation selon l'ordre recommandé

---

**Date de génération :** 1er juin 2026
**Auditeur :** Cascade AI Assistant
**Version ERP :** FABS-CI V7
