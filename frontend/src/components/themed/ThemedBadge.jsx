import { useTheme } from "../../hooks/useTheme";

/**
 * Badge avec couleur de thème
 * 
 * Usage:
 * <ThemedBadge variant="solid">En cours</ThemedBadge>
 * <ThemedBadge variant="outline">Validé</ThemedBadge>
 */
export default function ThemedBadge({
  children,
  variant = "light",
  className = "",
  style = {},
}) {
  const { themeColor, themeVariants } = useTheme();

  let badgeStyles = {
    display: "inline-block",
    padding: "0.25rem 0.75rem",
    borderRadius: "9999px",
    fontSize: "0.875rem",
    fontWeight: "600",
    whiteSpace: "nowrap",
    ...style,
  };

  switch (variant) {
    case "solid":
      badgeStyles = {
        ...badgeStyles,
        backgroundColor: themeColor,
        color: "white",
      };
      break;

    case "outline":
      badgeStyles = {
        ...badgeStyles,
        backgroundColor: "transparent",
        border: `1px solid ${themeColor}`,
        color: themeColor,
      };
      break;

    case "light":
    default:
      badgeStyles = {
        ...badgeStyles,
        backgroundColor: themeVariants.light,
        color: themeVariants.darker,
      };
      break;
  }

  return (
    <span className={`badge-themed ${className}`} style={badgeStyles}>
      {children}
    </span>
  );
}
