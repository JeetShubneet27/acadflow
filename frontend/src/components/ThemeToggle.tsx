"use client";

import { useEffect, useState } from "react";

const STORAGE_KEY = "acadflow_theme";

type Theme = "light" | "dark";

const applyTheme = (theme: Theme) => {
  document.documentElement.dataset.theme = theme;
};

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("light");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem(STORAGE_KEY) as Theme | null;
    const prefersDark = window.matchMedia?.("(prefers-color-scheme: dark)").matches;
    const initial = stored || (prefersDark ? "dark" : "light");
    setTheme(initial);
    applyTheme(initial);
    setMounted(true);
  }, []);

  const toggleTheme = () => {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    window.localStorage.setItem(STORAGE_KEY, next);
    applyTheme(next);
  };

  if (!mounted) {
    return null;
  }

  return (
    <button type="button" onClick={toggleTheme} className="btn btn-secondary btn-xs">
      {theme === "light" ? "Dark mode" : "Light mode"}
    </button>
  );
}
