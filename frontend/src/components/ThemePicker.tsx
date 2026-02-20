"use client";

import { useState, useRef, useEffect } from "react";
import { useTheme, THEMES } from "./ThemeProvider";
import type { ThemeId } from "./ThemeProvider";

export default function ThemePicker() {
  const { theme, setTheme } = useTheme();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Close on click outside
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  const currentTheme = THEMES.find((t) => t.id === theme) || THEMES[0];

  return (
    <div className="relative" ref={ref}>
      {/* Trigger button — 3 color dots */}
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg hover:bg-white/10 transition-colors"
        title="Changer le theme"
      >
        {currentTheme.colors.map((c, i) => (
          <div
            key={i}
            className="w-3 h-3 rounded-full border border-white/30"
            style={{ backgroundColor: c }}
          />
        ))}
        <svg
          className={`w-3 h-3 text-gray-400 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute right-0 top-full mt-2 w-64 bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden z-50 animate-fade-in">
          <div className="px-4 py-3 border-b border-gray-100">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Theme visuel
            </p>
          </div>
          <div className="py-2">
            {THEMES.map((t) => (
              <button
                key={t.id}
                onClick={() => {
                  setTheme(t.id as ThemeId);
                  setOpen(false);
                }}
                className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                  theme === t.id
                    ? "bg-gray-50"
                    : "hover:bg-gray-50"
                }`}
              >
                {/* Color swatches */}
                <div className="flex -space-x-1">
                  {t.colors.map((c, i) => (
                    <div
                      key={i}
                      className="w-5 h-5 rounded-full border-2 border-white shadow-sm"
                      style={{ backgroundColor: c }}
                    />
                  ))}
                </div>

                {/* Label */}
                <span className="text-sm text-gray-700 font-medium flex-1">
                  {t.name}
                </span>

                {/* Check mark */}
                {theme === t.id && (
                  <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
