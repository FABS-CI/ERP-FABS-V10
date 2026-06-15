# Scripts de Seed FABS-CI

Scripts d'initialisation des données officielles EDITIONS FABS-CI (2026-2027).

## Utilisateurs (8 comptes officiels)

```bash
cd /app && python -m backend.scripts.seed_utilisateurs_fabs
# Reset des mots de passe (force tous les comptes à Fabs@2026)
cd /app && python -m backend.scripts.seed_utilisateurs_fabs --reset-password
```

**Liste des comptes** (mot de passe initial : `Fabs@2026`) :

| Nom complet              | Email                                     | Rôle                     |
|--------------------------|-------------------------------------------|--------------------------|
| AKE APPIA YVES DORIS     | pissken@editionsfabsci.com                | super_admin              |
| ALI MAMIN                | ali.mamin@editionsfabsci.com              | directeur_general        |
| DETY MICHEL              | detymichel@editionsfabsci.com             | directeur_commercial     |
| NATACHA KOFFI            | natachakoffi@editionsfabsci.com           | comptable                |
| NIANGORAN GEOGIE         | niangorangeorgie@editionsfabsci.com       | gestionnaire_stock       |
| JOACHIN                  | joachin@editionsfabsci.com                | responsable_magasinier   |
| MME AHOMAN DADJE         | dadjelarissa@editionsfabsci.com           | secretariat              |
| YAKE BEN                 | yakeben@editionsfabsci.com                | service_logistique       |

## Articles (59 produits officiels)

```bash
cd /app && python -m backend.scripts.seed_articles_fabs
```

Catégories utilisées :
- `primaire` — MON CAHIER (CP1, CP2, CE1, CE2, CM1, CM2, CEPE)
- `premier_cycle` — Éducation musicale + Arts plastiques + Mémos/Tests BEPC
- `second_cycle` — Mémos/Tests BAC
- `litterature` — Romans
