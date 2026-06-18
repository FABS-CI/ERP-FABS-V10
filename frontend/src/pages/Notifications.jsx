import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { Bell, Check, CheckCheck, Trash2, Filter, Settings, Info, AlertTriangle, XCircle, CheckCircle, Package, ShoppingCart, CreditCard, Truck } from "lucide-react";
import { listNotifications, listUnreadNotifications, countUnread, markAsRead, markAllAsRead, deleteNotification } from "@/services/notificationsService";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/layout/PageHeader";

const Notifications = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState("all"); // all, unread
  const [categoryFilter, setCategoryFilter] = useState("");

  const { data: notifications, isLoading } = useQuery(
    ["notifications", filter, categoryFilter],
    () => listNotifications({ categorie: categoryFilter, lue: filter === "unread" ? false : undefined }),
    { enabled: !!user }
  );

  const { data: unreadCount } = useQuery(
    ["notifications-count"],
    countUnread,
    { enabled: !!user, refetchInterval: 30000 }
  );

  const markAsReadMutation = useMutation(markAsRead, {
    onSuccess: () => {
      queryClient.invalidateQueries(["notifications"]);
      queryClient.invalidateQueries(["notifications-count"]);
    },
  });

  const markAllAsReadMutation = useMutation(markAllAsRead, {
    onSuccess: () => {
      queryClient.invalidateQueries(["notifications"]);
      queryClient.invalidateQueries(["notifications-count"]);
      toast.success("Toutes les notifications marquées comme lues");
    },
  });

  const deleteMutation = useMutation(deleteNotification, {
    onSuccess: () => {
      queryClient.invalidateQueries(["notifications"]);
      queryClient.invalidateQueries(["notifications-count"]);
      toast.success("Notification supprimée");
    },
  });

  const handleMarkAsRead = (notificationId) => {
    markAsReadMutation.mutate(notificationId);
  };

  const handleMarkAllAsRead = () => {
    markAllAsReadMutation.mutate();
  };

  const handleDelete = (notificationId) => {
    if (window.confirm("Êtes-vous sûr de vouloir supprimer cette notification ?")) {
      deleteMutation.mutate(notificationId);
    }
  };

  const getCategoryIcon = (category) => {
    const icons = {
      stock: <Package className="w-4 h-4" />,
      commande: <ShoppingCart className="w-4 h-4" />,
      paiement: <CreditCard className="w-4 h-4" />,
      livraison: <Truck className="w-4 h-4" />,
      systeme: <Settings className="w-4 h-4" />,
    };
    return icons[category] || <Info className="w-4 h-4" />;
  };

  const getTypeIcon = (type) => {
    const icons = {
      info: <Info className="w-4 h-4 text-blue-500" />,
      warning: <AlertTriangle className="w-4 h-4 text-yellow-500" />,
      error: <XCircle className="w-4 h-4 text-red-500" />,
      success: <CheckCircle className="w-4 h-4 text-green-500" />,
    };
    return icons[type] || <Info className="w-4 h-4" />;
  };

  const getCategoryBadge = (category) => {
    const variants = {
      stock: "secondary",
      commande: "default",
      paiement: "outline",
      livraison: "success",
      systeme: "destructive",
    };
    const labels = {
      stock: "Stock",
      commande: "Commande",
      paiement: "Paiement",
      livraison: "Livraison",
      systeme: "Système",
    };
    return (
      <Badge variant={variants[category] || "secondary"}>
        {labels[category] || category}
      </Badge>
    );
  };

  if (isLoading) return <DashboardLayout><div className="p-2">Chargement...</div></DashboardLayout>;

  return (
    <DashboardLayout>
    <div data-testid="notifications-page">
      <PageHeader
        icon={Bell}
        title="Centre de Notifications"
        description={unreadCount?.count > 0 ? `${unreadCount.count} notification(s) non lue(s)` : "Toutes vos notifications ERP"}
        favoriteKey="notifications"
        actions={
          <>
            <Button
              variant={filter === "all" ? "default" : "outline"}
              onClick={() => setFilter("all")}
              className={filter === "all" ? "bg-[#FF6200] hover:bg-[#E65800]" : ""}
              data-testid="filter-all"
            >
              Toutes
            </Button>
            <Button
              variant={filter === "unread" ? "default" : "outline"}
              onClick={() => setFilter("unread")}
              className={filter === "unread" ? "bg-[#FF6200] hover:bg-[#E65800]" : ""}
              data-testid="filter-unread"
            >
              Non lues
            </Button>
            {unreadCount?.count > 0 && (
              <Button
                variant="outline"
                onClick={handleMarkAllAsRead}
                disabled={markAllAsReadMutation.isLoading}
                data-testid="btn-mark-all-read"
              >
                <CheckCheck className="w-4 h-4 mr-2" />
                Tout lire
              </Button>
            )}
          </>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex gap-4">
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="px-4 py-2 border rounded-md bg-white dark:bg-[#040f1a] dark:border-gray-700"
            >
              <option value="">Toutes les catégories</option>
              <option value="stock">Stock</option>
              <option value="commande">Commande</option>
              <option value="paiement">Paiement</option>
              <option value="livraison">Livraison</option>
              <option value="systeme">Système</option>
            </select>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {notifications?.map((notif) => (
              <div
                key={notif.notification_id}
                className={`p-4 rounded-lg border ${
                  !notif.lue ? "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800" : "bg-white dark:bg-[#040f1a]"
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-1">{getTypeIcon(notif.type)}</div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-[#0A2540] dark:text-white">{notif.titre}</h3>
                      {!notif.lue && <Badge variant="default">Nouveau</Badge>}
                      {getCategoryBadge(notif.categorie)}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{notif.message}</p>
                    <p className="text-xs text-gray-400">{new Date(notif.created_at).toLocaleString("fr-FR")}</p>
                  </div>
                  <div className="flex gap-2">
                    {!notif.lue && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleMarkAsRead(notif.notification_id)}
                        disabled={markAsReadMutation.isLoading}
                      >
                        <Check className="w-4 h-4" />
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(notif.notification_id)}
                      disabled={deleteMutation.isLoading}
                    >
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
            {notifications?.length === 0 && (
              <div className="text-center py-8 text-gray-500 dark:text-white/50">
                <Bell className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>Aucune notification</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
    </DashboardLayout>
  );
};

export default Notifications;
