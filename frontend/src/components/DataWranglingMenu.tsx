"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import type { CellData } from "@/components/SpreadsheetGrid";
import { COLS } from "@/components/SpreadsheetGrid";
import {
  removeEmptyRows,
  removeDuplicates,
  normalizePhones,
  splitNameColumn,
  fixCasing,
} from "@/lib/dataWrangling";

interface DataWranglingMenuProps {
  selectedCell: string | null;
  data: CellData;
  onDataChange: (data: CellData) => void;
}

export default function DataWranglingMenu({
  selectedCell,
  data,
  onDataChange,
}: DataWranglingMenuProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  const selectedCol = selectedCell ? selectedCell.replace(/\d/g, "") : null;
  const colIndex = selectedCol ? COLS.indexOf(selectedCol) : -1;
  const nextCol = colIndex >= 0 && colIndex < COLS.length - 1 ? COLS[colIndex + 1] : null;
  const hasCol = !!selectedCol;
  const canSplit = hasCol && !!nextCol;

  const run = useCallback(
    (fn: () => CellData) => {
      onDataChange(fn());
      setOpen(false);
    },
    [onDataChange]
  );

  const Item = ({
    label,
    disabled,
    onClick,
  }: {
    label: string;
    disabled?: boolean;
    onClick: () => void;
  }) => (
    <button
      disabled={disabled}
      onClick={onClick}
      className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
    >
      {label}
    </button>
  );

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 text-xs text-white/70 hover:text-white px-2.5 py-1.5 rounded hover:bg-white/10 transition-colors font-medium"
        title="Nettoyage automatique de données"
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
        </svg>
        Données
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 bg-white rounded-lg shadow-xl border border-gray-200 w-60 z-50 py-1.5 overflow-hidden">
          <p className="px-4 pt-1 pb-1.5 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
            Lignes
          </p>
          <Item
            label="Supprimer les lignes vides"
            onClick={() => run(() => removeEmptyRows(data))}
          />
          <Item
            label="Supprimer les doublons"
            disabled={!hasCol}
            onClick={() => run(() => removeDuplicates(data, selectedCol!))}
          />

          <div className="my-1.5 border-t border-gray-100" />

          <p className="px-4 pt-1 pb-1.5 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
            Colonne {selectedCol ?? "sélectionnée"}
          </p>
          <Item
            label="Normaliser les téléphones"
            disabled={!hasCol}
            onClick={() => run(() => normalizePhones(data, selectedCol!))}
          />
          <Item
            label={`Séparer Nom ↔ Prénom${nextCol ? ` → col. ${nextCol}` : ""}`}
            disabled={!canSplit}
            onClick={() => run(() => splitNameColumn(data, selectedCol!, nextCol!))}
          />
          <Item
            label="Corriger la casse"
            disabled={!hasCol}
            onClick={() => run(() => fixCasing(data, selectedCol!))}
          />
        </div>
      )}
    </div>
  );
}
