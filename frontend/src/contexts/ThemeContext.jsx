import React, { createContext, useState, useEffect, useCallback } from "react";
import { useLocation } from "react-router-dom";
import { getModuleFromPath, THEME_CONFIG } from "../utils/themeUtils";

export const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  const location = useLocation();
  const [activeModule, setActiveModule] = useState("dashboard");
  const [themeColor, setThemeColor] = useState(THEME_CONFIG.dashboard.base);
  const [themeVariants, setThemeVariants] = useState(THEME_CONFIG.dashboard.variants);

  // Detect module from URL path and update theme
  useEffect(() => {
    const detectedModule = getModuleFromPath(location.pathname);
    
    if (detectedModule && detectedModule !== activeModule) {
      setActiveModule(detectedModule);
      setThemeColor(THEME_CONFIG[detectedModule].base);
      setThemeVariants(THEME_CONFIG[detectedModule].variants);
      
      // Save to localStorage
      localStorage.setItem("fabs.theme.activeModule", detectedModule);
    }
  }, [location.pathname, activeModule]);

  // Initialize theme from localStorage on mount
  useEffect(() => {
    const savedModule = localStorage.getItem("fabs.theme.activeModule");
    if (savedModule && THEME_CONFIG[savedModule]) {
      setActiveModule(savedModule);
      setThemeColor(THEME_CONFIG[savedModule].base);
      setThemeVariants(THEME_CONFIG[savedModule].variants);
    }
  }, []);

  // Apply theme colors to CSS variables
  useEffect(() => {
    const root = document.documentElement;
    root.style.setProperty("--theme-primary", themeColor);
    root.style.setProperty("--theme-light", themeVariants.light);
    root.style.setProperty("--theme-lighter", themeVariants.lighter);
    root.style.setProperty("--theme-dark", themeVariants.dark);
    root.style.setProperty("--theme-darker", themeVariants.darker);
    root.style.setProperty("--theme-accent", themeVariants.accent);
  }, [themeColor, themeVariants]);

  const value = {
    activeModule,
    themeColor,
    themeVariants,
    THEME_CONFIG,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}
