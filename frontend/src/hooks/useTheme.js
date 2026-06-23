import { useContext } from "react";
import { ThemeContext } from "../contexts/ThemeContext";

/**
 * Hook pour accéder au thème actif du module
 * 
 * Usage:
 * const { themeColor, themeVariants, activeModule } = useTheme();
 * 
 * return <div style={{ color: themeVariants.dark }}>Texte</div>
 */
export function useTheme() {
  const context = useContext(ThemeContext);
  
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  
  return context;
}
