# Phase 2 - Extensions Fonctionnelles - Document de Cadrage

## 1. Vue d'ensemble

### Objectifs de Phase 2
Phase 2 vise à étendre les fonctionnalités de l'ERP avec quatre modules critiques pour les opérations logistiques et financières :
- **Packaging/Colisage** : Gestion des colis et préparation des expéditions
- **Notifications** : Système de notifications et alertes métier
- **Logistique et Transport** : Gestion des missions logistiques et livraisons
- **Comptabilité Avancée** : Plan comptable, journaux, rapprochement bancaire

### Contexte
Phase 1 a sécurisé et optimisé la plateforme. Phase 2 se concentre sur l'ajout de fonctionnalités métier essentielles pour :
- Améliorer l'efficacité opérationnelle
- Automatiser les processus manuels
- Renforcer le suivi et la traçabilité
- Améliorer la gestion financière

---

## 2. Architecture Fonctionnelle

### 2.1 Module Packaging / Colisage

#### Fonctionnalités principales
1. **Gestion des Colis**
   - Création de colis à partir de lignes de commande
   - Association de produits aux colis
   - Gestion des poids et dimensions
   - Étiquetage des colis (codes-barres/QR)

2. **Préparation des Expéditions**
   - Groupement de colis en expéditions
   - Gestion des adresses de livraison
   - Validation avant expédition
   - Génération de documents d'expédition

3. **Suivi des Quantités Expédiées**
   - Mise à jour automatique des stocks
   - Suivi en temps réel des quantités
   - Rapports d'expédition par commande
   - Historique des mouvements

4. **Historique des Mouvements**
   - Traçabilité complète des colis
   - Journal des opérations
   - Audit trail des modifications

#### Cas d'utilisation
- **Préparateur** : Crée des colis, prépare les expéditions
- **Responsable Logistique** : Valide les expéditions, consulte les rapports
- **Commercial** : Suit l'état des expéditions de ses clients

#### Intégrations
- Module Commandes (source des lignes à emballer)
- Module Stock (mise à jour des quantités)
- Module Bons de Livraison (génération automatique)

---

### 2.2 Module Notifications

#### Fonctionnalités principales
1. **Notifications Système**
   - Notifications in-app (toast, badge)
   - Centre de notifications
   - Préférences utilisateur
   - Historique des notifications

2. **Alertes Métier**
   - Alertes stock (rupture, alerte)
   - Alertes commandes (en attente, retard)
   - Alertes paiements (échéance, impayé)
   - Alertes livraison (en cours, livré)

3. **Rappels de Paiement**
   - Rappels automatiques avant échéance
   - Relances après échéance
   - Personnalisation des messages
   - Suivi des relances

4. **Emails Automatiques**
   - Confirmation de commande
   - Notification d'expédition
   - Facture envoyée
   - Reçu de paiement
   - Templates personnalisables

#### Cas d'utilisation
- **Utilisateur** : Consulte ses notifications, configure ses préférences
- **Système** : Envoie automatiquement des notifications basées sur des événements
- **Administrateur** : Configure les règles de notification

#### Intégrations
- Tous les modules existants (déclenchement d'événements)
- Module Email (envoi d'emails)
- Module Utilisateurs (préférences)

---

### 2.3 Module Logistique et Transport

#### Fonctionnalités principales
1. **Missions Logistiques**
   - Création de missions de livraison
   - Assignation de chauffeurs/véhicules
   - Planification des itinéraires
   - Gestion des priorités

2. **Suivi des Livraisons**
   - GPS tracking (optionnel)
   - Statuts de livraison en temps réel
   - Preuve de livraison (signature, photo)
   - Mises à jour depuis mobile

3. **Gestion des Coûts Logistiques**
   - Coûts de transport par mission
   - Analyse des coûts par client/zone
   - Optimisation des itinéraires
   - Rapports de rentabilité

4. **Tableaux de Bord Opérationnels**
   - Vue d'ensemble des livraisons en cours
   - Performance des chauffeurs
   - KPIs logistiques
   - Alertes opérationnelles

#### Cas d'utilisation
- **Responsable Logistique** : Planifie les missions, suit les livraisons
- **Chauffeur** : Consulte ses missions, met à jour les statuts
- **Directeur** : Consulte les tableaux de bord, analyse les coûts

#### Intégrations
- Module Packaging (source des expéditions)
- Module Bons de Livraison (validation)
- Module Clients (adresses de livraison)

---

### 2.4 Module Comptabilité Avancée

#### Fonctionnalités principales
1. **Plan Comptable**
   - Configuration du plan comptable SYSCOHADA
   - Hiérarchie des comptes
   - Association automatique (produits → comptes)
   - Import/Export du plan comptable

2. **Journaux Comptables**
   - Journal des ventes (ACH)
   - Journal des achats (ACQ)
   - Journal de banque (BQ)
   - Journal des OD (Opérations Diverses)
   - Génération automatique d'écritures

3. **Écritures Automatiques**
   - Écritures de facturation
   - Écritures de règlement
   - Écritures d'avoir
   - Écritures de régularisation

4. **Rapprochement Bancaire**
   - Import des relevés bancaires
   - Lettrage automatique
   - Rapprochement manuel
   - Écarts de rapprochement

#### Cas d'utilisation
- **Comptable** : Configure le plan comptable, valide les écritures
- **Directeur Financier** : Consulte les journaux, analyse les écarts
- **Système** : Génère automatiquement les écritures

#### Intégrations
- Module Factures (génération d'écritures)
- Module Paiements (génération d'écritures)
- Module Bons de Retour (génération d'avoirs)

---

## 3. Architecture Technique

### 3.1 Stack Technologique

#### Backend
- **Framework** : FastAPI (Python)
- **Base de données** : MongoDB
- **Cache** : Redis
- **File d'attente** : Celery + Redis (pour notifications asynchrones)
- **Email** : SendGrid/AWS SES (via boto3)

#### Frontend
- **Framework** : React
- **State Management** : React Query
- **UI Components** : Radix UI + Tailwind CSS
- **Routing** : React Router
- **Real-time** : WebSocket (optionnel pour notifications en temps réel)

#### Infrastructure
- **Monitoring** : Prometheus + Grafana
- **Logging** : Audit logs existants
- **CI/CD** : GitHub Actions (existants)

### 3.2 Architecture des Modules

#### Pattern Architectural
Chaque module suit le pattern établi dans Phase 1 :
- **Backend Module** : `module_module.py` avec router, schemas, helpers
- **Frontend Pages** : Pages React avec API services
- **API Services** : Services Axios pour les appels API
- **RBAC** : Contrôle d'accès basé sur les rôles

#### Nouveaux Patterns pour Phase 2

**Event-Driven Architecture (Notifications)**
```python
# Event bus pour notifications
async def publish_event(event_type: str, payload: dict):
    await redis.publish(f"events:{event_type}", json.dumps(payload))

# Event listeners
async def listen_for_events():
    pubsub = redis.pubsub()
    await pubsub.subscribe("events:*")
    async for message in pubsub.listen():
        await process_notification(message)
```

**Background Tasks (Celery)**
```python
# Tâches asynchrones pour emails
@celery.task
def send_payment_reminder_email(client_id, amount, due_date):
    # Logique d'envoi d'email
    pass
```

---

## 4. Modèle de Données

### 4.1 Module Packaging / Colisage

#### Collection `colis`
```javascript
{
  colis_id: "colis_uuid",
  reference: "FABS-COL-2026-XXXX",
  commande_id: "cmd_uuid",
  ligne_commande_ids: ["ligne1", "ligne2"],
  produits: [
    {
      produit_id: "prod_uuid",
      quantite: 10,
      poids_unitaire: 0.5,
      poids_total: 5.0
    }
  ],
  poids_total: 5.0,
  dimensions: { longueur: 30, largeur: 20, hauteur: 15 },
  statut: "en_preparation" | "pret" | "expedie",
  expedition_id: "exp_uuid" | null,
  code_barres: "1234567890123",
  qr_code: "https://erp.fabsci.ci/colis/colis_uuid",
  created_at: "2026-01-01T00:00:00Z",
  created_by: "user_uuid",
  updated_at: "2026-01-01T00:00:00Z"
}
```

#### Collection `expeditions`
```javascript
{
  expedition_id: "exp_uuid",
  reference: "FABS-EXP-2026-XXXX",
  colis_ids: ["colis1", "colis2"],
  commande_id: "cmd_uuid",
  client_id: "client_uuid",
  adresse_livraison: {
    nom: "Client Nom",
    adresse: "123 Rue Principale",
    ville: "Abidjan",
    pays: "Côte d'Ivoire",
    telephone: "+225 XX XX XX XX XX"
  },
  transporteur: "transporteur_uuid" | null,
  statut: "en_preparation" | "pret" | "en_transit" | "livre" | "annule",
  date_expedition: "2026-01-01",
  date_livraison_prevue: "2026-01-02",
  date_livraison_reelle: "2026-01-02" | null,
  notes: "Instructions spéciales",
  created_at: "2026-01-01T00:00:00Z",
  created_by: "user_uuid",
  updated_at: "2026-01-01T00:00:00Z"
}
```

#### Collection `mouvements_colis`
```javascript
{
  mouvement_id: "mouv_uuid",
  colis_id: "colis_uuid",
  type_mouvement: "creation" | "modification" | "expedition" | "reception",
  details: { ... },
  user_id: "user_uuid",
  timestamp: "2026-01-01T00:00:00Z"
}
```

---

### 4.2 Module Notifications

#### Collection `notifications`
```javascript
{
  notification_id: "notif_uuid",
  user_id: "user_uuid",
  type: "info" | "warning" | "error" | "success",
  categorie: "stock" | "commande" | "paiement" | "livraison" | "systeme",
  titre: "Titre de la notification",
  message: "Message détaillé",
  lien: "/path/to/resource" | null,
  lue: false,
  created_at: "2026-01-01T00:00:00Z",
  expires_at: "2026-01-08T00:00:00Z" | null
}
```

#### Collection `notification_preferences`
```javascript
{
  user_id: "user_uuid",
  preferences: {
    stock_alertes: true,
    commande_alertes: true,
    paiement_alertes: true,
    livraison_alertes: true,
    email_notifications: true,
    in_app_notifications: true
  },
  updated_at: "2026-01-01T00:00:00Z"
}
```

#### Collection `email_templates`
```javascript
{
  template_id: "tpl_uuid",
  code: "confirmation_commande",
  sujet: "Confirmation de votre commande #{reference}",
  corps_html: "<html>...</html>",
  corps_texte: "Texte brut...",
  variables: ["reference", "client_nom", "montant"],
  actif: true,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z"
}
```

#### Collection `email_logs`
```javascript
{
  email_log_id: "log_uuid",
  template_id: "tpl_uuid",
  destinataire: "client@example.com",
  sujet: "Sujet de l'email",
  statut: "envoye" | "en_attente" | "echec",
  erreur: null | "Error message",
  variables: { ... },
  sent_at: "2026-01-01T00:00:00Z" | null
}
```

---

### 4.3 Module Logistique et Transport

#### Collection `missions_logistiques`
```javascript
{
  mission_id: "mission_uuid",
  reference: "FABS-MIS-2026-XXXX",
  expedition_ids: ["exp1", "exp2"],
  chauffeur_id: "user_uuid" | null,
  vehicule_id: "veh_uuid" | null,
  date_mission: "2026-01-01",
  itineraire: [
    {
      expedition_id: "exp1",
      ordre: 1,
      adresse: "123 Rue A",
      statut: "en_attente" | "en_cours" | "livre"
    }
  ],
  statut: "planifie" | "en_cours" | "termine" | "annule",
  distance_totale_km: 50.5,
  cout_transport: 15000,
  notes: "Instructions spéciales",
  created_at: "2026-01-01T00:00:00Z",
  created_by: "user_uuid",
  updated_at: "2026-01-01T00:00:00Z"
}
```

#### Collection `vehicules`
```javascript
{
  vehicule_id: "veh_uuid",
  reference: "FABS-VEH-001",
  type: "camion" | "fourgonnette" | "moto",
  immatriculation: "AB-123-CD",
  capacite_kg: 1000,
  capacite_m3: 5.0,
  chauffeur_id: "user_uuid" | null,
  statut: "disponible" | "en_mission" | "maintenance",
  created_at: "2026-01-01T00:00:00Z"
}
```

#### Collection `suivi_livraisons`
```javascript
{
  suivi_id: "suivi_uuid",
  expedition_id: "exp_uuid",
  mission_id: "mission_uuid",
  statut: "en_transit" | "livre" | "retarde" | "annule",
  localisation: { latitude: 5.345, longitude: -4.123 } | null,
  preuve_livraison: {
    signature: "base64_signature" | null,
    photo: "base64_photo" | null,
    commentaire: "Commentaire"
  },
  updated_by: "user_uuid",
  updated_at: "2026-01-01T00:00:00Z"
}
```

---

### 4.4 Module Comptabilité Avancée

#### Collection `plan_comptable`
```javascript
{
  compte_id: "cpt_uuid",
  numero: "411000",
  intitule: "Clients",
  parent_id: "41" | null,
  type: "actif" | "passif" | "charge" | "produit",
  classe: 4,
  solde_debit: 0,
  solde_credit: 0,
  actif: true,
  created_at: "2026-01-01T00:00:00Z"
}
```

#### Collection `journaux_comptables`
```javascript
{
  journal_id: "journal_uuid",
  code: "ACH",
  intitule: "Journal des Ventes",
  type: "ventes" | "achats" | "banque" | "od",
  actif: true,
  created_at: "2026-01-01T00:00:00Z"
}
```

#### Collection `ecritures_comptables`
```javascript
{
  ecriture_id: "ecr_uuid",
  journal_id: "journal_uuid",
  reference: "FABS-ECR-2026-XXXX",
  date_ecriture: "2026-01-01",
  libelle: "Facture FC-2026-0001",
  lignes: [
    {
      compte_id: "cpt_uuid",
      compte_numero: "411000",
      compte_intitule: "Clients",
      debit: 118000,
      credit: 0
    },
    {
      compte_id: "cpt_uuid",
      compte_numero: "701000",
      compte_intitule: "Ventes de marchandises",
      debit: 0,
      credit: 100000
    }
  ],
  montant_total_debit: 118000,
  montant_total_credit: 118000,
  reference_source: "facture_uuid",
  type_source: "facture",
  created_at: "2026-01-01T00:00:00Z",
  created_by: "system"
}
```

#### Collection `rapprochements_bancaires`
```javascript
{
  rapprochement_id: "rapp_uuid",
  compte_bancaire_id: "cpt_uuid",
  date_rapprochement: "2026-01-01",
  solde_initial: 1000000,
  solde_final: 950000,
  ecritures_lettrees: ["ecr1", "ecr2"],
  operations_bancaires: [
    {
      date: "2026-01-01",
      reference: "REF123",
      libelle: "Virement client",
      montant: 50000,
      lettrage: "ecr1" | null
    }
  ],
  ecarts: [
    {
      type: "ecart_montant",
      description: "Écart de 500 FCFA",
      montant: 500
    }
  ],
  created_at: "2026-01-01T00:00:00Z",
  created_by: "user_uuid"
}
```

---

## 5. Dépendances entre Modules

### Graphe des Dépendances

```
Phase 2 Modules Dependencies:

Packaging/Colisage
├── Commandes (existant)
├── Stock (existant)
└── Bons de Livraison (existant)

Notifications
├── Tous les modules existants (déclenchement)
└── Utilisateurs (existant)

Logistique et Transport
├── Packaging/Colisage (nouveau)
├── Bons de Livraison (existant)
└── Clients (existant)

Comptabilité Avancée
├── Factures (existant)
├── Paiements (existant)
└── Bons de Retour (existant)
```

### Ordre de Développement Recommandé

1. **Sprint 2.1** : Packaging/Colisage (indépendant, fondation pour logistique)
2. **Sprint 2.2** : Notifications (indépendant, bénéfique pour tous les modules)
3. **Sprint 2.3** : Logistique et Transport (dépend de Packaging)
4. **Sprint 2.4** : Comptabilité Avancée (indépendant, module financier)

---

## 6. Roadmap Détaillée des Sprints

### Sprint 2.1 - Module Packaging/Colisage (2 semaines)

#### Semaine 1
- **Jour 1-2** : Modèle de données, création collections MongoDB
- **Jour 3-4** : Backend API (CRUD colis, expéditions)
- **Jour 5** : Intégration avec Commandes et Stock

#### Semaine 2
- **Jour 1-2** : Frontend pages (Liste colis, Détail colis, Création colis)
- **Jour 3-4** : Frontend expéditions (Liste, Détail, Création)
- **Jour 5** : Tests, documentation, validation

#### Livrables
- Backend: `colisage_module.py`
- Frontend: Pages Colis et Expéditions
- Documentation: API docs, user guide

---

### Sprint 2.2 - Module Notifications (2 semaines)

#### Semaine 1
- **Jour 1-2** : Modèle de données, système d'événements
- **Jour 3-4** : Backend API (notifications, préférences, templates)
- **Jour 5** : Intégration email (SendGrid/SES)

#### Semaine 2
- **Jour 1-2** : Frontend centre de notifications
- **Jour 3** : Configuration des règles de notification
- **Jour 4** : Intégration événements dans modules existants
- **Jour 5** : Tests, documentation, validation

#### Livrables
- Backend: `notifications_module.py`, event bus
- Frontend: Centre de notifications, configuration
- Documentation: Guide configuration notifications

---

### Sprint 2.3 - Module Logistique et Transport (3 semaines)

#### Semaine 1
- **Jour 1-2** : Modèle de données, création collections
- **Jour 3-4** : Backend API (missions, véhicules, suivi)
- **Jour 5** : Intégration avec Packaging

#### Semaine 2
- **Jour 1-2** : Frontend missions (Liste, Détail, Création)
- **Jour 3-4** : Frontend véhicules et suivi
- **Jour 5** : Tableaux de bord opérationnels

#### Semaine 3
- **Jour 1-2** : Optimisation itinéraires (algorithme simple)
- **Jour 3-4** : Rapports coûts logistiques
- **Jour 5** : Tests, documentation, validation

#### Livrables
- Backend: `logistique_module.py`
- Frontend: Pages Logistique, Tableaux de bord
- Documentation: Guide logistique

---

### Sprint 2.4 - Comptabilité Avancée (3 semaines)

#### Semaine 1
- **Jour 1-2** : Modèle de données, plan comptable SYSCOHADA
- **Jour 3-4** : Backend API (plan comptable, journaux)
- **Jour 5** : Import/Export plan comptable

#### Semaine 2
- **Jour 1-2** : Backend écritures automatiques (factures, paiements)
- **Jour 3-4** : Backend rapprochement bancaire
- **Jour 5** : Intégration avec Factures et Paiements

#### Semaine 3
- **Jour 1-2** : Frontend plan comptable et journaux
- **Jour 3-4** : Frontend rapprochement bancaire
- **Jour 5** : Tests, documentation, validation

#### Livrables
- Backend: `comptabilite_avancee_module.py`
- Frontend: Pages Comptabilité Avancée
- Documentation: Guide comptabilité

---

### Sprint 2.5 - Consolidation et Validation (1 semaine)

#### Activités
- **Jour 1-2** : Tests d'intégration inter-modules
- **Jour 3** : Performance testing
- **Jour 4** : Documentation finale
- **Day 5** : Validation et handoff

#### Livrables
- Rapport de validation Phase 2
- Documentation complète
- Plan de déploiement

---

## 7. Estimation de Charge

### Estimation en Jours-Homme

| Sprint | Module | Durée (semaines) | Jours-homme | Complexité |
|--------|--------|-----------------|-------------|------------|
| 2.1 | Packaging/Colisage | 2 | 10 | Moyenne |
| 2.2 | Notifications | 2 | 10 | Moyenne |
| 2.3 | Logistique/Transport | 3 | 15 | Élevée |
| 2.4 | Comptabilité Avancée | 3 | 15 | Élevée |
| 2.5 | Consolidation | 1 | 5 | Faible |
| **Total** | | **11** | **55** | |

### Répartition par Rôle

| Rôle | Jours-homme | Pourcentage |
|------|-------------|-------------|
| Backend Developer | 25 | 45% |
| Frontend Developer | 20 | 36% |
| DevOps/Infrastructure | 5 | 9% |
| QA/Testing | 5 | 9% |
| **Total** | **55** | **100%** |

### Coût Estimatif (Basé sur 400€/jour)

- **Total** : 55 jours-homme × 400€ = **22,000€**

---

## 8. Analyse des Risques

### Risques Techniques

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Performance MongoDB avec nouvelles collections | Moyenne | Moyen | Indexation appropriée, monitoring |
| Latence notifications temps réel | Moyenne | Faible | Utilisation Redis pub/sub, fallback polling |
| Complexité rapprochement bancaire | Élevée | Moyen | Tests approfondis, validation manuelle |
| Intégration email (SendGrid/SES) | Faible | Faible | Fallback SMTP local |

### Risques Fonctionnels

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Changements requirements mid-sprint | Moyenne | Moyen | Sprint planning détaillé, validation avant |
| Adoption utilisateurs (nouvelles fonctionnalités) | Moyenne | Faible | Formation, documentation, UX testing |
| Migration données existantes | Faible | Élevé | Script migration, backup, rollback plan |

### Risques Opérationnels

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Retard livraison | Faible | Moyen | Buffer temps dans planning, priorisation |
| Bugs en production | Faible | Élevé | Tests approfondis, déploiement progressif |

---

## 9. Plan de Déploiement

### 9.1 Pré-déploiement

1. **Backup**
   - Backup MongoDB complet
   - Backup configuration existante

2. **Tests**
   - Tests d'intégration complets
   - Tests de performance
   - Tests de sécurité

3. **Documentation**
   - Documentation technique
   - Documentation utilisateur
   - Guide de déploiement

### 9.2 Stratégie de Déploiement

#### Déploiement par Sprint (Recommandé)

**Sprint 2.1 - Packaging/Colisage**
- Déploiement isolé, impact minimal
- Validation avec équipe logistique
- Pas d'impact sur modules existants

**Sprint 2.2 - Notifications**
- Déploiement progressif (10% → 50% → 100%)
- Monitoring intensif
- Rollback rapide si problèmes

**Sprint 2.3 - Logistique/Transport**
- Déploiement après validation Sprint 2.1
- Formation chauffeurs
- Période de test en parallèle

**Sprint 2.4 - Comptabilité Avancée**
- Déploiement en fin d'exercice comptable
- Validation avec comptable
- Backup avant activation écritures automatiques

### 9.3 Post-déploiement

1. **Monitoring**
   - Surveillance métriques Prometheus
   - Alertes configurées
   - Logs audit activés

2. **Support**
   - Support technique dédié (1 semaine)
   - Hotline utilisateurs
   - Documentation accessible

3. **Feedback**
   - Collecte feedback utilisateurs
   - Ajustements rapides
   - Plan améliorations

### 9.4 Rollback Plan

- **Condition** : Critique majeur, impact business
- **Action** : Revert vers version précédente
- **Délai** : < 30 minutes
- **Validation** : Tests de régression

---

## 10. Conclusion

Phase 2 représente une extension significative des fonctionnalités de l'ERP avec 4 modules critiques pour les opérations logistiques et financières. Le cadrage proposé fournit une base solide pour le développement avec :

- Architecture fonctionnelle claire et cohérente
- Stack technique éprouvé et maintenable
- Modèle de données complet et normalisé
- Dépendances bien identifiées
- Roadmap détaillée et réaliste
- Estimation de charge transparente
- Analyse des risques proactive
- Plan de déploiement sécurisé

La durée totale estimée est de **11 semaines** pour une charge de **55 jours-homme** et un coût estimatif de **22,000€**.

Une fois ce cadrage validé, les développements pourront démarrer selon la roadmap proposée.

---

## Annexes

### A. Référentiel SYSCOHADA (Extrait)
- Classe 4 : Comptes de tiers (411 Clients, 401 Fournisseurs)
- Classe 7 : Comptes de produits (701 Ventes, 706 Services)
- Classe 6 : Comptes de charges (601 Achats, 623 Personnel)

### B. Templates Email (Exemples)
- Confirmation de commande
- Notification d'expédition
- Rappel de paiement
- Facture envoyée

### C. KPIs Logistiques
- Taux de livraison à temps
- Coût moyen par livraison
- Performance chauffeurs
- Utilisation véhicules

### D. Plan de Tests
- Tests unitaires (backend)
- Tests intégration (frontend)
- Tests E2E (scenarios utilisateur)
- Tests performance (load testing)
