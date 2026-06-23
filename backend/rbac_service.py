"""
Advanced RBAC/ACL Service — Scope-based access control
Prevents users from accessing data outside their scope (client_id, department, etc.)
"""

import logging
from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger("fabsci.rbac")


class Role(str, Enum):
    """User roles in FABS-CI ERP"""
    SUPER_ADMIN = "super_admin"
    DIRECTEUR_GENERAL = "directeur_general"
    DIRECTEUR_COMMERCIAL = "directeur_commercial"
    RESPONSABLE_MAGASINIER = "responsable_magasinier"
    COMPTABLE = "comptable"
    GESTIONNAIRE_STOCK = "gestionnaire_stock"
    SECRETARIAT = "secretariat"
    SERVICE_LOGISTIQUE = "service_logistique"
    ASSISTANTE = "assistante"


class Permission(str, Enum):
    """Fine-grained permissions"""
    # Clients
    VIEW_CLIENTS = "view_clients"
    CREATE_CLIENTS = "create_clients"
    EDIT_CLIENTS = "edit_clients"
    DELETE_CLIENTS = "delete_clients"
    
    # Produits
    VIEW_PRODUITS = "view_produits"
    CREATE_PRODUITS = "create_produits"
    EDIT_PRODUITS = "edit_produits"
    DELETE_PRODUITS = "delete_produits"
    
    # Commandes
    VIEW_COMMANDES = "view_commandes"
    CREATE_COMMANDES = "create_commandes"
    EDIT_COMMANDES = "edit_commandes"
    VALIDATE_COMMANDES = "validate_commandes"
    
    # Factures
    VIEW_FACTURES = "view_factures"
    CREATE_FACTURES = "create_factures"
    EDIT_FACTURES = "edit_factures"
    VALIDATE_FACTURES = "validate_factures"
    
    # Paiements
    VIEW_PAIEMENTS = "view_paiements"
    PROCESS_PAIEMENTS = "process_paiements"
    
    # Stock
    VIEW_STOCK = "view_stock"
    EDIT_STOCK = "edit_stock"
    
    # Rapports
    VIEW_RAPPORTS = "view_rapports"
    EXPORT_RAPPORTS = "export_rapports"
    
    # Utilisateurs
    VIEW_UTILISATEURS = "view_utilisateurs"
    MANAGE_UTILISATEURS = "manage_utilisateurs"
    
    # Admin
    ADMIN_SETTINGS = "admin_settings"
    AUDIT_LOG = "audit_log"


# Role-to-Permission mapping
ROLE_PERMISSIONS: Dict[Role, List[Permission]] = {
    Role.SUPER_ADMIN: [p for p in Permission],  # All permissions
    
    Role.DIRECTEUR_GENERAL: [
        Permission.VIEW_CLIENTS,
        Permission.VIEW_PRODUITS,
        Permission.VIEW_COMMANDES,
        Permission.VIEW_FACTURES,
        Permission.VIEW_PAIEMENTS,
        Permission.VIEW_STOCK,
        Permission.VIEW_RAPPORTS,
        Permission.EXPORT_RAPPORTS,
        Permission.VIEW_UTILISATEURS,
        Permission.ADMIN_SETTINGS,
        Permission.AUDIT_LOG,
    ],
    
    Role.DIRECTEUR_COMMERCIAL: [
        Permission.VIEW_CLIENTS,
        Permission.CREATE_CLIENTS,
        Permission.EDIT_CLIENTS,
        Permission.VIEW_PRODUITS,
        Permission.VIEW_COMMANDES,
        Permission.CREATE_COMMANDES,
        Permission.EDIT_COMMANDES,
        Permission.VIEW_FACTURES,
        Permission.VIEW_PAIEMENTS,
        Permission.VIEW_RAPPORTS,
        Permission.EXPORT_RAPPORTS,
    ],
    
    Role.COMPTABLE: [
        Permission.VIEW_CLIENTS,
        Permission.VIEW_COMMANDES,
        Permission.VIEW_FACTURES,
        Permission.CREATE_FACTURES,
        Permission.EDIT_FACTURES,
        Permission.VIEW_PAIEMENTS,
        Permission.PROCESS_PAIEMENTS,
        Permission.VIEW_RAPPORTS,
        Permission.EXPORT_RAPPORTS,
    ],
    
    Role.RESPONSABLE_MAGASINIER: [
        Permission.VIEW_PRODUITS,
        Permission.VIEW_COMMANDES,
        Permission.VIEW_STOCK,
        Permission.EDIT_STOCK,
    ],
    
    Role.GESTIONNAIRE_STOCK: [
        Permission.VIEW_PRODUITS,
        Permission.VIEW_COMMANDES,
        Permission.VIEW_STOCK,
        Permission.EDIT_STOCK,
    ],
    
    Role.SERVICE_LOGISTIQUE: [
        Permission.VIEW_CLIENTS,
        Permission.VIEW_COMMANDES,
        Permission.VIEW_STOCK,
        Permission.VIEW_RAPPORTS,
    ],
    
    Role.SECRETARIAT: [
        Permission.VIEW_CLIENTS,
        Permission.VIEW_COMMANDES,
        Permission.VIEW_FACTURES,
        Permission.VIEW_PAIEMENTS,
        Permission.VIEW_RAPPORTS,
    ],
    
    Role.ASSISTANTE: [
        Permission.VIEW_CLIENTS,
        Permission.VIEW_PRODUITS,
        Permission.VIEW_RAPPORTS,
    ],
}


@dataclass
class UserScope:
    """User's access scope"""
    user_id: str
    role: Role
    client_ids: List[str] = None  # If set, can only access these clients
    department: Optional[str] = None  # If set, only this department
    read_only: bool = False  # If True, can't modify anything


class RBACService:
    """
    Role-Based Access Control + Attribute-Based Access Control (ABAC)
    
    Checks:
    1. Role-based permissions (can user perform action X?)
    2. Scope-based access (can user access resource Y?)
    3. Data ownership (does resource belong to user's scope?)
    """
    
    @staticmethod
    def has_permission(user_role: Role, permission: Permission) -> bool:
        """
        Check if user role has specific permission.
        
        Args:
            user_role: User's role
            permission: Permission to check
            
        Returns:
            True if role has permission
        """
        if user_role not in ROLE_PERMISSIONS:
            return False
        
        allowed = ROLE_PERMISSIONS[user_role]
        return permission in allowed
    
    @staticmethod
    def has_any_permission(user_role: Role, permissions: List[Permission]) -> bool:
        """Check if user has ANY of the permissions."""
        return any(RBACService.has_permission(user_role, p) for p in permissions)
    
    @staticmethod
    def has_all_permissions(user_role: Role, permissions: List[Permission]) -> bool:
        """Check if user has ALL of the permissions."""
        return all(RBACService.has_permission(user_role, p) for p in permissions)
    
    @staticmethod
    def can_access_client(user_scope: UserScope, client_id: str) -> bool:
        """
        Check if user can access specific client.
        
        Args:
            user_scope: User's scope
            client_id: Client ID to access
            
        Returns:
            True if user can access this client
        """
        # Super admin can access all clients
        if user_scope.role == Role.SUPER_ADMIN:
            return True
        
        # If client_ids specified, user can only access those
        if user_scope.client_ids:
            return client_id in user_scope.client_ids
        
        # Some roles can access all clients
        if user_scope.role in [
            Role.DIRECTEUR_GENERAL,
            Role.DIRECTEUR_COMMERCIAL,
            Role.COMPTABLE,
        ]:
            return True
        
        # Others are restricted (should have client_ids set)
        return False
    
    @staticmethod
    def can_modify_resource(user_scope: UserScope, resource_owner_id: str) -> bool:
        """
        Check if user can modify resource owned by another user.
        
        Args:
            user_scope: User's scope
            resource_owner_id: ID of resource owner (user_id)
            
        Returns:
            True if user can modify
        """
        # Super admin can modify anything
        if user_scope.role == Role.SUPER_ADMIN:
            return True
        
        # Read-only users can't modify
        if user_scope.read_only:
            return False
        
        # Users can modify own resources
        if user_scope.user_id == resource_owner_id:
            return True
        
        # Managers can modify team member resources
        if user_scope.role in [Role.DIRECTEUR_GENERAL, Role.DIRECTEUR_COMMERCIAL]:
            return True
        
        # Others can't modify
        return False
    
    @staticmethod
    def can_view_report(user_scope: UserScope, report_scope: str) -> bool:
        """
        Check if user can view report with specific scope.
        
        Args:
            user_scope: User's scope
            report_scope: Report scope ('personal', 'department', 'company', 'all')
            
        Returns:
            True if user can view
        """
        if user_scope.role == Role.SUPER_ADMIN:
            return True
        
        if report_scope == "personal":
            return True
        
        if report_scope == "department" and user_scope.department:
            return user_scope.role in [
                Role.DIRECTEUR_GENERAL,
                Role.DIRECTEUR_COMMERCIAL,
                Role.COMPTABLE,
            ]
        
        if report_scope == "company":
            return user_scope.role in [
                Role.DIRECTEUR_GENERAL,
                Role.DIRECTEUR_COMMERCIAL,
                Role.COMPTABLE,
            ]
        
        if report_scope == "all":
            return user_scope.role == Role.SUPER_ADMIN
        
        return False
    
    @staticmethod
    def build_query_filter(user_scope: UserScope) -> Dict[str, Any]:
        """
        Build MongoDB query filter based on user scope.
        
        For queries to automatically filter data by user's scope.
        
        Args:
            user_scope: User's scope
            
        Returns:
            MongoDB query filter dict
        """
        filter_dict = {}
        
        # Add client_id filter if user is scoped to specific clients
        if user_scope.client_ids and user_scope.role not in [
            Role.SUPER_ADMIN,
            Role.DIRECTEUR_GENERAL,
            Role.COMPTABLE,
        ]:
            filter_dict["client_id"] = {"$in": user_scope.client_ids}
        
        # Add department filter if applicable
        if user_scope.department and user_scope.role not in [Role.SUPER_ADMIN]:
            filter_dict["department"] = user_scope.department
        
        return filter_dict


# Policy definitions (for declarative access control)
ACCESS_POLICIES = {
    # Clients: DG and commercial can see all, others see assigned only
    "clients:read": {
        Role.SUPER_ADMIN: True,
        Role.DIRECTEUR_GENERAL: True,
        Role.DIRECTEUR_COMMERCIAL: True,
        Role.COMPTABLE: True,
        Role.SERVICE_LOGISTIQUE: True,
        Role.SECRETARIAT: True,
    },
    
    # Produits: limited to non-commercial operations
    "produits:read": {
        Role.SUPER_ADMIN: True,
        Role.DIRECTEUR_GENERAL: True,
        Role.DIRECTEUR_COMMERCIAL: True,
        Role.RESPONSABLE_MAGASINIER: True,
        Role.GESTIONNAIRE_STOCK: True,
        Role.ASSISTANTE: True,
    },
    
    # Commandes: most roles can view, some can create
    "commandes:read": {
        Role.SUPER_ADMIN: True,
        Role.DIRECTEUR_GENERAL: True,
        Role.DIRECTEUR_COMMERCIAL: True,
        Role.COMPTABLE: True,
        Role.RESPONSABLE_MAGASINIER: True,
        Role.GESTIONNAIRE_STOCK: True,
        Role.SERVICE_LOGISTIQUE: True,
        Role.SECRETARIAT: True,
    },
    
    # Factures: accounting team + managers
    "factures:read": {
        Role.SUPER_ADMIN: True,
        Role.DIRECTEUR_GENERAL: True,
        Role.DIRECTEUR_COMMERCIAL: True,
        Role.COMPTABLE: True,
        Role.SECRETARIAT: True,
    },
    
    # Stock: warehouse team only
    "stock:read": {
        Role.SUPER_ADMIN: True,
        Role.DIRECTEUR_GENERAL: True,
        Role.RESPONSABLE_MAGASINIER: True,
        Role.GESTIONNAIRE_STOCK: True,
    },
}


def check_access_policy(user_role: Role, policy_name: str) -> bool:
    """Check if user role has access to policy."""
    policy = ACCESS_POLICIES.get(policy_name, {})
    return policy.get(user_role, False)


logger.info("✅ RBAC Service initialized with 7 roles, 24 permissions")
