import { useTheme } from "../../hooks/useTheme";

/**
 * Carte statistique avec couleur de thème
 * 
 * Usage:
 * <ThemedStatCard
 *   icon={<Users className="w-8 h-8" />}
 *   label="Clients"
 *   value="1,245"
 *   trend="+5%"
 * />
 */
export default function ThemedStatCard({
  icon,
  label,
  value,
  trend,
  className = "",
  style = {},
}) {
  const { themeColor, themeVariants } = useTheme();

  return (
    <div
      className={`stat-card ${className}`}
      style={{
        borderLeftColor: themeColor,
        background: `linear-gradient(135deg, white, ${themeVariants.light})`,
        boxShadow: `0 2px 8px ${themeVariants.light}`,
        ...style,
      }}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p
            className="text-sm font-medium"
            style={{ color: "#9CA3AF" }}
          >
            {label}
          </p>
          <p
            className="text-3xl font-bold mt-2"
            style={{ color: themeVariants.darker }}
          >
            {value}
          </p>
          {trend && (
            <p
              className="text-xs font-semibold mt-2"
              style={{ color: themeColor }}
            >
              {trend}
            </p>
          )}
        </div>
        {icon && (
          <div
            className="p-3 rounded-lg"
            style={{
              backgroundColor: themeVariants.light,
              color: themeColor,
            }}
          >
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
