import { useEffect, useCallback, useRef } from 'react';
import { useQueryClient } from 'react-query';
import { notificationWsManager } from '@/services/notificationsService';

/**
 * Hook to manage real-time notifications via WebSocket
 * 
 * Usage:
 *   const { isConnected } = useNotifications((payload) => {
 *     console.log('New notification:', payload);
 *   });
 * 
 *   OR with explicit callbacks:
 *   useNotifications(onNewNotification, onConnect, onDisconnect);
 */
export const useNotifications = (
  onMessage = null,
  onConnect = null,
  onDisconnect = null
) => {
  const queryClient = useQueryClient();
  const connectedRef = useRef(false);
  const unsubscribeRef = useRef(null);

  const handleNewNotification = useCallback((payload) => {
    // Invalidate notifications queries to refetch
    if (payload.event === "notification:new") {
      queryClient.invalidateQueries(["notifications"]);
      queryClient.invalidateQueries(["notifications-count"]);
    }

    // Call user callback if provided
    if (onMessage) onMessage(payload);
  }, [queryClient, onMessage]);

  const handleConnect = useCallback(() => {
    connectedRef.current = true;
    if (onConnect) onConnect();
  }, [onConnect]);

  const handleDisconnect = useCallback(() => {
    connectedRef.current = false;
    if (onDisconnect) onDisconnect();
  }, [onDisconnect]);

  useEffect(() => {
    // Connect to WebSocket if not already connected
    if (!notificationWsManager.connected) {
      notificationWsManager.connect(
        handleNewNotification,
        handleConnect,
        handleDisconnect
      );
    }

    // Subscribe to manager events
    unsubscribeRef.current = notificationWsManager.subscribe(
      handleNewNotification
    );

    // Periodic ping to keep connection alive
    const pingInterval = setInterval(() => {
      notificationWsManager.ping();
    }, 30000); // Every 30 seconds

    // Cleanup
    return () => {
      clearInterval(pingInterval);
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
      }
    };
  }, [handleNewNotification, handleConnect, handleDisconnect]);

  return {
    isConnected: notificationWsManager.connected,
    disconnect: () => notificationWsManager.disconnect(),
    reconnect: () => {
      notificationWsManager.disconnect();
      notificationWsManager.connect(
        handleNewNotification,
        handleConnect,
        handleDisconnect
      );
    },
  };
};

export default useNotifications;
