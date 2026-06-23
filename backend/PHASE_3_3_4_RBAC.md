# Phase 3.3.4: Advanced RBAC/ACL

**Status:** ✅ Implemented  
**Commit:** TBD  
**Files:**
- `rbac_service.py` — Role & permission definitions + scope validation
- `server.py` — Integration

---

## Overview

**Role-Based Access Control (RBAC)** + **Attribute-Based Access Control (ABAC)**

Prevents users from accessing data outside their scope:
- Client-scoped access (can only access assigned clients)
- Department-scoped access (can only access own department)
- Resource ownership (can only modify own/team resources)
- Read-only users (can view but not modify)

---

## Roles (7)

| Role | Abbr | Permissions | Scope |
|------|------|-------------|-------|
| **Super Admin** | `super_admin` | All | All data |
| **Directeur Général** | `directeur_general` | View all, manage all | All data |
| **Directeur Commercial** | `directeur_commercial` | Sales operations | All clients |
| **Responsable Magasinier** | `responsable_magasinier` | Stock operations | Assigned only |
| **Comptable** | `comptable` | Accounting | All clients |
| **Gestionnaire Stock** | `gestionnaire_stock` | Stock management | Assigned only |
| **Secrétariat** | `secretariat` | Read-only reporting | Assigned only |
| **Service Logistique** | `service_logistique` | Logistics view | Assigned only |
| **Assistante** | `assistante` | Administrative | Limited view |

---

## Permissions (24)

### Clients (4)
- `view_clients` — Can see client list
- `create_clients` — Can create new clients
- `edit_clients` — Can modify client data
- `delete_clients` — Can soft-delete clients

### Produits (4)
- `view_produits` — Can see product catalog
- `create_produits` — Can add products
- `edit_produits` — Can modify products
- `delete_produits` — Can delete products

### Commandes (4)
- `view_commandes` — Can see orders
- `create_commandes` — Can create orders
- `edit_commandes` — Can modify orders
- `validate_commandes` — Can approve/reject

### Factures (4)
- `view_factures` — Can see invoices
- `create_factures` — Can create invoices
- `edit_factures` — Can modify invoices
- `validate_factures` — Can approve/finalize

### Paiements (2)
- `view_paiements` — Can see payments
- `process_paiements` — Can record/refund

### Stock (2)
- `view_stock` — Can check inventory
- `edit_stock` — Can adjust stock

### Rapports (2)
- `view_rapports` — Can access reports
- `export_rapports` — Can export data

### Utilisateurs (2)
- `view_utilisateurs` — Can list users
- `manage_utilisateurs` — Can CRUD users

### Admin (2)
- `admin_settings` — Can change system settings
- `audit_log` — Can view audit trail

---

## Architecture

### UserScope

```python
@dataclass
class UserScope:
    user_id: str                    # User's unique ID
    role: Role                      # User's role
    client_ids: List[str] = None    # If set, can only access these clients
    department: str = None          # If set, only this department
    read_only: bool = False         # Can't modify anything if True
```

### RBAC Methods

```python
# Check role permission
RBACService.has_permission(Role.DIRECTEUR_GENERAL, Permission.VIEW_CLIENTS)

# Check client access
RBACService.can_access_client(user_scope, client_id)

# Check resource modification
RBACService.can_modify_resource(user_scope, resource_owner_id)

# Check report access
RBACService.can_view_report(user_scope, "department")

# Build query filter (auto-restrict results)
filter_dict = RBACService.build_query_filter(user_scope)
# → {"client_id": {"$in": ["client1", "client2"]}}
```

---

## Access Policies

Declarative policies for common operations:

```python
ACCESS_POLICIES = {
    "clients:read": {
        Role.SUPER_ADMIN: True,
        Role.DIRECTEUR_GENERAL: True,
        Role.DIRECTEUR_COMMERCIAL: True,
        ...
    },
    "stock:read": {
        Role.SUPER_ADMIN: True,
        Role.RESPONSABLE_MAGASINIER: True,
        Role.GESTIONNAIRE_STOCK: True,
    },
    ...
}

# Check policy
can_view_stock = check_access_policy(user.role, "stock:read")
```

---

## Integration Pattern

### 1. Check Permission (Endpoint)

```python
from rbac_service import RBACService, Permission

@api_router.post("/api/clients")
async def create_client(data: ClientCreate):
    user = await resolve_user(request, authorization)
    
    # Check permission
    if not RBACService.has_permission(user["role"], Permission.CREATE_CLIENTS):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Create client
    result = await db.clients.insert_one(data.dict())
    return result
```

### 2. Check Scope (Resource Access)

```python
from rbac_service import RBACService, UserScope, Role

@api_router.get("/api/clients/{client_id}")
async def get_client(client_id: str):
    user = await resolve_user(request, authorization)
    user_scope = UserScope(
        user_id=user["user_id"],
        role=Role(user["role"]),
        client_ids=user.get("assigned_clients")
    )
    
    # Check if user can access this client
    if not RBACService.can_access_client(user_scope, client_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Return client data
    client = await db.clients.find_one({"_id": client_id})
    return client
```

### 3. Auto-Filter Results

```python
from rbac_service import RBACService, UserScope, Role

@api_router.get("/api/clients")
async def list_clients():
    user = await resolve_user(request, authorization)
    user_scope = UserScope(
        user_id=user["user_id"],
        role=Role(user["role"]),
        client_ids=user.get("assigned_clients")
    )
    
    # Build filter based on scope
    query_filter = RBACService.build_query_filter(user_scope)
    
    # Query respects user's scope automatically
    clients = await db.clients.find(query_filter).to_list(100)
    return clients
```

---

## Security Considerations

### ✅ Strengths

1. **Multi-layered:** Role-based + attribute-based
2. **Scope-based:** Can restrict to specific clients/departments
3. **Declarative:** Easy to see and audit permissions
4. **Query-level:** Automatic filtering at database level
5. **Granular:** 24 fine-grained permissions

### ⚠️ Limitations

1. **Not data-row-level:** Can't restrict to specific rows (use additional database views if needed)
2. **Requires initialization:** User scope must be set correctly
3. **Static mapping:** Changes require code deployment (consider database-backed roles in v2)

### 🔐 Best Practices

1. **Fail secure:** Default to deny if role/permission not found
2. **Audit modifications:** Log all permission checks in audit trail
3. **Review quarterly:** Audit who has which permissions
4. **Minimize elevation:** Keep super_admin count low
5. **Scope users:** Always set `client_ids` for scoped roles

---

## Testing

```bash
# Test permission check
python3 -c "
from rbac_service import RBACService, Role, Permission

# DG should have view_clients
assert RBACService.has_permission(Role.DIRECTEUR_GENERAL, Permission.VIEW_CLIENTS)

# Assistante should NOT have create_clients
assert not RBACService.has_permission(Role.ASSISTANTE, Permission.CREATE_CLIENTS)

print('✅ Permission checks passed')
"

# Test scope validation
python3 -c "
from rbac_service import RBACService, UserScope, Role

user = UserScope(
    user_id='user1',
    role=Role.RESPONSABLE_MAGASINIER,
    client_ids=['client1', 'client2']
)

# Should access assigned client
assert RBACService.can_access_client(user, 'client1')

# Should NOT access unassigned client
assert not RBACService.can_access_client(user, 'client99')

print('✅ Scope validation passed')
"
```

---

## Monitoring

Watch for:
- Repeated 403 errors (user trying to access unauthorized data)
- Permission changes (audit trail)
- Role elevation attempts (suspicious behavior)

```logs
[WARNING] User {user_id} attempted access to {resource} without permission
[AUDIT] Permission check: {user_id} {permission} {resource} {allowed}
```

---

## Role Transition in v2

For **database-backed roles** (recommended in v2):

```javascript
// roles collection
{
  "_id": "role_director_commercial",
  "name": "Directeur Commercial",
  "permissions": [
    "view_clients",
    "create_clients",
    ...
  ],
  "scope_type": "client",  // client, department, all
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

## Next Steps

- **Phase 3.3.5:** Audit trail enhancements (IP logging, action context)
- **Phase 3.3.6:** Rate limiting advanced (per-user, per-endpoint)
- **Phase 3.3.7:** Secrets rotation (automated key management)
- **Phase 3.4:** Data in-transit protection (TLS enforcement)

---

## References

- OWASP RBAC: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- ABAC: https://en.wikipedia.org/wiki/Attribute-based_access_control
- Principle of Least Privilege: https://owasp.org/www-community/attacks/Privilege_Escalation
