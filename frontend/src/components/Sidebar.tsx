"use client";

import type { FormulaMeta } from "@/lib/api";

const CATEGORY_COLORS: Record<string, string> = {
  "Mathématiques": "bg-blue-100 text-blue-700",
  Logique: "bg-purple-100 text-purple-700",
  Recherche: "bg-amber-100 text-amber-700",
  Statistiques: "bg-pink-100 text-pink-700",
  Texte: "bg-cyan-100 text-cyan-700",
  Dates: "bg-orange-100 text-orange-700",
  "Données": "bg-teal-100 text-teal-700",
  Finance: "bg-green-100 text-green-700",
};

interface SidebarProps {
  formulas: Record<string, FormulaMeta>;
  selected: string | null;
  onSelect: (key: string) => void;
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
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col h-full overflow-y-auto">
      <div className="px-4 py-3 border-b border-gray-200">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Formules disponibles
        </h2>
      </div>
      <nav className="flex-1 px-2 py-2 space-y-4">
        {Object.entries(categories).map(([category, items]) => (
          <div key={category}>
            <span
              className={`inline-block px-2 py-0.5 rounded text-xs font-medium mb-1.5 ${
                CATEGORY_COLORS[category] || "bg-gray-100 text-gray-600"
              }`}
            >
              {category}
            </span>
            <ul className="space-y-0.5">
              {items.map(({ key, meta }) => (
                <li key={key}>
                  <button
                    onClick={() => onSelect(key)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                      selected === key
                        ? "bg-green-50 text-green-800 font-medium border border-green-200"
                        : "text-gray-700 hover:bg-gray-100"
                    }`}
                  >
                    <div className="font-medium text-xs">{meta.name}</div>
                    <div className="text-[11px] text-gray-500 truncate">
                      {meta.description}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>
    </aside>
  );
}
