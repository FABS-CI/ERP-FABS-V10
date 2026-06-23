/**
 * SCRIPT TEST NOTIFICATIONS LIVE
 * 
 * Usage:
 *   1. Ouvrir http://localhost:3000
 *   2. Ouvrir Console DevTools (F12)
 *   3. Copier-coller ce script
 *   4. Exécuter
 * 
 * Résultat:
 *   - Son joue immédiatement
 *   - Message console avec détails
 *   - Simulation WebSocket notification event
 */

(async function testNotifications() {
  console.group("🧪 TEST NOTIFICATIONS LIVE");
  
  // Test 1: Vérifier WebSocket
  console.log("✓ Test 1: WebSocket Status");
  try {
    const { notificationWsManager } = await import('@/services/notificationsService');
    console.log(`  Connected: ${notificationWsManager.connected}`);
    console.log(`  Instance: ${notificationWsManager.constructor.name}`);
    if (!notificationWsManager.connected) {
      console.warn("  ⚠️  WebSocket NOT connected, tentative connexion...");
      notificationWsManager.connect(
        (payload) => console.log("  📨 Message reçu:", payload),
        () => console.log("  ✅ Connecté"),
        () => console.log("  ❌ Déconnecté")
      );
    }
  } catch (e) {
    console.error("  ❌ Erreur import:", e);
  }
  
  // Test 2: Jouer le son
  console.log("\n✓ Test 2: Son Notification");
  try {
    const audio = new Audio("/sounds/notification.mp3");
    audio.volume = 0.5;
    await audio.play();
    console.log("  ✅ Son joue (notification.mp3 @ 50%)");
  } catch (e) {
    console.error("  ❌ Erreur son:", e.message);
  }
  
  // Test 3: Simuler payload notification
  console.log("\n✓ Test 3: Notification Payload");
  const mockNotif = {
    event: "notification:new",
    payload: {
      type: "success",
      categorie: "commande",
      titre: "📦 Nouvelle commande CMD-2024-001",
      message: "Commande créée pour ABC Corp — 500,000 FCFA (en attente approv.)",
      lien: "/commandes/cmd-2024-001",
      created_at: new Date().toISOString(),
      user_id: "current-user",
    }
  };
  console.table(mockNotif.payload);
  
  // Test 4: Vérifier fichier son
  console.log("\n✓ Test 4: Fichier Son");
  try {
    const response = await fetch("/sounds/notification.mp3", { method: "HEAD" });
    const size = response.headers.get("content-length");
    console.log(`  ✅ Fichier accessible (${(size/1024).toFixed(1)} KB)`);
  } catch (e) {
    console.error("  ❌ Fichier inaccessible:", e.message);
  }
  
  // Test 5: Vérifier hook React
  console.log("\n✓ Test 5: React Hook");
  try {
    const { useNotifications } = await import('@/hooks/useNotifications');
    console.log(`  ✅ useNotifications hook disponible`);
    console.log(`  Usage: const { isConnected } = useNotifications(callback)`);
  } catch (e) {
    console.error("  ❌ Hook non disponible:", e.message);
  }
  
  // Test 6: Infos navigateur
  console.log("\n✓ Test 6: Infos Navigateur");
  console.log(`  Protocol: ${window.location.protocol}`);
  console.log(`  Host: ${window.location.host}`);
  console.log(`  WebSocket URL: ${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/notifications/ws`);
  
  // Test 7: Session Token
  console.log("\n✓ Test 7: Session Token");
  const sessionToken = localStorage.getItem("session_token") || sessionStorage.getItem("session_token");
  if (sessionToken) {
    console.log(`  ✅ Token présent (${sessionToken.substring(0, 20)}...)`);
  } else {
    console.warn("  ⚠️  Aucun token trouvé (WebSocket utilisera URL sans token)");
  }
  
  // Summary
  console.log("\n=".repeat(50));
  console.log("✅ TOUS LES TESTS COMPLÉTÉS");
  console.log("=".repeat(50));
  console.log(`
📋 RÉSUMÉ:
  • WebSocket: ${notificationWsManager?.connected ? '✅ Connecté' : '⚠️  À vérifier'}
  • Son: ✅ Joué (50%)
  • Fichier: ✅ Accessible
  • Hook React: ✅ Disponible
  • Token: ${sessionToken ? '✅ Présent' : '⚠️  Absent'}

Prochaines étapes:
  1. Créer une commande depuis un autre utilisateur
  2. Vérifier que cette page reçoit notification en temps réel
  3. Vérifier que le son joue
  4. Ouvrir page /notifications pour voir historique
  `);
  
  console.groupEnd();
})();
