import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";
import { QueryClient, QueryClientProvider } from "react-query";

// Service Worker — désactivé (cause des problèmes de cache avec les requêtes API)
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.getRegistrations().then(registrations => {
    registrations.forEach(r => r.unregister());
  });
}

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 0,                         // pas de retry auto — échec = immédiat
      staleTime: 10 * 60 * 1000,        // 10 min — données considérées fraîches
      cacheTime: 15 * 60 * 1000,        // 15 min — garde en cache après unmount
    },
  },
});

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
);
