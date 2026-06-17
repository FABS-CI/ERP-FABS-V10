#!/usr/bin/env python3
"""
Création de tous les index MongoDB nécessaires pour la production.
TYPE A — SÛR : aucun impact métier.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("create_indexes")

async def create_all_indexes():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["fabsci_erp"]
    
    created = 0
    errors = 0
    
    async def idx(col, fields, unique=False, name=None, sparse=False):
        nonlocal created, errors
        try:
            opts = {}
            if name:
                opts["name"] = name
            if unique:
                opts["unique"] = True
            if sparse:
                opts["sparse"] = True
            await db[col].create_index(fields, **opts)
            log.info(f"✅ {col}: index {fields}")
            created += 1
        except Exception as e:
            log.warning(f"⚠️  {col} {fields}: {e}")
            errors += 1

    log.info("=== CRÉATION DES INDEX MONGODB ===")

    # COMMANDES
    await idx("commandes", [("commande_id", 1)], unique=True, name="unique_commande_id")
    await idx("commandes", [("client_id", 1)], name="idx_commandes_client")
    await idx("commandes", [("statut", 1)], name="idx_commandes_statut")
    await idx("commandes", [("created_at", -1)], name="idx_commandes_created_at")
    await idx("commandes", [("client_id", 1), ("statut", 1)], name="idx_commandes_client_statut")

    # COMMANDE_LIGNES
    await idx("commande_lignes", [("commande_id", 1)], name="idx_cmd_lignes_commande")
    await idx("commande_lignes", [("produit_id", 1)], name="idx_cmd_lignes_produit")

    # FACTURES
    await idx("factures", [("facture_id", 1)], unique=True, name="unique_facture_id")
    await idx("factures", [("client_id", 1)], name="idx_factures_client")
    await idx("factures", [("statut", 1)], name="idx_factures_statut")
    await idx("factures", [("commande_id", 1)], sparse=True, name="idx_factures_commande")
    await idx("factures", [("date_facture", -1)], name="idx_factures_date")
    await idx("factures", [("client_id", 1), ("statut", 1)], name="idx_factures_client_statut")

    # FACTURE_LIGNES
    await idx("facture_lignes", [("produit_id", 1)], name="idx_fac_lignes_produit")
    await idx("facture_lignes", [("facture_id", 1), ("produit_id", 1)], name="idx_fac_lignes_fac_prod")

    # PAIEMENTS
    await idx("paiements", [("paiement_id", 1)], unique=True, name="unique_paiement_id")
    await idx("paiements", [("client_id", 1)], name="idx_paiements_client")
    await idx("paiements", [("date_paiement", -1)], name="idx_paiements_date")

    # AFFECTATIONS PAIEMENT
    await idx("affectations_paiement", [("paiement_id", 1)], name="idx_affec_paiement")
    await idx("affectations_paiement", [("facture_id", 1)], name="idx_affec_facture")

    # CLIENTS
    await idx("clients", [("client_id", 1)], unique=True, name="unique_client_id")
    await idx("clients", [("nom", 1)], name="idx_clients_nom")
    await idx("clients", [("ville", 1)], sparse=True, name="idx_clients_ville")
    await idx("clients", [("type_client", 1)], name="idx_clients_type")
    await idx("clients", [("reference", 1)], unique=True, sparse=True, name="unique_clients_ref")
    # Index texte pour la recherche
    try:
        await db["clients"].create_index(
            [("nom", "text"), ("reference", "text"), ("telephone", "text")],
            name="idx_clients_text"
        )
        log.info("✅ clients: index texte")
        created += 1
    except Exception as e:
        log.warning(f"⚠️  clients texte: {e}")

    # PRODUITS
    await idx("produits", [("product_id", 1)], unique=True, name="unique_product_id")
    await idx("produits", [("categorie", 1)], name="idx_produits_categorie")
    await idx("produits", [("matiere", 1)], sparse=True, name="idx_produits_matiere")
    await idx("produits", [("actif", 1)], name="idx_produits_actif")
    await idx("produits", [("a_completer", 1)], sparse=True, name="idx_produits_a_completer")
    # Index texte pour recherche produits
    try:
        await db["produits"].create_index(
            [("titre", "text"), ("reference", "text"), ("isbn", "text")],
            name="idx_produits_text"
        )
        log.info("✅ produits: index texte")
        created += 1
    except Exception as e:
        log.warning(f"⚠️  produits texte: {e}")

    # BONS_LIVRAISON
    await idx("bons_livraison", [("bl_id", 1)], unique=True, name="unique_bl_id")
    await idx("bons_livraison", [("commande_id", 1)], name="idx_bl_commande")
    await idx("bons_livraison", [("client_id", 1)], name="idx_bl_client")
    await idx("bons_livraison", [("statut", 1)], name="idx_bl_statut")

    # BL_LIGNES
    await idx("bl_lignes", [("bl_id", 1)], name="idx_bl_lignes_bl")
    await idx("bl_lignes", [("produit_id", 1)], name="idx_bl_lignes_produit")

    # BONS_RETOUR
    await idx("bons_retour", [("retour_id", 1)], unique=True, sparse=True, name="unique_retour_id")
    await idx("bons_retour", [("client_id", 1)], sparse=True, name="idx_retour_client")

    # PROFORMAS
    await idx("proformas", [("proforma_id", 1)], unique=True, name="unique_proforma_id")
    await idx("proformas", [("client_id", 1)], name="idx_proformas_client")

    # PROFORMA_LIGNES
    await idx("proforma_lignes", [("proforma_id", 1)], name="idx_proforma_lignes")

    # MOUVEMENTS_STOCK
    await idx("mouvements_stock", [("produit_id", 1), ("created_at", -1)], name="idx_stock_produit_date")
    await idx("mouvements_stock", [("type_mouvement", 1)], name="idx_stock_type")
    await idx("mouvements_stock", [("created_at", -1)], name="idx_stock_date")

    # USERS
    await idx("users", [("email", 1)], unique=True, name="unique_user_email")
    await idx("users", [("role", 1)], name="idx_users_role")
    await idx("users", [("actif", 1)], sparse=True, name="idx_users_actif")

    # REFRESH_TOKENS
    await idx("refresh_tokens", [("token", 1)], unique=True, name="unique_refresh_token")
    await idx("refresh_tokens", [("user_id", 1)], name="idx_refresh_user")
    await idx("refresh_tokens", [("expires_at", 1)], name="idx_refresh_expires",
    )  # TTL index pour nettoyage automatique
    try:
        await db["refresh_tokens"].create_index(
            [("expires_at", 1)],
            expireAfterSeconds=0,
            name="ttl_refresh_expires"
        )
        log.info("✅ refresh_tokens: TTL index")
        created += 1
    except Exception as e:
        log.warning(f"⚠️  refresh_tokens TTL: {e}")

    # AUDIT_LOGS
    await idx("audit_logs", [("user_id", 1)], name="idx_audit_user")
    await idx("audit_logs", [("timestamp", -1)], name="idx_audit_timestamp")
    await idx("audit_logs", [("action", 1)], name="idx_audit_action")
    await idx("audit_logs", [("resource_type", 1)], name="idx_audit_resource")
    # TTL: garder logs 1 an
    try:
        await db["audit_logs"].create_index(
            [("timestamp", 1)],
            expireAfterSeconds=365*24*3600,
            name="ttl_audit_1an"
        )
        log.info("✅ audit_logs: TTL 1 an")
        created += 1
    except Exception as e:
        log.warning(f"⚠️  audit_logs TTL: {e}")

    # NOTIFICATIONS
    await idx("notifications", [("user_id", 1), ("lu", 1)], name="idx_notif_user_lu")
    await idx("notifications", [("created_at", -1)], name="idx_notif_date")

    # EMPLOYES
    await idx("employes", [("employe_id", 1)], unique=True, sparse=True, name="unique_employe_id")
    await idx("employes", [("email", 1)], sparse=True, name="idx_employe_email")

    # FOURNISSEURS
    await idx("fournisseurs", [("fournisseur_id", 1)], unique=True, sparse=True, name="unique_fournisseur_id")

    # APPROVISIONNEMENTS
    await idx("approvisionnements", [("appro_id", 1)], unique=True, sparse=True, name="unique_appro_id")
    await idx("approvisionnements", [("fournisseur_id", 1)], sparse=True, name="idx_appro_fournisseur")

    # ORDRES COLISAGE
    await idx("ordres_colisage", [("ordre_id", 1)], unique=True, sparse=True, name="unique_ordre_colisage_id")

    # INVENTAIRES
    await idx("inventaires", [("inventaire_id", 1)], unique=True, sparse=True, name="unique_inventaire_id")

    log.info(f"\n=== RÉSULTAT: {created} index créés, {errors} erreurs/ignorés ===")
    client.close()
    return created, errors

if __name__ == "__main__":
    asyncio.run(create_all_indexes())
