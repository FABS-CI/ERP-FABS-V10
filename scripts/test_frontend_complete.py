"""
Script de Test Complet - Frontend ERP FABS V7

Ce script teste:
- Chargement App
- Routing React
- Pages principales
- Appels API
- Performance

Usage:
    python scripts/test_frontend_complete.py --frontend-url http://localhost:3000
"""

import requests
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

class FrontendTester:
    def __init__(self, frontend_url: str):
        self.frontend_url = frontend_url
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
    
    def request(self, url: str) -> requests.Response:
        """Effectue une requête HTTP"""
        start = time.time()
        try:
            response = requests.get(url, timeout=10)
            response_time = time.time() - start
            return response, response_time
        except Exception as e:
            response_time = time.time() - start
            return None, response_time
    
    def test_frontend_accessible(self):
        """Test si le frontend est accessible"""
        response, response_time = self.request(self.frontend_url)
        if response and response.status_code == 200:
            content = response.text
            if "<!DOCTYPE html>" in content or "<html" in content:
                self.log_test("Frontend Accessible", "PASS", response_time, f"HTML content received")
                return True
            else:
                self.log_test("Frontend Accessible", "FAIL", response_time, "No HTML content")
                return False
        else:
            self.log_test("Frontend Accessible", "FAIL", response_time, f"Status: {response.status_code if response else 'No response'}")
            return False
    
    def test_frontend_performance(self):
        """Test la performance du frontend (<2s)"""
        response, response_time = self.request(self.frontend_url)
        if response and response.status_code == 200:
            if response_time < 2.0:
                self.log_test("Frontend Performance", "PASS", response_time, f"Load time: {response_time:.3f}s (<2s)")
                return True
            else:
                self.log_test("Frontend Performance", "FAIL", response_time, f"Load time: {response_time:.3f}s (>=2s)")
                return False
        else:
            self.log_test("Frontend Performance", "FAIL", response_time, "No response")
            return False
    
    def test_react_bundle_loaded(self):
        """Test si le bundle React est chargé"""
        response, response_time = self.request(self.frontend_url)
        if response and response.status_code == 200:
            content = response.text
            if "react" in content.lower() or "app" in content.lower():
                self.log_test("React Bundle Loaded", "PASS", response_time, "React content detected")
                return True
            else:
                self.log_test("React Bundle Loaded", "FAIL", response_time, "No React content detected")
                return False
        else:
            self.log_test("React Bundle Loaded", "FAIL", response_time, "No response")
            return False
    
    def test_security_headers(self):
        """Test les headers de sécurité"""
        response, response_time = self.request(self.frontend_url)
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
    
    def test_static_files(self):
        """Test si les fichiers statiques sont accessibles"""
        static_files = [
            "/static/js/",
            "/static/css/",
            "/favicon.ico"
        ]
        
        all_accessible = True
        for file_path in static_files:
            url = f"{self.frontend_url}{file_path}"
            response, response_time = self.request(url)
            if not response or response.status_code != 200:
                all_accessible = False
        
        if all_accessible:
            self.log_test("Static Files Accessible", "PASS", 0, "All static files accessible")
            return True
        else:
            self.log_test("Static Files Accessible", "WARNING", 0, "Some static files not accessible")
            return False
    
    def test_frontend_structure(self):
        """Test la structure du frontend"""
        frontend_dir = Path(__file__).parent.parent / "frontend"
        
        critical_files = [
            "package.json",
            "src/index.js",
            "src/App.js",
            "src/config/api.js"
        ]
        
        critical_dirs = [
            "src/components",
            "src/pages",
            "src/services"
        ]
        
        all_files_exist = True
        missing_files = []
        
        for file_path in critical_files:
            full_path = frontend_dir / file_path
            if not full_path.exists():
                all_files_exist = False
                missing_files.append(file_path)
        
        all_dirs_exist = True
        missing_dirs = []
        
        for dir_path in critical_dirs:
            full_path = frontend_dir / dir_path
            if not full_path.exists():
                all_dirs_exist = False
                missing_dirs.append(dir_path)
        
        if all_files_exist and all_dirs_exist:
            self.log_test("Frontend Structure", "PASS", 0, "All critical files and directories present")
            return True
        else:
            details = []
            if missing_files:
                details.append(f"Missing files: {', '.join(missing_files)}")
            if missing_dirs:
                details.append(f"Missing directories: {', '.join(missing_dirs)}")
            self.log_test("Frontend Structure", "FAIL", 0, "; ".join(details))
            return False
    
    def test_dependencies(self):
        """Test les dépendances frontend"""
        package_json_path = Path(__file__).parent.parent / "frontend" / "package.json"
        
        if not package_json_path.exists():
            self.log_test("Dependencies", "FAIL", 0, "package.json not found")
            return False
        
        with open(package_json_path, 'r') as f:
            package_json = json.load(f)
        
        critical_dependencies = [
            "react",
            "react-router-dom",
            "axios"
        ]
        
        all_present = True
        missing_deps = []
        
        for dep in critical_dependencies:
            if dep not in package_json.get("dependencies", {}):
                all_present = False
                missing_deps.append(dep)
        
        if all_present:
            self.log_test("Dependencies", "PASS", 0, "All critical dependencies present")
            return True
        else:
            self.log_test("Dependencies", "FAIL", 0, f"Missing dependencies: {', '.join(missing_deps)}")
            return False
    
    def test_api_configuration(self):
        """Test la configuration API"""
        api_config_path = Path(__file__).parent.parent / "frontend" / "src" / "config" / "api.js"
        
        if not api_config_path.exists():
            self.log_test("API Configuration", "FAIL", 0, "api.js not found")
            return False
        
        with open(api_config_path, 'r') as f:
            content = f.read()
        
        if "baseURL" in content or "BASE_URL" in content:
            self.log_test("API Configuration", "PASS", 0, "API base URL configured")
            return True
        else:
            self.log_test("API Configuration", "WARNING", 0, "API base URL not found in configuration")
            return False
    
    def test_routing_configuration(self):
        """Test la configuration du routing"""
        app_js_path = Path(__file__).parent.parent / "frontend" / "src" / "App.js"
        
        if not app_js_path.exists():
            self.log_test("Routing Configuration", "FAIL", 0, "App.js not found")
            return False
        
        with open(app_js_path, 'r') as f:
            content = f.read()
        
        if "BrowserRouter" in content or "Routes" in content or "Route" in content:
            self.log_test("Routing Configuration", "PASS", 0, "React Router configured")
            return True
        else:
            self.log_test("Routing Configuration", "FAIL", 0, "React Router not configured")
            return False
    
    def run_all_tests(self):
        """Exécute tous les tests"""
        print("=" * 80)
        print("TEST AUTOMATISÉ - FRONTEND ERP FABS V7")
        print(f"Frontend URL: {self.frontend_url}")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()
        
        # Test 1: Structure et Configuration
        print("1. Tests Structure et Configuration")
        self.test_frontend_structure()
        self.test_dependencies()
        self.test_api_configuration()
        self.test_routing_configuration()
        print()
        
        # Test 2: Accessibilité
        print("2. Tests Accessibilité")
        self.test_frontend_accessible()
        self.test_react_bundle_loaded()
        self.test_static_files()
        print()
        
        # Test 3: Performance
        print("3. Tests Performance")
        self.test_frontend_performance()
        print()
        
        # Test 4: Sécurité
        print("4. Tests Sécurité")
        self.test_security_headers()
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
        print("RAPPORT DE TEST FRONTEND")
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
            "frontend_url": self.frontend_url,
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "warning": warning,
            "success_rate": passed/total*100,
            "total_time": total_time,
            "results": self.test_results
        }
        
        with open("test_frontend_complete_results.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"Rapport sauvegardé: test_frontend_complete_results.json")
        print()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_frontend_complete.py --frontend-url http://localhost:3000")
        sys.exit(1)
    
    frontend_url = None
    
    for i in range(1, len(sys.argv)):
        if sys.argv[i] == "--frontend-url" and i + 1 < len(sys.argv):
            frontend_url = sys.argv[i + 1]
    
    if not frontend_url:
        print("Error: --frontend-url is required")
        sys.exit(1)
    
    tester = FrontendTester(frontend_url)
    tester.run_all_tests()
