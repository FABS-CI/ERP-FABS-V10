"""
Script d'Analyse Automatisée - ERP FABS V7

Ce script analyse tout le code du projet pour identifier:
- Bugs critiques
- Failles de sécurité
- Mauvaises pratiques
- Risques de crash

Usage:
    python scripts/analyze_code.py
"""

import os
import re
import ast
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

class CodeAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        self.issues = []
        
    def log_issue(self, severity: str, category: str, file: str, line: int, message: str):
        """Enregistre un problème détecté"""
        self.issues.append({
            "severity": severity,
            "category": category,
            "file": file,
            "line": line,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        severity_icon = "🔴" if severity == "CRITICAL" else "🟡" if severity == "WARNING" else "🔵"
        print(f"{severity_icon} [{severity}] {file}:{line} - {message}")
    
    def analyze_python_file(self, file_path: Path):
        """Analyse un fichier Python"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Recherche de patterns problématiques
            for i, line in enumerate(lines, 1):
                # Mock en production
                if "mock" in line.lower() and "production" not in line.lower():
                    if "TODO" in line or "FIXME" in line:
                        self.log_issue("CRITICAL", "Security", str(file_path.relative_to(self.project_root)), i, 
                                      "Mock detected in code - security risk")
                
                # TODO/FIXME non implémentés
                if "TODO" in line or "FIXME" in line:
                    if "JWT" in line or "auth" in line.lower() or "security" in line.lower():
                        self.log_issue("CRITICAL", "Security", str(file_path.relative_to(self.project_root)), i,
                                      f"Unimplemented security feature: {line.strip()}")
                
                # Hardcoded secrets
                if re.search(r'(password|secret|key)\s*=\s*["\']([^"\']+)["\']', line, re.IGNORECASE):
                    match = re.search(r'(password|secret|key)\s*=\s*["\']([^"\']+)["\']', line, re.IGNORECASE)
                    if match and match.group(2) not in ["CHANGE_THIS_IN_PRODUCTION", "admin123"]:
                        self.log_issue("CRITICAL", "Security", str(file_path.relative_to(self.project_root)), i,
                                      f"Hardcoded {match.group(1)} detected")
                
                # SQL injection patterns
                if re.search(r'(SELECT|INSERT|UPDATE|DELETE|DROP).*\+.*\w', line, re.IGNORECASE):
                    self.log_issue("CRITICAL", "Security", str(file_path.relative_to(self.project_root)), i,
                                  "Potential SQL injection pattern")
                
                # XSS patterns
                if "innerHTML" in line or "dangerouslySetInnerHTML" in line:
                    self.log_issue("WARNING", "Security", str(file_path.relative_to(self.project_root)), i,
                                  "Potential XSS vulnerability")
                
                # Exception handling vide
                if "except:" in line and "pass" in line:
                    self.log_issue("WARNING", "Code Quality", str(file_path.relative_to(self.project_root)), i,
                                  "Empty exception handling")
                
                # Debug prints
                if "print(" in line and "DEBUG" not in line:
                    self.log_issue("WARNING", "Code Quality", str(file_path.relative_to(self.project_root)), i,
                                  "Debug print statement found")
        
        except Exception as e:
            self.log_issue("ERROR", "Analysis", str(file_path.relative_to(self.project_root)), 0,
                          f"Failed to analyze file: {str(e)}")
    
    def analyze_javascript_file(self, file_path: Path):
        """Analyse un fichier JavaScript/JSX"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Hardcoded secrets
                if re.search(r'(password|secret|key|token)\s*[:=]\s*["\']([^"\']+)["\']', line, re.IGNORECASE):
                    match = re.search(r'(password|secret|key|token)\s*[:=]\s*["\']([^"\']+)["\']', line, re.IGNORECASE)
                    if match and match.group(2) not in ["CHANGE_THIS_IN_PRODUCTION", "admin123"]:
                        self.log_issue("CRITICAL", "Security", str(file_path.relative_to(self.project_root)), i,
                                      f"Hardcoded {match.group(1)} detected")
                
                # TODO/FIXME non implémentés
                if "TODO" in line or "FIXME" in line:
                    if "auth" in line.lower() or "security" in line.lower():
                        self.log_issue("WARNING", "Code Quality", str(file_path.relative_to(self.project_root)), i,
                                      f"Unimplemented feature: {line.strip()}")
                
                # XSS patterns
                if "innerHTML" in line or "dangerouslySetInnerHTML" in line:
                    self.log_issue("WARNING", "Security", str(file_path.relative_to(self.project_root)), i,
                                  "Potential XSS vulnerability")
                
                # Console.log en production
                if "console.log" in line:
                    self.log_issue("WARNING", "Code Quality", str(file_path.relative_to(self.project_root)), i,
                                  "Console.log statement found")
                
                # Eval usage
                if "eval(" in line:
                    self.log_issue("CRITICAL", "Security", str(file_path.relative_to(self.project_root)), i,
                                      "eval() usage - security risk")
        
        except Exception as e:
            self.log_issue("ERROR", "Analysis", str(file_path.relative_to(self.project_root)), 0,
                          f"Failed to analyze file: {str(e)}")
    
    def analyze_docker_compose(self):
        """Analyse docker-compose.yml"""
        docker_compose = self.project_root / "docker-compose.yml"
        if not docker_compose.exists():
            self.log_issue("CRITICAL", "Infrastructure", "docker-compose.yml", 0, "File not found")
            return
        
        with open(docker_compose, 'r') as f:
            content = f.read()
            lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Default passwords
            if "admin123" in line or "CHANGE_THIS" in line:
                self.log_issue("CRITICAL", "Security", "docker-compose.yml", i,
                              "Default password detected - must be changed in production")
            
            # Missing healthcheck
            if "healthcheck:" not in content.lower():
                self.log_issue("WARNING", "Infrastructure", "docker-compose.yml", 0,
                              "No healthcheck configured")
    
    def analyze_env_example(self):
        """Analyse env.example"""
        env_example = self.backend_dir / "env.example"
        if not env_example.exists():
            self.log_issue("CRITICAL", "Configuration", "backend/env.example", 0, "File not found")
            return
        
        with open(env_example, 'r') as f:
            content = f.read()
            lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if "CHANGE_THIS" in line:
                self.log_issue("WARNING", "Configuration", "backend/env.example", i,
                              "Placeholder value detected - must be configured in production")
    
    def run_analysis(self):
        """Exécute l'analyse complète"""
        print("=" * 80)
        print("ANALYSE AUTOMATISÉE - ERP FABS V7")
        print(f"Projet: {self.project_root}")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()
        
        # Analyser les fichiers Python
        print("📂 Analyse fichiers Python...")
        python_files = list(self.backend_dir.rglob("*.py"))
        for file_path in python_files:
            if "test" not in str(file_path) and "__pycache__" not in str(file_path):
                self.analyze_python_file(file_path)
        
        # Analyser les fichiers JavaScript/JSX
        print("\n📂 Analyse fichiers JavaScript/JSX...")
        js_files = list(self.frontend_dir.rglob("*.js")) + list(self.frontend_dir.rglob("*.jsx"))
        for file_path in js_files:
            if "node_modules" not in str(file_path):
                self.analyze_javascript_file(file_path)
        
        # Analyser Docker Compose
        print("\n📂 Analyse Docker Compose...")
        self.analyze_docker_compose()
        
        # Analyser env.example
        print("\n📂 Analyse Configuration...")
        self.analyze_env_example()
        
        # Générer le rapport
        self.generate_report()
    
    def generate_report(self):
        """Génère le rapport d'analyse"""
        critical = sum(1 for i in self.issues if i["severity"] == "CRITICAL")
        warning = sum(1 for i in self.issues if i["severity"] == "WARNING")
        error = sum(1 for i in self.issues if i["severity"] == "ERROR")
        total = len(self.issues)
        
        print("\n" + "=" * 80)
        print("RAPPORT D'ANALYSE")
        print("=" * 80)
        print(f"Total problèmes: {total}")
        print(f"🔴 Critiques: {critical}")
        print(f"🟡 Avertissements: {warning}")
        print(f"🔵 Erreurs: {error}")
        print("=" * 80)
        
        # Sauvegarder le rapport
        report = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "total_issues": total,
            "critical_issues": critical,
            "warning_issues": warning,
            "error_issues": error,
            "issues": self.issues
        }
        
        with open("analysis_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\nRapport sauvegardé: analysis_report.json")
        
        # Afficher les problèmes par catégorie
        print("\n📋 Problèmes par catégorie:")
        categories = {}
        for issue in self.issues:
            cat = issue["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(issue)
        
        for cat, issues in categories.items():
            print(f"\n{cat}: {len(issues)} problèmes")
            for issue in issues:
                severity_icon = "🔴" if issue["severity"] == "CRITICAL" else "🟡" if issue["severity"] == "WARNING" else "🔵"
                print(f"  {severity_icon} {issue['file']}:{issue['line']} - {issue['message']}")

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    analyzer = CodeAnalyzer(str(project_root))
    analyzer.run_analysis()
