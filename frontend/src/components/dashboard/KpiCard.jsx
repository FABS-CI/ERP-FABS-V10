import {
  TrendingUp, TrendingDown, AlertCircle, CheckCircle, ShoppingCart,
  Package, Truck, Wallet, Users, RotateCcw, Activity,
} from "lucide-react";
import { formatFCFA, formatFCFACompact } from "../../utils/format";

const ICONS = {
  TrendingUp, AlertCircle, CheckCircle, ShoppingCart, Package, Truck,
  Wallet, Users, RotateCcw, Activity,
};

export default function KpiCard({ kpi }) {
  const Icon = ICONS[kpi.icon] || Activity;
  const variation = kpi.variation_pct ?? 0;
  const variationPositive = variation > 0;
  const variationNeutral = variation === 0;
  const VarIcon = variationPositive ? TrendingUp : TrendingDown;
  const isCurrency = kpi.suffix === "FCFA";

  return (
    <div
      data-testid={`kpi-${kpi.key}`}
      style={{
        background: "#1E293B",
        border: "1px solid rgba(255,255,255,0.08)",
        borderRadius: "14px",
        padding: "20px",
        transition: "all 0.2s",
        cursor: "default",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = "translateY(-2px)";
        e.currentTarget.style.boxShadow = `0 12px 36px rgba(0,0,0,0.35)`;
        e.currentTarget.style.borderColor = "rgba(255,255,255,0.14)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "translateY(0)";
        e.currentTarget.style.boxShadow = "none";
        e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)";
      }}
    >
      <div className="flex items-start justify-between mb-4">
        {/* Icône */}
        <div
          style={{
            width: "44px", height: "44px",
            borderRadius: "12px",
            background: `${kpi.accent}18`,
            border: `1px solid ${kpi.accent}30`,
            display: "flex", alignItems: "center", justifyContent: "center",
          }}
        >
          <Icon style={{ width: "20px", height: "20px", color: kpi.accent }} />
        </div>

        {/* Badge variation */}
        {!variationNeutral && (
          <span
            style={{
              display: "inline-flex", alignItems: "center", gap: "3px",
              fontSize: "11px", fontWeight: 600, padding: "4px 8px", borderRadius: "99px",
              background: variationPositive ? "rgba(16,185,129,0.15)" : "rgba(239,68,68,0.15)",
              color: variationPositive ? "#10B981" : "#EF4444",
            }}
          >
            <VarIcon style={{ width: "12px", height: "12px" }} />
            {variationPositive ? "+" : ""}{variation.toFixed(1).replace(".", ",")}%
          </span>
        )}
      </div>

      {/* Label */}
      <p style={{ fontSize: "11px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: "#94A3B8", marginBottom: "6px" }}>
        {kpi.label}
      </p>

      {/* Valeur */}
      <p style={{ fontSize: "26px", fontWeight: 700, color: "#E2E8F0", lineHeight: 1.1, letterSpacing: "-0.02em" }}>
        {isCurrency ? formatFCFACompact(kpi.value) : kpi.value.toLocaleString("fr-FR")}
        {kpi.suffix && (
          <span style={{ fontSize: "12px", color: "#94A3B8", marginLeft: "4px", fontWeight: 500 }}>
            {kpi.suffix === "FCFA" ? "FCFA" : kpi.suffix}
          </span>
        )}
      </p>

      {/* Valeur secondaire */}
      {kpi.secondary_value != null && (
        <p style={{ fontSize: "11px", color: "#94A3B8", marginTop: "4px" }}>
          dont {formatFCFA(kpi.secondary_value)} dû
        </p>
      )}

      {/* Barre colorée en bas */}
      <div style={{ marginTop: "16px", height: "3px", borderRadius: "99px", background: `${kpi.accent}30` }}>
        <div style={{ height: "100%", borderRadius: "99px", background: kpi.accent, width: `${Math.min(Math.abs(variation) * 5 + 30, 100)}%`, transition: "width 0.6s ease" }} />
      </div>
    </div>
  );
}
