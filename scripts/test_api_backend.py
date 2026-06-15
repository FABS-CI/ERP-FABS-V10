"""
Script de Test Automatisé - API Backend ERP FABS V7

Ce script teste toutes les routes API de l'ERP pour détecter les bugs et problèmes.

Usage:
    python scripts/test_api_backend.py --base-url http://localhost:8001/api
"""

import requests
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Any

class APITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token = None
        self.test_results = []
        self.start_time = time.time()
        
    def log_test(self, test_name: str, status: str, response_time: float, details: str = ""):
        """Enregistre le résultat d'un test"""
        self.test_results.append({
            "test": test_name,
            "status": status,
            "response_time": response_time,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name} - {status} ({response_time:.3f}s)")
        if details:
            print(f"   {details}")
    
    def request(self, method: str, endpoint: str, data: dict = None, headers: dict = None) -> requests.Response:
        """Effectue une requête HTTP"""
        url = f"{self.base_url}{endpoint}"
        req_headers = {"Content-Type": "application/json"}
        if self.token:
            req_headers["Authorization"] = f"Bearer {self.token}"
        if headers:
            req_headers.update(headers)
        
        start = time.time()
        try:
            if method == "GET":
                response = requests.get(url, headers=req_headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, headers=req_headers, timeout=10)
            elif method == "PATCH":
                response = requests.patch(url, json=data, headers=req_headers, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=req_headers, timeout=10)
            else:
                raise ValueError(f"Method {method} not supported")
            
            response_time = time.time() - start
            return response, response_time
        except Exception as e:
            response_time = time.time() - start
            return None, response_time
    
    def test_health_check(self):
        """Test du endpoint health"""
        response, response_time = self.request("GET", "/health")
        if response and response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                self.log_test("Health Check", "PASS", response_time, f"Status: {data.get('status')}")
                return True
            else:
                self.log_test("Health Check", "FAIL", response_time, f"Status: {data.get('status')}")
                return False
        else:
            self.log_test("Health Check", "FAIL", response_time, "No response or error")
            return False
    
    def test_login(self, email: str, password: str):
        """Test de connexion"""
        data = {"email": email, "password": password}
        response, response_time = self.request("POST", "/auth/login", data)
        if response and response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            if self.token:
                self.log_test("Login", "PASS", response_time, f"User: {email}")
                return True
            else:
                self.log_test("Login", "FAIL", response_time, "No token received")
                return False
        else:
            self.log_test("Login", "FAIL", response_time, f"Status: {response.status_code if response else 'No response'}")
            return False
    
    def test_dashboard(self):
        """Test du dashboard"""
        response, response_time = self.request("GET", "/dashboard")
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Dashboard", "PASS", response_time, f"KPIs received")
            return True
        else:
            self.log_test("Dashboard", "FAIL", response_time, f"Status: {response.status_code if response else 'No response'}")
            return False
    
    def test_clients_list(self):
        """Test de la liste des clients"""
        response, response_time = self.request("GET", "/clients")
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Clients List", "PASS", response_time, f"Count: {len(data.get('clients', []))}")
            return True
        else:
            self.log_test("Clients List", "FAIL", response_time, f"Status: {response.status_code if response else 'No response'}")
            return False
    
    def test_products_list(self):
        """Test de la liste des produits"""
        response, response_time = self.request("GET", "/produits")
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Products List", "PASS", response_time, f"Count: {len(data.get('produits', []))}")
            return True
        else:
            self.log_test("Products List", "FAIL", response_time, f"Status: {response.status_code if response else 'No response'}")
            return False
    
    def test_fournisseurs_list(self):
        """Test de la liste des fournisseurs"""
        response, response_time = self.request("GET", "/fournisseurs")
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Fournisseurs List", "PASS", response_time, f"Count: {len(data.get('fournisseurs', []))}")
            return True
        else:
            self.log_test("Fournisseurs List", "FAIL", response_time, f"Status: {response.status_code if response else 'No response'}")
            return False
    
    def test_approvisionnements_list(self):
        """Test de la liste des approvisionnements"""
        response, response_time = self.request("GET", "/approvisionnements")
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Approvisionnements List", "PASS", response_time, f"Count: {len(data.get('approvisionnements', []))}")
            return True
        else:
            self.log_test("Approvisionnements List", "FAIL", response_time, f"Status: {response.status_code if response else 'No response'}")
            return False
    
    def test_stock_movements(self):
        """Test des mouvements de stock"""
        response, response_time = self.request("GET", "/stock/mouvements")
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Stock Movements", "PASS", response_time, f"Count: {len(data.get('mouvements', []))}")
            return True
        else:
            self.log_test("Stock Movements", "FAIL", response_time, f"Status: {response.status_code if response else 'No response'}")
            return False
    
    def test_commandes_list(self):
        """Test de la liste des commandes"""
        response, response_time = self.request("GET", "/commandes")
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Commandes List", "PASS", response_time, f"Count: {len(data.get('commandes', []))}")
            return True
        else:
            self.log_test("Commandes List", "FAIL", response_time, f"Status: {response.status_code if response else 'No response'}")
            return False
    
    def test_factures_list(self):
        """Test de la liste des factures"""
        response, response_time = self.request("GET", "/factures")
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Factures List", "PASS", response_time, f"Count: {len(data.get('factures', []))}")
            return True
        else:
            self.log_test("Factures List", "FAIL", response_time, f"Status: {response.status_code if response else 'No response'}")
            return False
    
    def test_rh_dashboard(self):
        """Test du dashboard RH"""
        response, response_time = self.request("GET", "/rh/dashboard")
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("RH Dashboard", "PASS", response_time, f"KPIs received")
            return True
        else:
            self.log_test("RH Dashboard", "FAIL", response_time, f"Status: {response.status_code if response else 'No response'}")
            return False
    
    def test_rh_employes_list(self):
        """Test de la liste des employés"""
        response, response_time = self.request("GET", "/rh/employes")
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("RH Employes List", "PASS", response_time, f"Count: {len(data.get('employes', []))}")
            return True
        else:
            self.log_test("RH Employes List", "FAIL", response_time, f"Status: {response.status_code if response else 'No response'}")
            return False
    
    def run_all_tests(self, email: str = "pissken@editionsfabsci.com", password: str = "Admin@2024"):
        """Exécute tous les tests"""
        print("=" * 60)
        print("TEST AUTOMATISÉ - API BACKEND ERP FABS V7")
        print(f"Base URL: {self.base_url}")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()
        
        # Test 1: Health Check
        print("1. Tests de Connexion")
        self.test_health_check()
        print()
        
        # Test 2: Login
        print("2. Test d'Authentification")
        if not self.test_login(email, password):
            print("⚠️  Login failed - skipping authenticated tests")
            self.generate_report()
            return False
        print()
        
        # Test 3: Dashboard
        print("3. Test Dashboard")
        self.test_dashboard()
        print()
        
        # Test 4: Modules Principaux
        print("4. Tests Modules Principaux")
        self.test_clients_list()
        self.test_products_list()
        self.test_fournisseurs_list()
        self.test_approvisionnements_list()
        self.test_stock_movements()
        print()
        
        # Test 5: Modules Ventes
        print("5. Tests Modules Ventes")
        self.test_commandes_list()
        self.test_factures_list()
        print()
        
        # Test 6: Module RH
        print("6. Tests Module RH")
        self.test_rh_dashboard()
        self.test_rh_employes_list()
        print()
        
        # Generate Report
        self.generate_report()
        return True
    
    def generate_report(self):
        """Génère le rapport de test"""
        total_time = time.time() - self.start_time
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        total = len(self.test_results)
        
        print("=" * 60)
        print("RAPPORT DE TEST")
        print("=" * 60)
        print(f"Tests exécutés: {total}")
        print(f"Tests réussis: {passed} ✅")
        print(f"Tests échoués: {failed} ❌")
        print(f"Taux de réussite: {(passed/total*100):.1f}%")
        print(f"Temps total: {total_time:.2f}s")
        print("=" * 60)
        
        # Save report to JSON
        report = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "success_rate": passed/total*100,
            "total_time": total_time,
            "results": self.test_results
        }
        
        with open("test_results.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"Rapport sauvegardé: test_results.json")
        print()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_api_backend.py --base-url http://localhost:8001/api [--email EMAIL] [--password PASSWORD]")
        sys.exit(1)
    
    base_url = None
    email = "pissken@editionsfabsci.com"
    password = "Admin@2024"
    
    for i in range(1, len(sys.argv)):
        if sys.argv[i] == "--base-url" and i + 1 < len(sys.argv):
            base_url = sys.argv[i + 1]
        elif sys.argv[i] == "--email" and i + 1 < len(sys.argv):
            email = sys.argv[i + 1]
        elif sys.argv[i] == "--password" and i + 1 < len(sys.argv):
            password = sys.argv[i + 1]
    
    if not base_url:
        print("Error: --base-url is required")
        sys.exit(1)
    
    tester = APITester(base_url)
    tester.run_all_tests(email, password)
