"""
Script d'audit final avant déploiement Emergent IA - ERP FABS-CI V7
Valide tous les aspects techniques du projet avant déploiement
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

class AuditFinal:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.errors = []
        self.warnings = []
        self.successes = []
        self.results = {}
        
    def log_error(self, section, message):
        self.errors.append(f"[{section}] {message}")
        print(f"❌ [{section}] {message}")
        
    def log_warning(self, section, message):
        self.warnings.append(f"[{section}] {message}")
        print(f"⚠️  [{section}] {message}")
        
    def log_success(self, section, message):
        self.successes.append(f"[{section}] {message}")
        print(f"✅ [{section}] {message}")
        
    def audit_1_build_backend(self):
        """Audit 1: Validation build backend"""
        print("\n" + "="*60)
        print("AUDIT 1: VALIDATION BUILD BACKEND")
        print("="*60)
        
        requirements_file = self.root_dir / "backend" / "requirements.txt"
        
        # Vérifier que requirements.txt existe
        if not requirements_file.exists():
            self.log_error("BUILD BACKEND", "requirements.txt non trouvé")
            return False
            
        self.log_success("BUILD BACKEND", "requirements.txt trouvé")
        
        # Vérifier les dépendances critiques
        critical_deps = [
            "fastapi", "uvicorn", "motor", "pymongo", "redis", 
            "pyjwt", "bcrypt", "passlib", "slowapi", "pydantic"
        ]
        
        with open(requirements_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for dep in critical_deps:
            if dep in content.lower():
                self.log_success("BUILD BACKEND", f"Dépendance critique trouvée: {dep}")
            else:
                self.log_error("BUILD BACKEND", f"Dépendance critique manquante: {dep}")
                
        # Vérifier que server.py existe
        server_file = self.root_dir / "backend" / "server.py"
        if not server_file.exists():
            self.log_error("BUILD BACKEND", "server.py non trouvé")
            return False
            
        self.log_success("BUILD BACKEND", "server.py trouvé")
        
        # Vérifier les imports dans server.py
        with open(server_file, 'r', encoding='utf-8') as f:
            server_content = f.read()
            
        critical_imports = [
            "from fastapi import",
            "from motor.motor_asyncio import",
            "import redis",
            "import jwt",
            "import bcrypt"
        ]
        
        for imp in critical_imports:
            if imp in server_content:
                self.log_success("BUILD BACKEND", f"Import critique trouvé: {imp}")
            else:
                self.log_warning("BUILD BACKEND", f"Import critique manquant: {imp}")
                
        return len(self.errors) == 0
        
    def audit_1_build_frontend(self):
        """Audit 1: Validation build frontend"""
        print("\n" + "="*60)
        print("AUDIT 1: VALIDATION BUILD FRONTEND")
        print("="*60)
        
        package_file = self.root_dir / "frontend" / "package.json"
        
        # Vérifier que package.json existe
        if not package_file.exists():
            self.log_error("BUILD FRONTEND", "package.json non trouvé")
            return False
            
        self.log_success("BUILD FRONTEND", "package.json trouvé")
        
        # Lire package.json
        with open(package_file, 'r', encoding='utf-8') as f:
            package_data = json.load(f)
            
        # Vérifier les dépendances critiques
        critical_deps = [
            "react", "react-dom", "react-router-dom", "axios",
            "tailwindcss", "lucide-react"
        ]
        
        dependencies = package_data.get("dependencies", {})
        dev_dependencies = package_data.get("devDependencies", {})
        all_deps = {**dependencies, **dev_dependencies}
        
        for dep in critical_deps:
            if dep in all_deps:
                self.log_success("BUILD FRONTEND", f"Dépendance critique trouvée: {dep}")
            else:
                self.log_error("BUILD FRONTEND", f"Dépendance critique manquante: {dep}")
                
        # Vérifier les scripts
        scripts = package_data.get("scripts", {})
        if "build" in scripts:
            self.log_success("BUILD FRONTEND", "Script build trouvé")
        else:
            self.log_error("BUILD FRONTEND", "Script build manquant")
            
        return len(self.errors) == 0
        
    def audit_2_docker(self):
        """Audit 2: Validation Docker"""
        print("\n" + "="*60)
        print("AUDIT 2: VALIDATION DOCKER")
        print("="*60)
        
        # Vérifier Dockerfile.backend
        dockerfile_backend = self.root_dir / "Dockerfile.backend"
        if dockerfile_backend.exists():
            self.log_success("DOCKER", "Dockerfile.backend trouvé")
            with open(dockerfile_backend, 'r', encoding='utf-8') as f:
                content = f.read()
                if "curl" in content:
                    self.log_success("DOCKER", "curl installé dans Dockerfile.backend")
                else:
                    self.log_error("DOCKER", "curl manquant dans Dockerfile.backend")
        else:
            self.log_error("DOCKER", "Dockerfile.backend non trouvé")
            
        # Vérifier Dockerfile.frontend
        dockerfile_frontend = self.root_dir / "Dockerfile.frontend"
        if dockerfile_frontend.exists():
            self.log_success("DOCKER", "Dockerfile.frontend trouvé")
            with open(dockerfile_frontend, 'r', encoding='utf-8') as f:
                content = f.read()
                if "wget" in content:
                    self.log_success("DOCKER", "wget installé dans Dockerfile.frontend")
                else:
                    self.log_error("DOCKER", "wget manquant dans Dockerfile.frontend")
        else:
            self.log_error("DOCKER", "Dockerfile.frontend non trouvé")
            
        # Vérifier nginx.conf
        nginx_conf = self.root_dir / "nginx.conf"
        if nginx_conf.exists():
            self.log_success("DOCKER", "nginx.conf trouvé")
            with open(nginx_conf, 'r', encoding='utf-8') as f:
                content = f.read()
                if "fabsci-backend" in content:
                    self.log_success("DOCKER", "Nom de service backend correct dans nginx.conf")
                else:
                    self.log_error("DOCKER", "Nom de service backend incorrect dans nginx.conf")
        else:
            self.log_error("DOCKER", "nginx.conf non trouvé")
            
        # Vérifier docker-compose.yml
        docker_compose = self.root_dir / "docker-compose.yml"
        if docker_compose.exists():
            self.log_success("DOCKER", "docker-compose.yml trouvé")
            with open(docker_compose, 'r', encoding='utf-8') as f:
                content = f.read()
                services = ["mongodb", "redis", "backend", "frontend"]
                for service in services:
                    if service in content:
                        self.log_success("DOCKER", f"Service {service} défini")
                    else:
                        self.log_error("DOCKER", f"Service {service} manquant")
        else:
            self.log_error("DOCKER", "docker-compose.yml non trouvé")
            
        return len(self.errors) == 0
        
    def audit_3_api(self):
        """Audit 3: Validation API"""
        print("\n" + "="*60)
        print("AUDIT 3: VALIDATION API")
        print("="*60)
        
        server_file = self.root_dir / "backend" / "server.py"
        
        if not server_file.exists():
            self.log_error("API", "server.py non trouvé")
            return False
            
        with open(server_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Vérifier endpoint health
        if '@api_router.get("/health")' in content:
            self.log_success("API", "Endpoint /health trouvé")
        else:
            self.log_error("API", "Endpoint /health manquant")
            
        # Vérifier endpoint docs
        if 'docs_url="/docs"' in content or 'docs_url' in content:
            self.log_success("API", "Documentation Swagger configurée")
        else:
            self.log_warning("API", "Documentation Swagger non explicitement configurée")
            
        # Vérifier endpoint login
        if '@api_router.post("/login")' in content or '/login' in content:
            self.log_success("API", "Endpoint login trouvé")
        else:
            self.log_error("API", "Endpoint login manquant")
            
        return len(self.errors) == 0
        
    def audit_6_securite(self):
        """Audit 6: Validation Sécurité"""
        print("\n" + "="*60)
        print("AUDIT 6: VALIDATION SECURITE")
        print("="*60)
        
        server_file = self.root_dir / "backend" / "server.py"
        
        if not server_file.exists():
            self.log_error("SECURITE", "server.py non trouvé")
            return False
            
        with open(server_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Vérifier JWT_SECRET
        if 'JWT_SECRET' in content:
            self.log_success("SECURITE", "JWT_SECRET configuré")
            if 'if env == \'production\' and not JWT_SECRET:' in content:
                self.log_success("SECURITE", "Validation JWT_SECRET en production")
        else:
            self.log_error("SECURITE", "JWT_SECRET non configuré")
            
        # Vérifier rate limiting
        if 'slowapi' in content.lower() or 'Limiter' in content:
            self.log_success("SECURITE", "Rate limiting configuré")
        else:
            self.log_warning("SECURITE", "Rate limiting non configuré")
            
        # Vérifier CORS
        if 'CORSMiddleware' in content:
            self.log_success("SECURITE", "CORS configuré")
        else:
            self.log_error("SECURITE", "CORS non configuré")
            
        # Vérifier validation mot de passe
        if 'PASSWORD_REGEX' in content or 'password' in content.lower():
            self.log_success("SECURITE", "Validation mot de passe configurée")
        else:
            self.log_warning("SECURITE", "Validation mot de passe non trouvée")
            
        return len(self.errors) == 0
        
    def audit_7_donnees_demo(self):
        """Audit 7: Validation Données Demo"""
        print("\n" + "="*60)
        print("AUDIT 7: VALIDATION DONNEES DEMO")
        print("="*60)
        
        seed_file = self.root_dir / "backend" / "seed_demo_data.py"
        
        if seed_file.exists():
            self.log_success("DONNEES DEMO", "seed_demo_data.py trouvé")
            with open(seed_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Vérifier les créations
            entities = ["users", "clients", "produits", "commandes"]
            for entity in entities:
                if f'db.{entity}' in content:
                    self.log_success("DONNEES DEMO", f"Création {entity} configurée")
                else:
                    self.log_warning("DONNEES DEMO", f"Création {entity} non trouvée")
                    
            # Vérifier les identifiants par défaut
            if "pissken@editionsfabsci.com" in content:
                self.log_success("DONNEES DEMO", "Identifiants admin configurés")
            else:
                self.log_warning("DONNEES DEMO", "Identifiants admin non trouvés")
        else:
            self.log_error("DONNEES DEMO", "seed_demo_data.py non trouvé")
            
        return len(self.errors) == 0
        
    def audit_8_emergent_ia(self):
        """Audit 8: Compatibilité Emergent IA"""
        print("\n" + "="*60)
        print("AUDIT 8: COMPATIBILITE EMERGENT IA")
        print("="*60)
        
        # Vérifier scripts de démarrage
        start_script = self.root_dir / "scripts" / "start.sh"
        if start_script.exists():
            self.log_success("EMERGENT IA", "start.sh trouvé")
        else:
            self.log_warning("EMERGENT IA", "start.sh non trouvé")
            
        # Vérifier script healthcheck
        healthcheck_script = self.root_dir / "scripts" / "healthcheck.sh"
        if healthcheck_script.exists():
            self.log_success("EMERGENT IA", "healthcheck.sh trouvé")
        else:
            self.log_warning("EMERGENT IA", "healthcheck.sh non trouvé")
            
        # Vérifier configuration production
        prod_config = self.root_dir / "scripts" / "production-env-config.json"
        if prod_config.exists():
            self.log_success("EMERGENT IA", "production-env-config.json trouvé")
            with open(prod_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if "variables" in config:
                    self.log_success("EMERGENT IA", "Variables d'environnement configurées")
                else:
                    self.log_warning("EMERGENT IA", "Variables d'environnement non trouvées")
        else:
            self.log_warning("EMERGENT IA", "production-env-config.json non trouvé")
            
        # Vérifier volumes persistants dans docker-compose
        docker_compose = self.root_dir / "docker-compose.yml"
        if docker_compose.exists():
            with open(docker_compose, 'r', encoding='utf-8') as f:
                content = f.read()
                if "volumes:" in content:
                    self.log_success("EMERGENT IA", "Volumes persistants configurés")
                else:
                    self.log_warning("EMERGENT IA", "Volumes persistants non configurés")
                    
        return len(self.errors) == 0
        
    def generate_report(self):
        """Générer le rapport final"""
        print("\n" + "="*60)
        print("RAPPORT FINAL")
        print("="*60)
        
        report = {
            "date": datetime.now().isoformat(),
            "status": "READY FOR DEPLOYMENT" if len(self.errors) == 0 else "NOT READY",
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
            "successes_count": len(self.successes),
            "errors": self.errors,
            "warnings": self.warnings,
            "successes": self.successes
        }
        
        print(f"\n📊 Statut: {report['status']}")
        print(f"❌ Erreurs: {report['errors_count']}")
        print(f"⚠️  Avertissements: {report['warnings_count']}")
        print(f"✅ Succès: {report['successes_count']}")
        
        if self.errors:
            print("\n❌ Erreurs détectées:")
            for error in self.errors:
                print(f"  - {error}")
                
        if self.warnings:
            print("\n⚠️  Avertissements:")
            for warning in self.warnings:
                print(f"  - {warning}")
                
        # Sauvegarder le rapport
        report_file = self.root_dir / "RAPPORT_AUDIT_FINAL.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n📄 Rapport sauvegardé: {report_file}")
        
        return report
        
    def run_full_audit(self):
        """Exécuter l'audit complet"""
        print("="*60)
        print("AUDIT FINAL AVANT DEPLOIEMENT EMERGENT IA")
        print("="*60)
        print(f"Date: {datetime.now().isoformat()}")
        print(f"Projet: ERP FABS-CI V7")
        
        # Exécuter tous les audits
        self.audit_1_build_backend()
        self.audit_1_build_frontend()
        self.audit_2_docker()
        self.audit_3_api()
        self.audit_6_securite()
        self.audit_7_donnees_demo()
        self.audit_8_emergent_ia()
        
        # Générer le rapport
        report = self.generate_report()
        
        return report

if __name__ == "__main__":
    audit = AuditFinal()
    report = audit.run_full_audit()
    
    # Exit code basé sur le statut
    sys.exit(0 if report["status"] == "READY FOR DEPLOYMENT" else 1)
