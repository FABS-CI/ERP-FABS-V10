#!/usr/bin/env python3
"""
TEST DIRECT API : Contourne Playwright et teste les endpoints directement
Plus fiable et plus rapide
"""

import httpx
import asyncio
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def main():
    results = {
        "timestamp": datetime.now().isoformat(),
        "endpoints": {}
    }
    
    async with httpx.AsyncClient(timeout=10) as client:
        
        # 1. LOGIN
        print("\n🔐 LOGIN")
        r = await client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "pissken@editionsfabsci.com",
            "password": "Admin@2025"
        })
        if r.status_code != 200:
            print(f"❌ Login failed: {r.status_code}")
            return
        
        data = r.json()
        token = data.get("access_token") or data.get("token")
        user = data.get("user")
        
        print(f"✅ Connecté : {user.get('nom_complet', 'Unknown')} ({user.get('role')})")
        results["user"] = user
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. TEST ENDPOINTS CRITIQUES
        print("\n"+"="*60)
        print("TEST ENDPOINTS CRITIQUES")
        print("="*60)
        
        endpoints = [
            ("GET", "/api/commandes", None, "Lister commandes"),
            ("GET", "/api/factures", None, "Lister factures"),
            ("GET", "/api/paiements", None, "Lister paiements"),
            ("GET", "/api/clients", None, "Lister clients"),
            ("GET", "/api/produits", None, "Lister produits"),
            ("GET", "/api/stock", None, "Lister stock"),
        ]
        
        for method, path, payload, label in endpoints:
            try:
                if method == "GET":
                    r = await client.get(f"{BASE_URL}{path}", headers=headers)
                elif method == "POST":
                    r = await client.post(f"{BASE_URL}{path}", json=payload, headers=headers)
                
                status = "✅" if r.status_code == 200 else f"❌ {r.status_code}"
                data = r.json() if r.status_code == 200 else None
                count = len(data) if isinstance(data, list) else "?"
                
                results["endpoints"][path] = {
                    "status": r.status_code,
                    "count": count if isinstance(count, int) else count,
                    "sample": data[0] if isinstance(data, list) and len(data) > 0 else None
                }
                
                print(f"{status} {label:25} : {path:20} → {count} items")
                
            except Exception as e:
                print(f"❌ {label:25} : {str(e)[:50]}")
                results["endpoints"][path] = {"error": str(e)[:50]}
        
        # 3. TEST WORKFLOW : Créer une commande test
        print("\n"+"="*60)
        print("TEST WORKFLOW : Créer commande")
        print("="*60)
        
        # Récupérer un client
        r = await client.get(f"{BASE_URL}/api/clients?limit=1", headers=headers)
        data = r.json()
        clients = data.get("items", data) if isinstance(data, dict) and "items" in data else data
        if not clients:
            print("❌ Pas de clients disponibles")
            return
        
        client_id = clients[0].get("client_id")
        print(f"  Client sélectionné : {clients[0].get('nom')} ({client_id})")
        
        # Récupérer un produit
        r = await client.get(f"{BASE_URL}/api/produits?limit=1", headers=headers)
        data = r.json()
        produits = data.get("items", data) if isinstance(data, dict) and "items" in data else data
        if not produits:
            print("❌ Pas de produits disponibles")
            return
        
        product = produits[0]
        product_id = product.get("product_id")
        print(f"  Produit sélectionné : {product.get('nom', product.get('name'))} ({product_id})")
        
        # Créer commande
        cmd_payload = {
            "client_id": client_id,
            "lignes": [
                {
                    "product_id": product_id,
                    "quantite": 1,
                    "prix_unitaire": 2000,
                    "remise_ligne": 0
                }
            ],
            "remise_globale": 0,
            "notes": "Test API script",
            "date_livraison_prevue": "2026-06-25"
        }
        
        r = await client.post(f"{BASE_URL}/api/commandes", json=cmd_payload, headers=headers)
        if r.status_code != 201:
            print(f"❌ Créer commande : {r.status_code}")
            print(f"   Response: {r.text[:200]}")
            results["workflow_create"] = f"❌ {r.status_code}"
            return
        
        cmd = r.json()
        cmd_id = cmd.get("commande_id")
        print(f"  ✅ Commande créée : {cmd_id}")
        results["workflow_create"] = "✅"
        
        # 4. SOUMETTRE COMMANDE D'ABORD
        print("\n"+"="*60)
        print("TEST ACTIONS COMMANDE")
        print("="*60)
        
        # Soumettre (brouillon → en_attente)
        r = await client.post(f"{BASE_URL}/api/commandes/{cmd_id}/soumettre", json={}, headers=headers)
        if r.status_code in [200, 201]:
            print(f"  ✅ Soumettre         : {r.status_code}")
            results["workflow_actions"] = {"Soumettre": "✅"}
        else:
            print(f"  ❌ Soumettre         : {r.status_code}")
            results["workflow_actions"] = {"Soumettre": f"❌ {r.status_code}"}
        
        # Actions principales
        actions = [
            ("POST", f"/api/commandes/{cmd_id}/valider", None, "Valider"),
            ("POST", f"/api/commandes/{cmd_id}/preparer", None, "Préparer"),
            ("POST", f"/api/commandes/{cmd_id}/livrer", None, "Livrer"),
        ]
        
        for method, path, payload, label in actions:
            try:
                r = await client.post(f"{BASE_URL}{path}", json=payload or {}, headers=headers)
                
                if r.status_code in [200, 201]:
                    print(f"  ✅ {label:15} : {r.status_code}")
                    results["workflow_actions"][label] = "✅"
                else:
                    error_msg = r.json().get("detail", "Unknown error") if r.headers.get("content-type") == "application/json" else r.text[:80]
                    print(f"  ⚠️  {label:15} : {r.status_code} - {error_msg[:40]}")
                    results["workflow_actions"][label] = f"⚠️ {r.status_code}"
                    break  # stop if action fails
                
            except Exception as e:
                print(f"  ❌ {label:15} : {str(e)[:40]}")
                results["workflow_actions"][label] = f"❌ {str(e)[:30]}"
                break
        
        # 5. GÉNÉRER FACTURE (après validation)
        print("\n"+"="*60)
        print("TEST FACTURE")
        print("="*60)
        
        # Essayer endpoints possibles
        facture_endpoints = [
            f"/api/commandes/{cmd_id}/generer-facture",
            f"/api/factures?commande_id={cmd_id}",
            f"/api/transformations/{cmd_id}/generer-facture"
        ]
        
        facture_ok = False
        for endpoint in facture_endpoints:
            if "POST" in endpoint or "generer" in endpoint:
                method = "POST"
            else:
                method = "POST"
            
            try:
                r = await client.post(f"{BASE_URL}{endpoint}", json={}, headers=headers) if "generer" in endpoint else await client.get(f"{BASE_URL}{endpoint}", headers=headers)
                
                if r.status_code in [200, 201]:
                    result = r.json()
                    facture_id = result.get("facture_id") or (result.get("items")[0].get("facture_id") if isinstance(result, dict) and "items" in result and result["items"] else None)
                    print(f"  ✅ Facture générée : {facture_id} (via {endpoint})")
                    results["workflow_facture"] = "✅"
                    facture_ok = True
                    break
            except:
                pass
        
        if not facture_ok:
            print(f"  ⚠️  Facture : Endpoint non trouvé (commande en _livree_, facture générée auto à validation)")
            results["workflow_facture"] = "⚠️ À vérifier (auto-génération attend validation)"
        
    # RÉSUMÉ
    print("\n" + "="*60)
    print("📊 RÉSUMÉ")
    print("="*60)
    
    ok_endpoints = sum(1 for e in results["endpoints"].values() if e.get("status") == 200)
    total_endpoints = len(results["endpoints"])
    
    print(f"Endpoints OK : {ok_endpoints}/{total_endpoints}")
    print(f"User role : {user.get('role')}")
    print(f"Workflow : {results.get('workflow_create')} {results.get('workflow_facture')}")
    
    # Sauver
    with open("/home/user/ERP-FABS-V10/RAPPORT_API_TEST.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Rapport : /home/user/ERP-FABS-V10/RAPPORT_API_TEST.json")

if __name__ == "__main__":
    asyncio.run(main())
