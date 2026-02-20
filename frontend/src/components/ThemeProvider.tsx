"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";

export type ThemeId = "emerald" | "finance" | "vibrant" | "energy" | "minimal" | "chic" | "earth";

export interface ThemeInfo {
  id: ThemeId;
  name: string;
  colors: [string, string, string]; // 3 swatch colors for the picker
}

export const THEMES: ThemeInfo[] = [
  { id: "emerald",  name: "Emerald Eco",       colors: ["#ffffff", "#16a34a", "#171717"] },
  { id: "finance",  name: "Finance Pro",        colors: ["#ffffff", "#1e40af", "#0f172a"] },
  { id: "vibrant",  name: "Vibrant Creative",   colors: ["#ffffff", "#c026d3", "#7c3aed"] },
  { id: "energy",   name: "Modern Energy",      colors: ["#ffffff", "#ea580c", "#171717"] },
  { id: "minimal",  name: "Minimalist",         colors: ["#ffffff", "#a3a3a3", "#171717"] },
  { id: "chic",     name: "Chic Bold",          colors: ["#ffffff", "#db2777", "#171717"] },
  { id: "earth",    name: "Earth Elegant",       colors: ["#fefce8", "#d97706", "#1c1917"] },
];

const STORAGE_KEY = "lexee_theme";

interface ThemeContextValue {
  theme: ThemeId;
  setTheme: (id: ThemeId) => void;
}

const ThemeContext = createContext<ThemeContextValue>({
  theme: "emerald",
  setTheme: () => {},
});

export function useTheme() {
  return useContext(ThemeContext);
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<ThemeId>("emerald");
  const [mounted, setMounted] = useState(false);

  // On mount: read from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as ThemeId | null;
    if (stored && THEMES.some((t) => t.id === stored)) {
      setThemeState(stored);
      document.documentElement.setAttribute("data-theme", stored);
    }
    setMounted(true);
  }, []);

  const setTheme = useCallback((id: ThemeId) => {
    setThemeState(id);
    localStorage.setItem(STORAGE_KEY, id);
    document.documentElement.setAttribute("data-theme", id);
  }, []);

  // Prevent flash of wrong theme
  if (!mounted) return null;

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
