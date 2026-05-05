"use client";

import { useState, useRef, useEffect } from "react";

interface SheetTab {
  id: string;
  name: string;
}

interface SheetTabsProps {
  sheets: SheetTab[];
  activeSheet: string;
  onSelect: (id: string) => void;
  onAdd: () => void;
  onRename: (id: string, name: string) => void;
  onDelete: (id: string) => void;
}

export default function SheetTabs({
  sheets,
  activeSheet,
  onSelect,
  onAdd,
  onRename,
  onDelete,
}: SheetTabsProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editingId && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editingId]);

  return (
    <div className="flex items-center bg-gray-100 border-t border-gray-300 px-2 py-1 gap-1 shrink-0 overflow-x-auto">
      {sheets.map((sheet) => (
        <div
          key={sheet.id}
          className={`flex items-center gap-1 px-3 py-1.5 rounded-t text-xs cursor-pointer transition-colors ${
            activeSheet === sheet.id
              ? "bg-white text-gray-900 font-medium border border-gray-300 border-b-white -mb-px"
              : "text-gray-500 hover:text-gray-700 hover:bg-gray-200"
          }`}
          onClick={() => onSelect(sheet.id)}
          onDoubleClick={() => {
            setEditingId(sheet.id);
            setEditValue(sheet.name);
          }}
        >
          {editingId === sheet.id ? (
            <input
              ref={inputRef}
              type="text"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onBlur={() => {
                if (editValue.trim()) onRename(sheet.id, editValue.trim());
                setEditingId(null);
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  if (editValue.trim()) onRename(sheet.id, editValue.trim());
                  setEditingId(null);
                }
                if (e.key === "Escape") setEditingId(null);
              }}
              className="w-20 text-xs border border-gray-300 rounded px-1 py-0.5 outline-none"
              onClick={(e) => e.stopPropagation()}
            />
          ) : (
            <span>{sheet.name}</span>
          )}
          {sheets.length > 1 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                if (confirm(`Supprimer "${sheet.name}" ?`)) onDelete(sheet.id);
              }}
              className="text-gray-400 hover:text-red-500 ml-1 text-[10px] leading-none"
            >
              &times;
            </button>
          )}
        </div>
      ))}
      <button
        onClick={onAdd}
        className="px-2 py-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded text-sm"
        title="Ajouter une feuille"
      >
        +
      </button>
    </div>
  );
}
