"""
Module Rapports — EDITIONS FABS-CI ERP
- Rapports de ventes avec filtres multiples
- Rapports de stock avec alertes
- Exports PDF
"""
from fastapi import APIRouter, HTTPException, Request, Header
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from collections import defaultdict
import logging

logger = logging.getLogger("fabsci")


def build_rapports_router(db, resolve_user):
    router = APIRouter(prefix="/rapports", tags=["Rapports"])
    
    # RBAC
    READ_ROLES = {"super_admin", "directeur_general", "comptable", "directeur_commercial"}
    
    async def check_read(request, authorization):
        u = await resolve_user(request, authorization)
        if u["role"] not in READ_ROLES:
            raise HTTPException(status_code=403, detail="Accès interdit")
        return u
    
    @router.get("/ventes")
    async def get_rapport_ventes(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        matiere: Optional[str] = None,
        ecole: Optional[str] = None,
        localite: Optional[str] = None,
        niveau_scolaire: Optional[str] = None,
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
    ):
        """
        Rapport de ventes avec filtres multiples.
        Retourne les données agrégées par matière, école, localité, niveau.
        """
        await check_read(request, authorization)
        
        # Construction du pipeline d'agrégation MongoDB
        # Étape 1 : Récupérer toutes les factures émises/payées
        match_stage = {
            "statut": {"$in": ["emise", "partiellement_payee", "payee"]},
            "type_facture": "facture"
        }
        
        if date_debut:
            match_stage["date_facture"] = {"$gte": date_debut}
        if date_fin:
            if "date_facture" in match_stage:
                match_stage["date_facture"]["$lte"] = date_fin
            else:
                match_stage["date_facture"] = {"$lte": date_fin}
        
        factures = await db.factures.find(match_stage, {"_id": 0}).to_list(1000)
        
        # Étape 2 : Pour chaque facture, récupérer les lignes
        results = []
        total_quantite = 0
        total_montant = 0
        
        for facture in factures:
            facture_id = facture["facture_id"]
            client_id = facture.get("client_id")
            
            # Récupérer le client
            client = await db.clients.find_one({"client_id": client_id}, {"_id": 0})
            if not client:
                continue
            
            # Vérifier les filtres client
            if ecole and client.get("nom_client", "").lower().find(ecole.lower()) == -1:
                continue
            if localite and client.get("localite", "").lower().find(localite.lower()) == -1:
                continue
            
            # Récupérer les lignes de facture
            lignes = await db.facture_lignes.find({"facture_id": facture_id}, {"_id": 0}).to_list(100)
            
            for ligne in lignes:
                produit_id = ligne.get("produit_id")
                produit = await db.produits.find_one({"product_id": produit_id}, {"_id": 0})
                
                if not produit:
                    continue
                
                # Appliquer les filtres produit
                if matiere:
                    # La matière peut être dans le titre ou auteur
                    titre_auteur = f"{produit.get('titre', '')} {produit.get('auteur', '')}".lower()
                    if matiere.lower() not in titre_auteur:
                        continue
                
                if niveau_scolaire and produit.get("niveau_scolaire", "").lower().find(niveau_scolaire.lower()) == -1:
                    continue
                
                # Calculer les montants
                quantite = ligne.get("quantite", 0)
                montant_ht = ligne.get("montant_ht", 0)
                
                # Ajouter au résultat
                results.append({
                    "matiere": produit.get("auteur", "Non spécifié"),  # Utiliser auteur comme proxy pour matière
                    "titre_produit": produit.get("titre", ""),
                    "ecole": client.get("nom_client", ""),
                    "localite": client.get("localite", "Non spécifiée"),
                    "niveau_scolaire": produit.get("niveau_scolaire", "Non spécifié"),
                    "quantite_vendue": quantite,
                    "montant_total": montant_ht,
                    "date_facture": facture.get("date_facture", ""),
                    "reference_facture": facture.get("reference", ""),
                })
                
                total_quantite += quantite
                total_montant += montant_ht
        
        # Agrégations pour les graphiques
        # Par matière
        ventes_par_matiere = defaultdict(lambda: {"quantite": 0, "montant": 0})
        for r in results:
            matiere = r["matiere"]
            ventes_par_matiere[matiere]["quantite"] += r["quantite_vendue"]
            ventes_par_matiere[matiere]["montant"] += r["montant_total"]
        
        # Par localité
        ventes_par_localite = defaultdict(lambda: {"quantite": 0, "montant": 0})
        for r in results:
            loc = r["localite"]
            ventes_par_localite[loc]["quantite"] += r["quantite_vendue"]
            ventes_par_localite[loc]["montant"] += r["montant_total"]
        
        # Par date (agrégation par mois)
        ventes_par_mois = defaultdict(lambda: {"quantite": 0, "montant": 0})
        for r in results:
            if r["date_facture"]:
                mois = r["date_facture"][:7]  # YYYY-MM
                ventes_par_mois[mois]["quantite"] += r["quantite_vendue"]
                ventes_par_mois[mois]["montant"] += r["montant_total"]
        
        return {
            "lignes": results,
            "total_quantite": total_quantite,
            "total_montant": total_montant,
            "nombre_lignes": len(results),
            "agregations": {
                "par_matiere": [
                    {"matiere": k, **v} for k, v in ventes_par_matiere.items()
                ],
                "par_localite": [
                    {"localite": k, **v} for k, v in ventes_par_localite.items()
                ],
                "par_mois": [
                    {"mois": k, **v} for k, v in sorted(ventes_par_mois.items())
                ],
            }
        }
    
    @router.get("/stock")
    async def get_rapport_stock(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        matiere: Optional[str] = None,
        niveau_scolaire: Optional[str] = None,
        alerte_uniquement: bool = False,
    ):
        """
        Rapport de stock avec alertes.
        """
        await check_read(request, authorization)
        
        # Récupérer tous les produits
        match_stage = {"actif": True}
        
        produits = await db.produits.find(match_stage, {"_id": 0}).to_list(1000)
        
        results = []
        total_stock_valeur = 0
        nb_alertes = 0
        
        for produit in produits:
            # Filtres
            if matiere:
                titre_auteur = f"{produit.get('titre', '')} {produit.get('auteur', '')}".lower()
                if matiere.lower() not in titre_auteur:
                    continue
            
            if niveau_scolaire and produit.get("niveau_scolaire", "").lower().find(niveau_scolaire.lower()) == -1:
                continue
            
            stock_actuel = produit.get("stock_actuel", 0)
            stock_minimum = produit.get("stock_minimum", 10)
            prix_vente = produit.get("prix_vente", 0)
            
            # Alerte si stock < minimum
            en_alerte = stock_actuel < stock_minimum
            
            if alerte_uniquement and not en_alerte:
                continue
            
            if en_alerte:
                nb_alertes += 1
            
            # Calculer la valeur du stock
            valeur_stock = stock_actuel * prix_vente
            total_stock_valeur += valeur_stock
            
            results.append({
                "reference": produit.get("reference", ""),
                "titre": produit.get("titre", ""),
                "auteur": produit.get("auteur", ""),
                "niveau_scolaire": produit.get("niveau_scolaire", ""),
                "categorie": produit.get("categorie", ""),
                "stock_actuel": stock_actuel,
                "stock_minimum": stock_minimum,
                "prix_vente": prix_vente,
                "valeur_stock": valeur_stock,
                "en_alerte": en_alerte,
                "statut_stock": "rupture" if stock_actuel == 0 else ("alerte" if en_alerte else "ok"),
            })
        
        # Récupérer l'historique des mouvements récents (30 derniers) avec $lookup
        pipeline_mouvements = [
            {"$sort": {"date_mouvement": -1}},
            {"$limit": 30},
            {"$lookup": {
                "from": "produits",
                "localField": "product_id",
                "foreignField": "product_id",
                "as": "produit_info"
            }},
            {"$addFields": {
                "titre_produit": {"$arrayElemAt": ["$produit_info.titre", 0]}
            }},
            {"$project": {
                "produit_info": 0,
                "_id": 0
            }}
        ]
        mouvements = await db.mouvements_stock.aggregate(pipeline_mouvements).to_list(30)
        
        return {
            "produits": results,
            "total_produits": len(results),
            "nb_alertes": nb_alertes,
            "valeur_stock_total": total_stock_valeur,
            "mouvements_recents": mouvements,
        }
    
    # ══════════════════════════════════════════════════════════════
    # EXPORT PDF — ÉTAT DE COMPTE CLIENTS
    # ══════════════════════════════════════════════════════════════
    @router.get("/etat-compte-clients")
    async def export_etat_compte_clients(
        request: Request,
        filtre: str = "tous",
        annee: Optional[str] = None,
        authorization: Optional[str] = Header(None),
    ):
        """
        Génère et renvoie le PDF État de Compte Clients.
        filtre: tous | paye | impaye
        annee: ex "2025" (optionnel, défaut = année courante)
        """
        from fastapi.responses import StreamingResponse
        from compte_client_pdf_generator import generate_etat_compte_clients_pdf

        await check_read(request, authorization)

        now_year = str(datetime.now().year)
        if annee is None:
            annee = now_year

        # ── 1. Récupérer toutes les factures (type facture uniquement) ──
        query_factures: Dict = {"type_facture": "facture"}

        # Filtre payé / impayé sur montant_restant
        if filtre == "paye":
            query_factures["montant_restant"] = 0
        elif filtre == "impaye":
            query_factures["montant_restant"] = {"$gt": 0}

        factures_raw = await db.factures.find(
            query_factures,
            {"_id": 0, "facture_id": 1, "reference": 1, "client_id": 1,
             "date_facture": 1, "date_livraison": 1,
             "montant_ht": 1, "montant_ttc": 1, "montant_tva": 1,
             "remise_globale": 1, "montant_regle": 1, "montant_restant": 1,
             "statut": 1}
        ).to_list(None)

        if not factures_raw:
            # Retourner un PDF vide avec message
            clients_data = []
            resume = {
                "nb_clients": 0, "nb_factures": 0,
                "total_vente": 0, "total_remise": 0,
                "total_ht": 0, "total_regle": 0, "total_solde": 0,
            }
            pdf_buf = generate_etat_compte_clients_pdf(
                clients_data, resume, filtre=filtre, annee=annee
            )
            filename = f"etat_compte_clients_{filtre}_{annee}.pdf"
            return StreamingResponse(
                pdf_buf,
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        # ── 2. Regrouper les factures par client_id ──
        from collections import defaultdict
        factures_par_client: Dict[str, List] = defaultdict(list)
        all_client_ids = set()
        for f in factures_raw:
            cid = f.get("client_id")
            if cid:
                factures_par_client[cid].append(f)
                all_client_ids.add(cid)

        # ── 3. Récupérer les clients concernés ──
        clients_raw = await db.clients.find(
            {"client_id": {"$in": list(all_client_ids)}},
            {"_id": 0, "client_id": 1, "nom": 1, "representant": 1,
             "telephone": 1, "type_client": 1, "region": 1, "ville": 1}
        ).to_list(None)

        clients_by_id: Dict[str, Dict] = {c["client_id"]: c for c in clients_raw}

        # ── 4. Construire clients_data + calcul résumé ──
        clients_data = []
        total_vente  = 0.0
        total_remise = 0.0
        total_ht     = 0.0
        total_regle  = 0.0
        total_solde  = 0.0
        total_facts  = 0

        # Trier par nom client
        sorted_client_ids = sorted(
            factures_par_client.keys(),
            key=lambda cid: (clients_by_id.get(cid, {}).get("nom") or "").lower()
        )

        for cid in sorted_client_ids:
            client_doc = clients_by_id.get(cid, {"client_id": cid, "nom": cid})
            # Normaliser ville/zone
            client_doc["ville"] = (
                client_doc.get("ville") or client_doc.get("region") or "—"
            )
            factures_client = factures_par_client[cid]

            # Trier les factures par date
            factures_client.sort(key=lambda x: str(x.get("date_facture") or ""))

            clients_data.append({
                "client": client_doc,
                "factures": factures_client,
            })

            for f in factures_client:
                total_vente  += float(f.get("montant_ttc") or 0)
                total_remise += float(f.get("remise_globale") or 0)
                total_ht     += float(f.get("montant_ht") or 0)
                total_regle  += float(f.get("montant_regle") or 0)
                total_solde  += float(f.get("montant_restant") or 0)
                total_facts  += 1

        resume = {
            "nb_clients":   len(clients_data),
            "nb_factures":  total_facts,
            "total_vente":  total_vente,
            "total_remise": total_remise,
            "total_ht":     total_ht,
            "total_regle":  total_regle,
            "total_solde":  total_solde,
        }

        # ── 5. Générer le PDF ──
        pdf_buf = generate_etat_compte_clients_pdf(
            clients_data, resume, filtre=filtre, annee=annee
        )

        filename = f"etat_compte_clients_{filtre}_{annee}.pdf"
        return StreamingResponse(
            pdf_buf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    return router
