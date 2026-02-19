"use client";

import { useState } from "react";
import type { FormulaMeta } from "@/lib/api";

const CATEGORY_COLORS: Record<string, string> = {
  "Mathématiques": "bg-blue-100 text-blue-700 border-blue-200",
  Logique: "bg-purple-100 text-purple-700 border-purple-200",
  Recherche: "bg-amber-100 text-amber-700 border-amber-200",
  Statistiques: "bg-pink-100 text-pink-700 border-pink-200",
  Texte: "bg-cyan-100 text-cyan-700 border-cyan-200",
  Dates: "bg-orange-100 text-orange-700 border-orange-200",
  "Données": "bg-teal-100 text-teal-700 border-teal-200",
  Finance: "bg-green-100 text-green-700 border-green-200",
  Nettoyage: "bg-indigo-100 text-indigo-700 border-indigo-200",
  Architecture: "bg-slate-100 text-slate-700 border-slate-200",
  "Tableaux Dynamiques": "bg-violet-100 text-violet-700 border-violet-200",
  Analyse: "bg-rose-100 text-rose-700 border-rose-200",
};

interface SidebarProps {
  formulas: Record<string, FormulaMeta>;
  selected: string | null;
  onSelect: (key: string) => void;
}

/** Tooltip component — appears on hover */
function Tooltip({ text, children }: { text: string; children: React.ReactNode }) {
  const [show, setShow] = useState(false);

  return (
    <div
      className="relative"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      {show && (
        <div className="absolute z-50 left-full ml-3 top-1/2 -translate-y-1/2
                        bg-gray-900 text-white text-xs rounded-lg px-3 py-2
                        shadow-lg max-w-[240px] leading-relaxed
                        pointer-events-none animate-tooltip-in">
          {/* Arrow */}
          <div className="absolute right-full top-1/2 -translate-y-1/2
                          border-4 border-transparent border-r-gray-900" />
          {text}
        </div>
      )}
    </div>
  );
}

export default function Sidebar({ formulas, selected, onSelect }: SidebarProps) {
  // Group by category
  const categories: Record<string, { key: string; meta: FormulaMeta }[]> = {};
  for (const [key, meta] of Object.entries(formulas)) {
    const cat = meta.category;
    if (!categories[cat]) categories[cat] = [];
    categories[cat].push({ key, meta });
  }

  return (
    <aside className="w-72 bg-white border-r border-gray-200 flex flex-col h-full overflow-y-auto">
      <div className="px-5 py-4 border-b border-gray-100">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Formules disponibles
        </h2>
        <p className="text-[11px] text-gray-400 mt-1">
          {Object.keys(formulas).length} formules — survolez pour plus de details
        </p>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-5">
        {Object.entries(categories).map(([category, items]) => (
          <div key={category}>
            <span
              className={`inline-block px-2.5 py-1 rounded-md text-xs font-semibold mb-2 border ${
                CATEGORY_COLORS[category] || "bg-gray-100 text-gray-600 border-gray-200"
              }`}
            >
              {category}
              <span className="ml-1.5 opacity-60">{items.length}</span>
            </span>
            <ul className="space-y-1">
              {items.map(({ key, meta }) => (
                <li key={key}>
                  <Tooltip text={meta.description}>
                    <button
                      onClick={() => onSelect(key)}
                      className={`w-full text-left px-4 py-3 rounded-lg text-sm transition-all duration-150 ${
                        selected === key
                          ? "bg-lexee-50 text-lexee-800 font-medium border border-lexee-200 shadow-sm"
                          : "text-gray-700 hover:bg-gray-50 border border-transparent"
                      }`}
                    >
                      <div className="font-medium text-[13px] leading-tight">{meta.name}</div>
                      <div className="text-[11px] text-gray-400 mt-1 line-clamp-1">
                        {meta.description}
                      </div>
                    </button>
                  </Tooltip>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>
    </aside>
  );
}
