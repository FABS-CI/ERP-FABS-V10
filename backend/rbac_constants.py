"""
ERP FABS-CI - RBAC Constants
Centralized role and permission definitions for backend
"""

# ============================================================================
# ROLES
# ============================================================================
ROLES = {
    "super_admin",
    "directeur_general",
    "comptable",
    "directeur_commercial",
    "gestionnaire_stock",
    "responsable_magasinier",
    "secretariat",
    "service_logistique",
    "assistante",
}

# ============================================================================
# ROLE HIERARCHY (for permission escalation checks)
# ============================================================================
ROLE_HIERARCHY = {
    "super_admin": 8,
    "directeur_general": 7,
    "comptable": 6,
    "directeur_commercial": 5,
    "gestionnaire_stock": 4,
    "responsable_magasinier": 3,
    "secretariat": 2,
    "assistante": 1,
    "service_logistique": 0,
}

# ============================================================================
# MODULE PERMISSIONS
# ============================================================================
# Format: {module: {role: permission_level}}
# permission_level: 0 = denied, 1 = read, 2 = write, 3 = admin
MODULE_PERMISSIONS = {
    "dashboard": {
        "super_admin": 2,
        "directeur_general": 1,
        "comptable": 1,
        "directeur_commercial": 1,
        "gestionnaire_stock": 1,
        "responsable_magasinier": 1,
        "secretariat": 1,
        "service_logistique": 1,
        "assistante": 0,
    },
    "clients": {
        "super_admin": 2,
        "directeur_general": 0,  # RBAC 2026-06-17: DG = dashboard+paiements+rh only
        "comptable": 1,
        "directeur_commercial": 2,
        "gestionnaire_stock": 0,
        "responsable_magasinier": 0,
        "secretariat": 2,
        "service_logistique": 0,
        "assistante": 2,
    },
    "produits": {
        "super_admin": 2,
        "directeur_general": 0,  # RBAC 2026-06-17
        "comptable": 0,
        "directeur_commercial": 2,
        "gestionnaire_stock": 2,
        "responsable_magasinier": 0,
        "secretariat": 2,  # RBAC 2026-06-17: secretariat write
        "service_logistique": 0,
        "assistante": 2,  # RBAC 2026-06-17: assistante write
    },
    "commandes": {
        "super_admin": 2,
        "directeur_general": 0,  # RBAC 2026-06-17
        "comptable": 2,
        "directeur_commercial": 1,  # RBAC 2026-06-17: read only
        "gestionnaire_stock": 0,
        "responsable_magasinier": 1,
        "secretariat": 2,
        "service_logistique": 0,
        "assistante": 2,
    },
    "factures": {
        "super_admin": 2,
        "directeur_general": 0,  # RBAC 2026-06-17: DG totalement retiré des factures
        "comptable": 2,
        "directeur_commercial": 0,
        "gestionnaire_stock": 0,
        "responsable_magasinier": 0,
        "secretariat": 0,
        "service_logistique": 0,
        "assistante": 0,
    },
    "paiements": {
        "super_admin": 2,
        "directeur_general": 1,  # RBAC 2026-06-17: DG garde lecture paiements
        "comptable": 2,
        "directeur_commercial": 0,
        "gestionnaire_stock": 0,
        "responsable_magasinier": 0,
        "secretariat": 0,
        "service_logistique": 0,
        "assistante": 0,
    },
    "livraisons": {
        "super_admin": 2,
        "directeur_general": 0,  # RBAC 2026-06-17
        "comptable": 0,  # RBAC 2026-06-17: comptable retiré
        "directeur_commercial": 1,  # RBAC 2026-06-17: read only
        "gestionnaire_stock": 0,  # RBAC 2026-06-17: read only (était 2)
        "responsable_magasinier": 0,
        "secretariat": 0,
        "service_logistique": 2,
        "assistante": 0,
    },
    "retours": {
        "super_admin": 2,
        "directeur_general": 0,  # RBAC 2026-06-17
        "comptable": 0,
        "directeur_commercial": 1,  # RBAC 2026-06-17: read only
        "gestionnaire_stock": 2,
        "responsable_magasinier": 0,  # RBAC 2026-06-17: read only
        "secretariat": 0,
        "service_logistique": 0,
        "assistante": 0,
    },
    "stock": {
        "super_admin": 2,
        "directeur_general": 0,  # RBAC 2026-06-17
        "comptable": 0,
        "directeur_commercial": 0,
        "gestionnaire_stock": 2,
        "responsable_magasinier": 1,
        "secretariat": 0,
        "service_logistique": 0,
        "assistante": 0,
    },
    "colis": {
        "super_admin": 2,
        "directeur_general": 0,  # RBAC 2026-06-17
        "comptable": 0,
        "directeur_commercial": 0,  # RBAC 2026-06-17: retiré
        "gestionnaire_stock": 0,  # RBAC 2026-06-17: retiré
        "responsable_magasinier": 2,
        "secretariat": 0,
        "service_logistique": 1,
        "assistante": 0,
    },
    "expeditions": {
        "super_admin": 2,
        "directeur_general": 0,  # RBAC 2026-06-17
        "comptable": 0,
        "directeur_commercial": 0,  # RBAC 2026-06-17: retiré
        "gestionnaire_stock": 0,
        "responsable_magasinier": 0,
        "secretariat": 0,
        "service_logistique": 2,
        "assistante": 0,
    },
    "notifications": {
        "super_admin": 2,
        "directeur_general": 1,
        "comptable": 1,
        "directeur_commercial": 1,
        "gestionnaire_stock": 1,
        "responsable_magasinier": 1,
        "secretariat": 1,
        "service_logistique": 1,
        "assistante": 1,
    },
    "logistique": {
        "super_admin": 2,
        "directeur_general": 0,  # RBAC 2026-06-17
        "comptable": 0,
        "directeur_commercial": 0,  # RBAC 2026-06-17: retiré
        "gestionnaire_stock": 0,
        "responsable_magasinier": 0,
        "secretariat": 0,
        "service_logistique": 2,
        "assistante": 0,
    },
    "comptabilite_avancee": {
        "super_admin": 2,
        "directeur_general": 0,  # RBAC 2026-06-17: DG retiré
        "comptable": 2,
        "directeur_commercial": 0,
        "gestionnaire_stock": 0,
        "responsable_magasinier": 0,
        "secretariat": 0,
        "service_logistique": 0,
        "assistante": 0,
    },
    "fleet": {
        "super_admin": 2,
        "directeur_general": 0,  # RBAC 2026-06-17: DG retiré
        "comptable": 0,
        "directeur_commercial": 0,
        "gestionnaire_stock": 0,
        "responsable_magasinier": 0,
        "secretariat": 0,
        "service_logistique": 2,
        "assistante": 0,
    },
    "logistics_costs": {
        "super_admin": 2,
        "directeur_general": 0,  # RBAC 2026-06-17: DG retiré
        "comptable": 1,
        "directeur_commercial": 0,
        "gestionnaire_stock": 0,
        "responsable_magasinier": 0,
        "secretariat": 0,
        "service_logistique": 2,
        "assistante": 0,
    },
    "multi_channel_notifications": {
        "super_admin": 2,
        "directeur_general": 0,  # RBAC 2026-06-17: DG retiré
        "comptable": 0,
        "directeur_commercial": 0,
        "gestionnaire_stock": 0,
        "responsable_magasinier": 0,
        "secretariat": 0,
        "service_logistique": 0,
        "assistante": 0,
    },
    "bi_analytics": {
        "super_admin": 2,
        "directeur_general": 0,  # RBAC 2026-06-17: DG retiré
        "comptable": 0,
        "directeur_commercial": 0,  # RBAC 2026-06-17: dir_com retiré
        "gestionnaire_stock": 0,
        "responsable_magasinier": 0,
        "secretariat": 0,
        "service_logistique": 0,
        "assistante": 0,
    },
    "workflow_approvals": {
        "super_admin": 2,
        "directeur_general": 0,  # RBAC 2026-06-17: DG retiré
        "comptable": 0,
        "directeur_commercial": 0,
        "gestionnaire_stock": 0,
        "responsable_magasinier": 0,
        "secretariat": 0,
        "service_logistique": 0,
        "assistante": 0,
    },
    "file_storage": {
        "super_admin": 2,
        "directeur_general": 0,  # RBAC 2026-06-17: DG retiré
        "comptable": 0,  # RBAC 2026-06-17: comptable retiré
        "directeur_commercial": 0,
        "gestionnaire_stock": 0,
        "responsable_magasinier": 0,
        "secretariat": 0,  # RBAC 2026-06-17: secretariat retiré
        "service_logistique": 0,
        "assistante": 0,
    },
    "backup": {
        "super_admin": 2,
        "directeur_general": 0,  # RBAC 2026-06-17: DG retiré
        "comptable": 0,
        "directeur_commercial": 0,
        "gestionnaire_stock": 0,
        "responsable_magasinier": 0,
        "secretariat": 0,
        "service_logistique": 0,
        "assistante": 0,
    },
    "comptabilite": {
        "super_admin": 2,
        "directeur_general": 0,  # RBAC 2026-06-17: DG retiré
        "comptable": 2,
        "directeur_commercial": 0,
        "gestionnaire_stock": 0,
        "responsable_magasinier": 0,
        "secretariat": 0,
        "service_logistique": 0,
        "assistante": 0,
    },
    "rapports": {
        "super_admin": 2,
        "directeur_general": 0,  # RBAC 2026-06-17: DG retiré
        "comptable": 2,
        "directeur_commercial": 0,  # RBAC 2026-06-17: dir_com retiré
        "gestionnaire_stock": 0,
        "responsable_magasinier": 0,
        "secretariat": 0,
        "service_logistique": 0,
        "assistante": 0,
    },
    "utilisateurs": {
        "super_admin": 2,
        "directeur_general": 0,  # RBAC 2026-06-17: DG retiré
        "comptable": 0,
        "directeur_commercial": 0,
        "gestionnaire_stock": 0,
        "responsable_magasinier": 0,
        "secretariat": 0,
        "service_logistique": 0,
        "assistante": 0,
    },
    "parametres": {
        "super_admin": 2,
        "directeur_general": 0,  # RBAC 2026-06-17: DG retiré
        "comptable": 0,
        "directeur_commercial": 0,
        "gestionnaire_stock": 0,
        "responsable_magasinier": 0,
        "secretariat": 0,
        "service_logistique": 0,
        "assistante": 0,
    },
    "rh": {
        "super_admin": 2,
        "directeur_general": 1,
        "comptable": 1,
        "directeur_commercial": 1,
        "secretariat": 2,
        "gestionnaire_stock": 0,
        "responsable_magasinier": 0,
        "service_logistique": 0,
        "assistante": 0,
    },
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def can_access(role: str, module: str, required_level: int = 1) -> bool:
    """
    Check if a role can access a module with the required permission level.
    
    Args:
        role: The user's role
        module: The module to check
        required_level: Minimum permission level (1=read, 2=write, 3=admin)
    
    Returns:
        True if the role has sufficient permissions, False otherwise
    """
    if role not in ROLES:
        return False
    
    if module not in MODULE_PERMISSIONS:
        return False
    
    return MODULE_PERMISSIONS[module].get(role, 0) >= required_level

def can_read(role: str, module: str) -> bool:
    """Check if a role can read from a module"""
    return can_access(role, module, required_level=1)

def can_write(role: str, module: str) -> bool:
    """Check if a role can write to a module"""
    return can_access(role, module, required_level=2)

def can_admin(role: str, module: str) -> bool:
    """Check if a role has admin rights on a module"""
    return can_access(role, module, required_level=3)

def get_accessible_modules(role: str) -> list:
    """Get list of modules accessible to a role"""
    return [module for module in MODULE_PERMISSIONS if can_read(role, module)]

def is_super_admin(role: str) -> bool:
    """Check if role is super_admin"""
    return role == "super_admin"

def is_directeur_general(role: str) -> bool:
    """Check if role is directeur_general"""
    return role == "directeur_general"

def is_financial_role(role: str) -> bool:
    """Check if role has financial access (can see purchase prices)"""
    return role in {"super_admin", "directeur_general", "comptable"}
