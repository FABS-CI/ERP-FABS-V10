"""
Script de Test Performance et Sécurité - ERP FABS V7

Ce script teste:
- Performance API (<500ms)
- Sécurité JWT (vérification réelle, PAS DE MOCK)
- Protection routes
- Headers sécurisés
- CORS correct

Usage:
    python scripts/test_performance_security.py --base-url http://localhost:8001/api
"""

import requests
import json
import sys
import time
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Any

class PerformanceSecurityTester:
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
            else:
                raise ValueError(f"Method {method} not supported")
            
            response_time = time.time() - start
            return response, response_time
        except Exception as e:
            response_time = time.time() - start
            return None, response_time
    
    def test_api_performance(self, endpoint: str, method: str = "GET", data: dict = None):
        """Test la performance d'un endpoint API (<500ms)"""
        response, response_time = self.request(method, endpoint, data)
        
        if response and response.status_code == 200:
            if response_time < 0.5:
                self.log_test(f"Performance - {method} {endpoint}", "PASS", response_time, f"Response time: {response_time*1000:.0f}ms (<500ms)")
                return True
            else:
                self.log_test(f"Performance - {method} {endpoint}", "FAIL", response_time, f"Response time: {response_time*1000:.0f}ms (>=500ms)")
                return False
        else:
            self.log_test(f"Performance - {method} {endpoint}", "FAIL", response_time, f"Status: {response.status_code if response else 'No response'}")
            return False
    
    def test_security_headers(self):
        """Test les headers de sécurité"""
        response, response_time = self.request("GET", "/health")
        if response and response.status_code == 200:
            headers = response.headers
            
            security_headers = {
                "X-Content-Type-Options": headers.get("X-Content-Type-Options"),
                "X-Frame-Options": headers.get("X-Frame-Options"),
                "X-XSS-Protection": headers.get("X-XSS-Protection"),
                "Strict-Transport-Security": headers.get("Strict-Transport-Security"),
                "Content-Security-Policy": headers.get("Content-Security-Policy")
            }
            
            missing_headers = [k for k, v in security_headers.items() if not v]
            
            if not missing_headers:
                self.log_test("Security Headers", "PASS", response_time, "All security headers present")
                return True
            else:
                self.log_test("Security Headers", "WARNING", response_time, f"Missing headers: {', '.join(missing_headers)}")
                return False
        else:
            self.log_test("Security Headers", "FAIL", response_time, "No response")
            return False
    
    def test_jwt_verification_real(self, email: str = "pissken@editionsfabsci.com", password: str = "Admin@2024"):
        """Test que la vérification JWT est réelle (PAS DE MOCK)"""
        # Login pour obtenir un token
        data = {"email": email, "password": password}
        response, response_time = self.request("POST", "/auth/login", data)
        
        if not response or response.status_code != 200:
            self.log_test("JWT Verification - Real Check", "SKIP", response_time, "Login failed - cannot test JWT")
            return False
        
        token_data = response.json()
        token = token_data.get("access_token")
        self.token = token
        
        if not token:
            self.log_test("JWT Verification - Real Check", "FAIL", response_time, "No token received")
            return False
        
        # Vérifier que le token a une structure valide
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            if not payload.get("user_id"):
                self.log_test("JWT Verification - Real Check", "FAIL", 0, "Token missing user_id")
                return False
        except Exception as e:
            self.log_test("JWT Verification - Real Check", "FAIL", 0, f"Invalid token structure: {str(e)}")
            return False
        
        # Tester avec un token modifié (doit être rejeté)
        modified_token = token[:-5] + "12345"
        headers = {"Authorization": f"Bearer {modified_token}"}
        response, response_time = self.request("GET", "/dashboard", headers=headers)
        
        if response and response.status_code == 401:
            self.log_test("JWT Verification - Real Check", "PASS", response_time, "Modified token correctly rejected")
            return True
        else:
            self.log_test("JWT Verification - Real Check", "FAIL", response_time, f"Modified token not rejected (status: {response.status_code if response else 'No response'})")
            return False
    
    def test_route_protection(self):
        """Test que les routes sont protégées"""
        # Test route sans token
        temp_token = self.token
        self.token = None
        
        protected_routes = [
            "/dashboard",
            "/clients",
            "/produits",
            "/fournisseurs",
            "/factures"
        ]
        
        all_protected = True
        for route in protected_routes:
            response, response_time = self.request("GET", route)
            if response and response.status_code != 401:
                all_protected = False
                self.log_test(f"Route Protection - {route}", "FAIL", response_time, f"Route not protected (status: {response.status_code})")
        
        self.token = temp_token
        
        if all_protected:
            self.log_test("Route Protection", "PASS", 0, "All protected routes require authentication")
            return True
        else:
            return False
    
    def test_cors_configuration(self):
        """Test la configuration CORS"""
        headers = {"Origin": "http://localhost:3000"}
        response, response_time = self.request("GET", "/health", headers=headers)
        
        if response:
            cors_headers = response.headers.get("Access-Control-Allow-Origin")
            if cors_headers:
                self.log_test("CORS Configuration", "PASS", response_time, f"CORS configured: {cors_headers}")
                return True
            else:
                self.log_test("CORS Configuration", "WARNING", response_time, "No CORS headers found")
                return False
        else:
            self.log_test("CORS Configuration", "FAIL", response_time, "No response")
            return False
    
    def test_rate_limiting(self):
        """Test le rate limiting"""
        # Faire plusieurs requêtes rapides
        responses = []
        for i in range(10):
            response, response_time = self.request("GET", "/health")
            if response:
                responses.append(response.status_code)
        
        # Vérifier si on reçoit un 429 (Too Many Requests)
        if 429 in responses:
            self.log_test("Rate Limiting", "PASS", 0, "Rate limiting active (429 received)")
            return True
        else:
            self.log_test("Rate Limiting", "WARNING", 0, "Rate limiting not detected")
            return False
    
    def test_sql_injection_protection(self):
        """Test la protection contre SQL injection"""
        malicious_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "<script>alert('xss')</script>"
        ]
        
        all_protected = True
        for payload in malicious_payloads:
            data = {"email": payload, "password": "test"}
            response, response_time = self.request("POST", "/auth/login", data)
            
            # Ne devrait pas réussir avec des payloads malveillants
            if response and response.status_code == 200:
                all_protected = False
                self.log_test("SQL Injection Protection", "FAIL", response_time, f"Malicious payload accepted: {payload[:20]}")
        
        if all_protected:
            self.log_test("SQL Injection Protection", "PASS", 0, "All malicious payloads rejected")
            return True
        else:
            return False
    
    def test_input_validation(self):
        """Test la validation des entrées"""
        # Tester avec des données invalides
        invalid_data = {
            "email": "invalid-email",
            "password": "123"  # Mot de passe trop court
        }
        
        response, response_time = self.request("POST", "/auth/login", invalid_data)
        
        if response and response.status_code == 400 or response.status_code == 422:
            self.log_test("Input Validation", "PASS", response_time, "Invalid data correctly rejected")
            return True
        else:
            self.log_test("Input Validation", "WARNING", response_time, f"Invalid data not rejected (status: {response.status_code if response else 'No response'})")
            return False
    
    def run_all_tests(self, email: str = "pissken@editionsfabsci.com", password: str = "Admin@2024"):
        """Exécute tous les tests"""
        print("=" * 80)
        print("TEST AUTOMATISÉ - PERFORMANCE ET SÉCURITÉ ERP FABS V7")
        print(f"Base URL: {self.base_url}")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()
        
        # Test 1: Performance
        print("1. Tests Performance API (<500ms)")
        self.test_api_performance("/health")
        self.test_api_performance("/dashboard")
        self.test_api_performance("/clients")
        self.test_api_performance("/produits")
        print()
        
        # Test 2: Sécurité Headers
        print("2. Tests Sécurité Headers")
        self.test_security_headers()
        print()
        
        # Test 3: JWT Verification
        print("3. Tests JWT Verification (PAS DE MOCK)")
        self.test_jwt_verification_real(email, password)
        print()
        
        # Test 4: Route Protection
        print("4. Tests Protection Routes")
        self.test_route_protection()
        print()
        
        # Test 5: CORS
        print("5. Tests CORS")
        self.test_cors_configuration()
        print()
        
        # Test 6: Rate Limiting
        print("6. Tests Rate Limiting")
        self.test_rate_limiting()
        print()
        
        # Test 7: Protection Injection
        print("7. Tests Protection Injection")
        self.test_sql_injection_protection()
        self.test_input_validation()
        print()
        
        # Generate Report
        self.generate_report()
    
    def generate_report(self):
        """Génère le rapport de test"""
        total_time = time.time() - self.start_time
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        warning = sum(1 for r in self.test_results if r["status"] == "WARNING")
        total = len(self.test_results)
        
        print("=" * 80)
        print("RAPPORT DE TEST PERFORMANCE ET SÉCURITÉ")
        print("=" * 80)
        print(f"Tests exécutés: {total}")
        print(f"Tests réussis: {passed} ✅")
        print(f"Tests échoués: {failed} ❌")
        print(f"Tests avertissements: {warning} ⚠️")
        print(f"Taux de réussite: {(passed/total*100):.1f}%")
        print(f"Temps total: {total_time:.2f}s")
        print("=" * 80)
        
        # Save report to JSON
        report = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "warning": warning,
            "success_rate": passed/total*100,
            "total_time": total_time,
            "results": self.test_results
        }
        
        with open("test_performance_security_results.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"Rapport sauvegardé: test_performance_security_results.json")
        print()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_performance_security.py --base-url http://localhost:8001/api [--email EMAIL] [--password PASSWORD]")
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
    
    tester = PerformanceSecurityTester(base_url)
    tester.run_all_tests(email, password)
