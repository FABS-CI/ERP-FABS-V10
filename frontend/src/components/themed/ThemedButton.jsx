import { useTheme } from "../../hooks/useTheme";
import { forwardRef } from "react";

/**
 * Bouton avec couleur de thème appliquée dynamiquement
 * 
 * Usage:
 * <ThemedButton variant="primary">Créer</ThemedButton>
 * <ThemedButton variant="outline">Annuler</ThemedButton>
 */
const ThemedButton = forwardRef(
  ({ 
    variant = "primary", 
    children, 
    className = "",
    style = {},
    ...props 
  }, ref) => {
    const { themeColor, themeVariants } = useTheme();

    const baseStyles = {
      fontWeight: "500",
      padding: "0.5rem 1rem",
      borderRadius: "0.375rem",
      cursor: "pointer",
      transition: "all 0.3s ease",
      border: "none",
      fontSize: "0.95rem",
      ...style,
    };

    let variantStyles = {};

    switch (variant) {
      case "primary":
        variantStyles = {
          backgroundColor: themeColor,
          color: "white",
          boxShadow: `0 2px 8px ${themeVariants.light}`,
        };
        break;

      case "outline":
        variantStyles = {
          backgroundColor: "transparent",
          border: `2px solid ${themeColor}`,
          color: themeColor,
        };
        break;

      case "ghost":
        variantStyles = {
          backgroundColor: "transparent",
          color: themeColor,
        };
        break;

      case "light":
        variantStyles = {
          backgroundColor: themeVariants.light,
          color: themeVariants.darker,
        };
        break;

      default:
        variantStyles = variantStyles["primary"];
    }

    const hoverStyles = {
      primary: {
        backgroundColor: themeVariants.dark,
        boxShadow: `0 4px 16px ${themeVariants.light}`,
      },
      outline: {
        backgroundColor: themeVariants.light,
        borderColor: themeVariants.dark,
        color: themeVariants.dark,
      },
      ghost: {
        backgroundColor: themeVariants.light,
        color: themeVariants.dark,
      },
      light: {
        backgroundColor: themeVariants.lighter,
      },
    };

    return (
      <button
        ref={ref}
        className={`btn-themed ${className}`}
        style={{
          ...baseStyles,
          ...variantStyles,
        }}
        onMouseEnter={(e) => {
          Object.assign(e.currentTarget.style, hoverStyles[variant]);
        }}
        onMouseLeave={(e) => {
          Object.assign(e.currentTarget.style, variantStyles);
        }}
        {...props}
      >
        {children}
      </button>
    );
  }
);

ThemedButton.displayName = "ThemedButton";

export default ThemedButton;
