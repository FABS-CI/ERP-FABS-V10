"""
Script de Test Automatisé - Frontend ERP FABS V7

Ce script vérifie la configuration du frontend et détecte les problèmes potentiels.

Usage:
    python scripts/test_frontend.py
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

class FrontendTester:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.frontend_dir = self.project_root / "frontend"
        self.test_results = []
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Enregistre le résultat d'un test"""
        self.test_results.append({
            "test": test_name,
            "status": status,
            "details": details
        })
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name} - {status}")
        if details:
            print(f"   {details}")
    
    def test_package_json(self):
        """Test du fichier package.json"""
        package_json_path = self.frontend_dir / "package.json"
        if not package_json_path.exists():
            self.log_test("package.json exists", "FAIL", "File not found")
            return False
        
        with open(package_json_path, 'r') as f:
            package_json = json.load(f)
        
        # Vérifier les dépendances critiques
        required_deps = ["react", "react-dom", "react-router-dom", "axios"]
        missing_deps = []
        for dep in required_deps:
            if dep not in package_json.get("dependencies", {}):
                missing_deps.append(dep)
        
        if missing_deps:
            self.log_test("package.json dependencies", "FAIL", f"Missing: {', '.join(missing_deps)}")
            return False
        else:
            self.log_test("package.json dependencies", "PASS", f"All required deps present")
            return True
    
    def test_env_file(self):
        """Test du fichier .env"""
        env_file = self.frontend_dir / ".env"
        if not env_file.exists():
            self.log_test(".env file", "WARN", "File not found - will use defaults")
            return True
        
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        if "REACT_APP_API_BASE_URL" in env_content:
            self.log_test(".env API URL", "PASS", "REACT_APP_API_BASE_URL configured")
            return True
        else:
            self.log_test(".env API URL", "FAIL", "REACT_APP_API_BASE_URL not configured")
            return False
    
    def test_app_js(self):
        """Test du fichier App.js"""
        app_js_path = self.frontend_dir / "src" / "App.js"
        if not app_js_path.exists():
            self.log_test("App.js exists", "FAIL", "File not found")
            return False
        
        with open(app_js_path, 'r') as f:
            app_js_content = f.read()
        
        # Vérifier que la route ProduitsInventaire est présente
        if "ProduitsInventaire" in app_js_content:
            self.log_test("App.js route ProduitsInventaire", "PASS", "Route configured")
            return True
        else:
            self.log_test("App.js route ProduitsInventaire", "FAIL", "Route not configured")
            return False
    
    def test_services_directory(self):
        """Test du répertoire services"""
        services_dir = self.frontend_dir / "src" / "services"
        if not services_dir.exists():
            self.log_test("services directory", "FAIL", "Directory not found")
            return False
        
        # Vérifier les fichiers de services critiques
        required_services = ["fournisseursApi.js", "approvisionnementApi.js"]
        missing_services = []
        for service in required_services:
            if not (services_dir / service).exists():
                missing_services.append(service)
        
        if missing_services:
            self.log_test("services files", "FAIL", f"Missing: {', '.join(missing_services)}")
            return False
        else:
            self.log_test("services files", "PASS", "All required services present")
            return True
    
    def test_pages_directory(self):
        """Test du répertoire pages"""
        pages_dir = self.frontend_dir / "src" / "pages"
        if not pages_dir.exists():
            self.log_test("pages directory", "FAIL", "Directory not found")
            return False
        
        # Vérifier les fichiers de pages critiques
        required_pages = ["ProduitsInventaire.jsx"]
        missing_pages = []
        for page in required_pages:
            if not (pages_dir / page).exists():
                missing_pages.append(page)
        
        if missing_pages:
            self.log_test("pages files", "FAIL", f"Missing: {', '.join(missing_pages)}")
            return False
        else:
            self.log_test("pages files", "PASS", "All required pages present")
            return True
    
    def test_components_directory(self):
        """Test du répertoire components"""
        components_dir = self.frontend_dir / "src" / "components"
        if not components_dir.exists():
            self.log_test("components directory", "FAIL", "Directory not found")
            return False
        
        # Compter le nombre de composants
        component_files = list(components_dir.glob("*.jsx")) + list(components_dir.glob("*.js"))
        self.log_test("components directory", "PASS", f"{len(component_files)} components found")
        return True
    
    def test_index_js(self):
        """Test du fichier index.js"""
        index_js_path = self.frontend_dir / "src" / "index.js"
        if not index_js_path.exists():
            self.log_test("index.js exists", "FAIL", "File not found")
            return False
        
        with open(index_js_path, 'r') as f:
            index_js_content = f.read()
        
        if "ReactDOM.createRoot" in index_js_content or "ReactDOM.render" in index_js_content:
            self.log_test("index.js render", "PASS", "ReactDOM render found")
            return True
        else:
            self.log_test("index.js render", "FAIL", "ReactDOM render not found")
            return False
    
    def run_all_tests(self):
        """Exécute tous les tests"""
        print("=" * 60)
        print("TEST AUTOMATISÉ - FRONTEND ERP FABS V7")
        print(f"Frontend Directory: {self.frontend_dir}")
        print("=" * 60)
        print()
        
        # Test 1: Configuration
        print("1. Tests de Configuration")
        self.test_package_json()
        self.test_env_file()
        print()
        
        # Test 2: Structure
        print("2. Tests de Structure")
        self.test_app_js()
        self.test_index_js()
        self.test_services_directory()
        self.test_pages_directory()
        self.test_components_directory()
        print()
        
        # Generate Report
        self.generate_report()
    
    def generate_report(self):
        """Génère le rapport de test"""
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        warned = sum(1 for r in self.test_results if r["status"] == "WARN")
        total = len(self.test_results)
        
        print("=" * 60)
        print("RAPPORT DE TEST FRONTEND")
        print("=" * 60)
        print(f"Tests exécutés: {total}")
        print(f"Tests réussis: {passed} ✅")
        print(f"Tests échoués: {failed} ❌")
        print(f"Tests avertissements: {warned} ⚠️")
        print(f"Taux de réussite: {(passed/total*100):.1f}%")
        print("=" * 60)
        
        # Save report to JSON
        report = {
            "frontend_directory": str(self.frontend_dir),
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "warned": warned,
            "success_rate": passed/total*100,
            "results": self.test_results
        }
        
        with open("test_frontend_results.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"Rapport sauvegardé: test_frontend_results.json")
        print()

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    tester = FrontendTester(str(project_root))
    tester.run_all_tests()
