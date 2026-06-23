/**
 * Page FNE — Journal d'audit (Sprint 2 V10)
 */
import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, RefreshCw, FileText, Search, Download } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/PageHeader";
import { listFNELogs } from "../services/fneApi";

const STATUS_COLORS = {
  queued:    "bg-[#F59E0B] text-white",
  delivered: "bg-[#10B981] text-white",
  success:   "bg-[#10B981] text-white",
  failed:    "bg-[#EF4444] text-white",
  error:     "bg-[#EF4444] text-white",
};

export default function FNELogs() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await listFNELogs({ limit: 200 });
      setItems(r.items || []);
      setTotal(r.total || 0);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = items.filter((i) => {
    if (!search) return true;
    return (
      (i.invoice_id || "").toLowerCase().includes(search.toLowerCase()) ||
      (i.action || "").toLowerCase().includes(search.toLowerCase()) ||
      (i.status || "").toLowerCase().includes(search.toLowerCase())
    );
  });

  const exportCSV = () => {
    const headers = ["ts", "invoice_id", "action", "status", "user_id"];
    const rows = [headers, ...filtered.map((i) => headers.map((h) => i[h] || ""))];
    const csv = rows.map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `fne_logs_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
  };

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="fne-logs-page">
        <Button variant="ghost" onClick={() => navigate("/fne")} data-testid="btn-back">
          <ArrowLeft className="h-4 w-4 mr-2" /> Retour FNE
        </Button>

        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <FileText className="h-8 w-8 text-[#FF6200]" />
              Journal d&apos;audit FNE
            </h1>
            <p className="text-muted-foreground mt-1">{total} entrée(s) au total · {filtered.length} affichée(s)</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={load} data-testid="btn-refresh-logs">
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} /> Rafraîchir
            </Button>
            <Button variant="outline" onClick={exportCSV} data-testid="btn-export-csv">
              <Download className="h-4 w-4 mr-2" /> Export CSV
            </Button>
          </div>
        </div>

        <Card>
          <CardContent className="pt-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                data-testid="logs-search"
                type="search"
                placeholder="Rechercher dans les logs (invoice_id, action, statut…)"
                className="pl-9"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Journal complet</CardTitle>
            <CardDescription>Tous les événements FNE tracés depuis le démarrage</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-40 w-full" />
            ) : filtered.length === 0 ? (
              <div className="text-center py-16 text-muted-foreground" data-testid="logs-empty">
                <FileText className="h-12 w-12 mx-auto mb-3 opacity-30" />
                <p>Aucun log FNE pour l&apos;instant.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm" data-testid="logs-table">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-2 w-44">Horodatage</th>
                      <th className="text-left py-3 px-2">Invoice ID</th>
                      <th className="text-left py-3 px-2">Action</th>
                      <th className="text-center py-3 px-2">Statut</th>
                      <th className="text-left py-3 px-2">User</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((log, idx) => (
                      <tr key={idx} className="border-b hover:bg-muted/50" data-testid={`log-row-${idx}`}>
                        <td className="py-2 px-2 font-mono text-xs">{log.ts?.slice(0, 19).replace("T", " ") || "—"}</td>
                        <td className="py-2 px-2 font-mono">{log.invoice_id || "—"}</td>
                        <td className="py-2 px-2">{log.action || "—"}</td>
                        <td className="py-2 px-2 text-center">
                          <Badge className={STATUS_COLORS[log.status] || "bg-gray-400 text-white"}>
                            {log.status || "—"}
                          </Badge>
                        </td>
                        <td className="py-2 px-2 text-xs text-muted-foreground">{log.user_id || "system"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
