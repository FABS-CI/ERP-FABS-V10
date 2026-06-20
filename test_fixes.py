#!/usr/bin/env python3
import asyncio
import httpx
from datetime import datetime

API_BASE = "http://localhost:8000/api"

async def test_fixes():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("\n" + "="*70)
        print("TESTING FIX #2: POST /api/clients (with valid type)")
        print("="*70 + "\n")
        
        # Login super admin
        resp = await client.post(f"{API_BASE}/auth/login", json={
            "email": "pissken@editionsfabsci.com",
            "password": "Admin@2025"
        })
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test with valid client type
        client_data = {
            "nom_client": f"Client Test {datetime.now().timestamp()}",
            "categorie": "librairie",  # Valid enum value
            "ville": "Abidjan",
            "telephone": "0000000001",
            "email": f"test_{datetime.now().timestamp()}@test.com",
            "adresse": "123 Rue Test"
        }
        
        resp = await client.post(f"{API_BASE}/clients", json=client_data, headers=headers)
        print(f"POST /api/clients (with aliases nom_client + categorie): {resp.status_code}")
        if resp.status_code in (200, 201):
            print("✅ Client created successfully with field aliases!")
            client_obj = resp.json()
            print(f"   Client ID: {client_obj.get('client_id')}")
            print(f"   Name: {client_obj.get('nom')}")
            print(f"   Type: {client_obj.get('type_client')}\n")
        else:
            print(f"❌ Error: {resp.text}\n")

asyncio.run(test_fixes())
