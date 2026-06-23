/**
 * Hook pour accéder aux permissions custom de l'utilisateur
 * Utilisé pour les règles spéciales par utilisateur (ex: DETY MICHEL)
 */
import { useAuth } from "./useAuth";

export function useCustomPermissions() {
  const { user } = useAuth();
  
  // Récupérer les permissions custom stockées côté backend
  const customPerms = user?.custom_permissions || {};
  
  return {
    canCreateCommandes: customPerms.can_create_commandes !== false,
    canCreateClients: customPerms.can_create_clients !== false,
    canModifyClients: customPerms.can_modify_clients !== false,
    canDisableClients: customPerms.can_disable_clients !== false,
    canCreateProduits: customPerms.can_create_produits !== false,
    canModifyProduits: customPerms.can_modify_produits !== false,
    canDisableProduits: customPerms.can_disable_produits !== false,
    hideStockQuantity: customPerms.hide_stock_quantity === true,
    hasFullRHAccess: customPerms.has_full_rh_access === true,
  };
}
