"use client";

import { useCallback } from "react";
import type { CellStyle } from "@/lib/types";

interface ToolbarProps {
  selectedCell: string | null;
  styles: Record<string, CellStyle>;
  onStylesChange: (styles: Record<string, CellStyle>) => void;
  onUndo: () => void;
  onRedo: () => void;
  onExportPDF: () => void;
  onShowChart: () => void;
}

export default function Toolbar({
  selectedCell,
  styles,
  onStylesChange,
  onUndo,
  onRedo,
  onExportPDF,
  onShowChart,
}: ToolbarProps) {
  const current = selectedCell ? styles[selectedCell] || {} : {};

  const setStyle = useCallback(
    (update: Partial<CellStyle>) => {
      if (!selectedCell) return;
      onStylesChange({
        ...styles,
        [selectedCell]: { ...current, ...update },
      });
    },
    [selectedCell, styles, current, onStylesChange]
  );

  const toggle = useCallback(
    (prop: "bold" | "italic") => setStyle({ [prop]: !current[prop] }),
    [current, setStyle]
  );

  const Btn = ({
    active,
    onClick,
    children,
    title,
  }: {
    active?: boolean;
    onClick: () => void;
    children: React.ReactNode;
    title: string;
  }) => (
    <button
      onClick={onClick}
      title={title}
      className={`px-2 py-1.5 rounded text-sm transition-colors ${
        active
          ? "bg-theme-primary-100 text-theme-primary-text"
          : "hover:bg-gray-100 text-gray-600"
      }`}
    >
      {children}
    </button>
  );

  const Sep = () => <div className="w-px h-6 bg-gray-200 mx-1" />;

  return (
    <div className="flex items-center gap-0.5 bg-white border-b border-gray-200 px-3 py-1 shrink-0 flex-wrap">
      {/* Undo / Redo */}
      <Btn onClick={onUndo} title="Annuler (Ctrl+Z)">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h10a5 5 0 015 5v2M3 10l4-4m-4 4l4 4" />
        </svg>
      </Btn>
      <Btn onClick={onRedo} title="Retablir (Ctrl+Y)">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M21 10H11a5 5 0 00-5 5v2m15-7l-4-4m4 4l-4 4" />
        </svg>
      </Btn>

      <Sep />

      {/* Text formatting */}
      <Btn active={current.bold} onClick={() => toggle("bold")} title="Gras (Ctrl+B)">
        <span className="font-bold">B</span>
      </Btn>
      <Btn active={current.italic} onClick={() => toggle("italic")} title="Italique (Ctrl+I)">
        <span className="italic">I</span>
      </Btn>

      <Sep />

      {/* Text color */}
      <div className="relative">
        <label title="Couleur du texte" className="cursor-pointer px-2 py-1.5 rounded hover:bg-gray-100 flex items-center gap-1">
          <span className="text-sm font-bold" style={{ color: current.color || "#000" }}>A</span>
          <input
            type="color"
            value={current.color || "#000000"}
            onChange={(e) => setStyle({ color: e.target.value })}
            className="w-0 h-0 opacity-0 absolute"
          />
        </label>
      </div>

      {/* Background color */}
      <div className="relative">
        <label title="Couleur de fond" className="cursor-pointer px-2 py-1.5 rounded hover:bg-gray-100 flex items-center gap-1">
          <span className="text-sm px-1 rounded" style={{ backgroundColor: current.bgColor || "#f3f4f6" }}>
            <svg className="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 24 24">
              <path d="M16.56 8.94L7.62 0 6.21 1.41l2.38 2.38-5.15 5.15a1.49 1.49 0 000 2.12l5.5 5.5c.29.29.68.44 1.06.44s.77-.15 1.06-.44l5.5-5.5c.59-.58.59-1.53 0-2.12zM5.21 10L10 5.21 14.79 10H5.21zM19 11.5s-2 2.17-2 3.5c0 1.1.9 2 2 2s2-.9 2-2c0-1.33-2-3.5-2-3.5z" />
            </svg>
          </span>
          <input
            type="color"
            value={current.bgColor || "#ffffff"}
            onChange={(e) => setStyle({ bgColor: e.target.value })}
            className="w-0 h-0 opacity-0 absolute"
          />
        </label>
      </div>

      <Sep />

      {/* Alignment */}
      <Btn active={current.align === "left"} onClick={() => setStyle({ align: "left" })} title="Aligner a gauche">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" d="M3 6h18M3 12h12M3 18h18" />
        </svg>
      </Btn>
      <Btn active={current.align === "center"} onClick={() => setStyle({ align: "center" })} title="Centrer">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" d="M3 6h18M6 12h12M3 18h18" />
        </svg>
      </Btn>
      <Btn active={current.align === "right"} onClick={() => setStyle({ align: "right" })} title="Aligner a droite">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" d="M3 6h18M9 12h12M3 18h18" />
        </svg>
      </Btn>

      <Sep />

      {/* Number format */}
      <select
        value={current.numberFormat || "general"}
        onChange={(e) => setStyle({ numberFormat: e.target.value as CellStyle["numberFormat"] })}
        className="text-xs border border-gray-200 rounded px-2 py-1.5 bg-white text-gray-600 hover:border-gray-300"
        title="Format de nombre"
      >
        <option value="general">General</option>
        <option value="number">Nombre</option>
        <option value="currency">Monnaie (EUR)</option>
        <option value="percent">Pourcentage</option>
        <option value="date">Date</option>
      </select>

      <Sep />

      {/* Chart */}
      <Btn onClick={onShowChart} title="Inserer un graphique">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      </Btn>

      {/* Export */}
      <Btn onClick={onExportPDF} title="Imprimer / Export PDF">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
        </svg>
      </Btn>
    </div>
  );
}
