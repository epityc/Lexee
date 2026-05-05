"use client";

import { useState, useRef, useCallback, useEffect, useMemo } from "react";
import { evaluate, isFormula, formatResult } from "@/lib/engine";
import type { CellStyle, ConditionalRule, ValidationRule } from "@/lib/types";

export type CellData = Record<string, Record<number, string>>;
export type CellFormulas = Record<string, string>;

interface SpreadsheetGridProps {
  data: CellData;
  formulas: CellFormulas;
  styles: Record<string, CellStyle>;
  validations: Record<string, ValidationRule>;
  conditionalRules: ConditionalRule[];
  colWidths: Record<string, number>;
  onDataChange: (data: CellData) => void;
  onStylesChange: (styles: Record<string, CellStyle>) => void;
  onColWidthsChange: (widths: Record<string, number>) => void;
  selectedCell: string | null;
  onSelectCell: (cell: string | null) => void;
  onSave?: () => void;
}

const COLS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
const ROW_COUNT = 100;
const DEFAULT_COL_WIDTH = 100;

export function cellToColRow(cell: string): { col: string; row: number } | null {
  const m = cell.match(/^([A-Z])(\d+)$/i);
  if (!m) return null;
  return { col: m[1].toUpperCase(), row: parseInt(m[2]) };
}

export function getCellValue(data: CellData, col: string, row: number): string {
  return data[col]?.[row] ?? "";
}

export function setCellValue(data: CellData, col: string, row: number, value: string): CellData {
  const next = { ...data };
  if (!next[col]) next[col] = {};
  next[col] = { ...next[col], [row]: value };
  return next;
}

export function parseCellRange(range: string): { col: string; row: number }[] {
  const m = range.match(/^([A-Z])(\d+):([A-Z])(\d+)$/i);
  if (!m) return [];
  const ci = COLS.indexOf(m[1].toUpperCase());
  const ce = COLS.indexOf(m[3].toUpperCase());
  const rs = parseInt(m[2]), re = parseInt(m[4]);
  const cells: { col: string; row: number }[] = [];
  for (let c = ci; c <= ce; c++)
    for (let r = rs; r <= re; r++)
      cells.push({ col: COLS[c], row: r });
  return cells;
}

export function getNumericValues(data: CellData, range: string): number[] {
  return parseCellRange(range)
    .map(({ col, row }) => parseFloat(getCellValue(data, col, row)))
    .filter((n) => !isNaN(n));
}

function dataToFlat(data: CellData): Record<string, string> {
  const flat: Record<string, string> = {};
  for (const [col, rows] of Object.entries(data)) {
    for (const [r, v] of Object.entries(rows)) {
      if (v !== "") flat[`${col}${r}`] = v;
    }
  }
  return flat;
}

function evalCell(cellId: string, data: CellData): string {
  const flat = dataToFlat(data);
  const raw = flat[cellId] ?? "";
  if (!isFormula(raw)) return raw;
  return formatResult(evaluate(raw, flat));
}

function matchesCondition(
  value: string,
  rule: ConditionalRule
): boolean {
  const num = parseFloat(value);
  const ruleVal = rule.value ? parseFloat(rule.value) : NaN;
  switch (rule.condition) {
    case "gt": return !isNaN(num) && !isNaN(ruleVal) && num > ruleVal;
    case "lt": return !isNaN(num) && !isNaN(ruleVal) && num < ruleVal;
    case "eq": return value === rule.value;
    case "neq": return value !== rule.value;
    case "contains": return value.includes(rule.value ?? "");
    case "empty": return value === "";
    case "notEmpty": return value !== "";
    default: return false;
  }
}

function getConditionalStyle(
  cellId: string,
  value: string,
  rules: ConditionalRule[]
): CellStyle | null {
  for (const rule of rules) {
    const cells = parseCellRange(rule.range);
    const matches = cells.some((c) => `${c.col}${c.row}` === cellId);
    if (matches && matchesCondition(value, rule)) return rule.style;
  }
  return null;
}

function incrementRef(ref: string, dRow: number, dCol: number): string {
  return ref.replace(/([A-Z])(\d+)/gi, (_, col: string, row: string) => {
    const ci = COLS.indexOf(col.toUpperCase());
    const newCol = COLS[Math.max(0, Math.min(25, ci + dCol))] ?? col;
    const newRow = Math.max(1, parseInt(row) + dRow);
    return `${newCol}${newRow}`;
  });
}

function formatNumber(value: string, fmt?: string): string {
  const n = parseFloat(value);
  if (isNaN(n) || !fmt || fmt === "general") return value;
  switch (fmt) {
    case "number": return n.toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    case "currency": return n.toLocaleString("fr-FR", { style: "currency", currency: "EUR" });
    case "percent": return (n * 100).toFixed(1) + "%";
    case "date": return value;
    default: return value;
  }
}

export default function SpreadsheetGrid({
  data,
  formulas,
  styles,
  validations,
  conditionalRules,
  colWidths,
  onDataChange,
  onStylesChange,
  onColWidthsChange,
  selectedCell,
  onSelectCell,
  onSave,
}: SpreadsheetGridProps) {
  const [editingCell, setEditingCell] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [clipboard, setClipboard] = useState<{ cell: string; value: string; style?: CellStyle } | null>(null);
  const [undoStack, setUndoStack] = useState<CellData[]>([]);
  const [redoStack, setRedoStack] = useState<CellData[]>([]);
  const [resizingCol, setResizingCol] = useState<string | null>(null);
  const [resizeStart, setResizeStart] = useState(0);
  const [showFilter, setShowFilter] = useState<string | null>(null);
  const [sortState, setSortState] = useState<{ col: string; dir: "asc" | "desc" } | null>(null);
  const [filterState, setFilterState] = useState<Record<string, Set<string>>>({});
  const [selectionRange, setSelectionRange] = useState<{ start: string; end: string } | null>(null);
  const [autofillDragging, setAutofillDragging] = useState(false);
  const [autofillTarget, setAutofillTarget] = useState<number | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const fxInputRef = useRef<HTMLInputElement>(null);
  const gridRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (editingCell && inputRef.current) inputRef.current.focus();
  }, [editingCell]);

  const computedValues = useMemo(() => {
    const flat = dataToFlat(data);
    const result: Record<string, string> = {};
    for (const [key, raw] of Object.entries(flat)) {
      if (isFormula(raw)) {
        result[key] = formatResult(evaluate(raw, flat));
      } else {
        result[key] = raw;
      }
    }
    return result;
  }, [data]);

  const sortedRows = useMemo(() => {
    let rows = Array.from({ length: ROW_COUNT }, (_, i) => i + 1);
    if (sortState) {
      const col = sortState.col;
      rows.sort((a, b) => {
        const va = computedValues[`${col}${a}`] ?? "";
        const vb = computedValues[`${col}${b}`] ?? "";
        const na = parseFloat(va), nb = parseFloat(vb);
        const cmp = !isNaN(na) && !isNaN(nb) ? na - nb : va.localeCompare(vb, "fr");
        return sortState.dir === "asc" ? cmp : -cmp;
      });
    }
    if (Object.keys(filterState).length > 0) {
      rows = rows.filter((r) => {
        for (const [col, allowed] of Object.entries(filterState)) {
          const val = computedValues[`${col}${r}`] ?? "";
          if (allowed.size > 0 && !allowed.has(val)) return false;
        }
        return true;
      });
    }
    return rows;
  }, [sortState, filterState, computedValues]);

  const pushUndo = useCallback(() => {
    setUndoStack((prev) => [...prev.slice(-50), JSON.parse(JSON.stringify(data))]);
    setRedoStack([]);
  }, [data]);

  const undo = useCallback(() => {
    setUndoStack((prev) => {
      if (prev.length === 0) return prev;
      const last = prev[prev.length - 1];
      setRedoStack((r) => [...r, JSON.parse(JSON.stringify(data))]);
      onDataChange(last);
      return prev.slice(0, -1);
    });
  }, [data, onDataChange]);

  const redo = useCallback(() => {
    setRedoStack((prev) => {
      if (prev.length === 0) return prev;
      const last = prev[prev.length - 1];
      setUndoStack((u) => [...u, JSON.parse(JSON.stringify(data))]);
      onDataChange(last);
      return prev.slice(0, -1);
    });
  }, [data, onDataChange]);

  const navigate = useCallback(
    (dc: number, dr: number) => {
      if (!selectedCell) { onSelectCell("A1"); return; }
      const p = cellToColRow(selectedCell);
      if (!p) return;
      const ci = COLS.indexOf(p.col);
      const nc = Math.max(0, Math.min(25, ci + dc));
      const nr = Math.max(1, Math.min(ROW_COUNT, p.row + dr));
      onSelectCell(`${COLS[nc]}${nr}`);
    },
    [selectedCell, onSelectCell]
  );

  const validateCell = useCallback(
    (cellId: string, value: string): boolean => {
      const rule = validations[cellId];
      if (!rule) return true;
      if (rule.type === "list" && rule.values) return rule.values.includes(value);
      if (rule.type === "number") {
        const n = parseFloat(value);
        if (isNaN(n)) return false;
        if (rule.min !== undefined && n < rule.min) return false;
        if (rule.max !== undefined && n > rule.max) return false;
      }
      return true;
    },
    [validations]
  );

  const commitEdit = useCallback(() => {
    if (!editingCell) return;
    const p = cellToColRow(editingCell);
    if (!p) return;
    if (!validateCell(editingCell, editValue)) {
      setValidationError(`Valeur invalide pour ${editingCell}`);
      setTimeout(() => setValidationError(null), 3000);
      return;
    }
    pushUndo();
    onDataChange(setCellValue(data, p.col, p.row, editValue));
    setEditingCell(null);
  }, [editingCell, editValue, data, onDataChange, pushUndo, validateCell]);

  const startEdit = useCallback(
    (cellId?: string) => {
      const target = cellId || selectedCell;
      if (!target) return;
      const p = cellToColRow(target);
      if (!p) return;
      setEditingCell(target);
      setEditValue(getCellValue(data, p.col, p.row));
    },
    [selectedCell, data]
  );

  const deleteCell = useCallback(() => {
    if (!selectedCell) return;
    const p = cellToColRow(selectedCell);
    if (!p) return;
    pushUndo();
    onDataChange(setCellValue(data, p.col, p.row, ""));
  }, [selectedCell, data, onDataChange, pushUndo]);

  const copyCell = useCallback(() => {
    if (!selectedCell) return;
    const p = cellToColRow(selectedCell);
    if (!p) return;
    setClipboard({
      cell: selectedCell,
      value: getCellValue(data, p.col, p.row),
      style: styles[selectedCell],
    });
  }, [selectedCell, data, styles]);

  const pasteCell = useCallback(() => {
    if (!selectedCell || !clipboard) return;
    const p = cellToColRow(selectedCell);
    if (!p) return;
    pushUndo();
    const src = cellToColRow(clipboard.cell);
    let value = clipboard.value;
    if (src && isFormula(value)) {
      const dr = p.row - src.row;
      const dc = COLS.indexOf(p.col) - COLS.indexOf(src.col);
      value = "=" + incrementRef(value.substring(1), dr, dc);
    }
    onDataChange(setCellValue(data, p.col, p.row, value));
    if (clipboard.style) {
      onStylesChange({ ...styles, [selectedCell]: clipboard.style });
    }
  }, [selectedCell, clipboard, data, styles, onDataChange, onStylesChange, pushUndo]);

  const handleAutofill = useCallback(
    (targetRow: number) => {
      if (!selectedCell) return;
      const p = cellToColRow(selectedCell);
      if (!p) return;
      pushUndo();
      const srcValue = getCellValue(data, p.col, p.row);
      let newData = { ...data };
      const startRow = p.row;
      const endRow = targetRow;
      const dir = endRow > startRow ? 1 : -1;
      for (let r = startRow + dir; dir > 0 ? r <= endRow : r >= endRow; r += dir) {
        let val = srcValue;
        if (isFormula(val)) {
          val = "=" + incrementRef(val.substring(1), r - startRow, 0);
        } else {
          const n = parseFloat(val);
          if (!isNaN(n)) val = String(n + (r - startRow));
        }
        newData = setCellValue(newData, p.col, r, val);
      }
      onDataChange(newData);
    },
    [selectedCell, data, onDataChange, pushUndo]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (editingCell) {
        if (e.key === "Enter") { e.preventDefault(); commitEdit(); navigate(0, e.shiftKey ? -1 : 1); }
        else if (e.key === "Escape") setEditingCell(null);
        else if (e.key === "Tab") { e.preventDefault(); commitEdit(); navigate(e.shiftKey ? -1 : 1, 0); }
        return;
      }

      if (e.ctrlKey || e.metaKey) {
        switch (e.key.toLowerCase()) {
          case "c": e.preventDefault(); copyCell(); return;
          case "v": e.preventDefault(); pasteCell(); return;
          case "z": e.preventDefault(); if (e.shiftKey) redo(); else undo(); return;
          case "y": e.preventDefault(); redo(); return;
          case "s": e.preventDefault(); onSave?.(); return;
          case "b": e.preventDefault(); toggleStyle("bold"); return;
          case "i": e.preventDefault(); toggleStyle("italic"); return;
        }
      }

      switch (e.key) {
        case "ArrowUp": e.preventDefault(); navigate(0, -1); break;
        case "ArrowDown": e.preventDefault(); navigate(0, 1); break;
        case "ArrowLeft": e.preventDefault(); navigate(-1, 0); break;
        case "ArrowRight": e.preventDefault(); navigate(1, 0); break;
        case "Tab": e.preventDefault(); navigate(e.shiftKey ? -1 : 1, 0); break;
        case "Enter": e.preventDefault(); startEdit(); break;
        case "F2": e.preventDefault(); startEdit(); break;
        case "Delete": case "Backspace": e.preventDefault(); deleteCell(); break;
        default:
          if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
            if (selectedCell) {
              setEditingCell(selectedCell);
              setEditValue(e.key);
            }
          }
      }
    },
    [editingCell, commitEdit, navigate, startEdit, deleteCell, copyCell, pasteCell, undo, redo, onSave, selectedCell]
  );

  const toggleStyle = useCallback(
    (prop: "bold" | "italic") => {
      if (!selectedCell) return;
      const current = styles[selectedCell] || {};
      onStylesChange({
        ...styles,
        [selectedCell]: { ...current, [prop]: !current[prop] },
      });
    },
    [selectedCell, styles, onStylesChange]
  );

  const handleSort = useCallback(
    (col: string) => {
      setSortState((prev) => {
        if (prev?.col === col) {
          if (prev.dir === "asc") return { col, dir: "desc" };
          return null;
        }
        return { col, dir: "asc" };
      });
      setShowFilter(null);
    },
    []
  );

  const handleFilter = useCallback(
    (col: string, values: Set<string>) => {
      setFilterState((prev) => {
        const next = { ...prev };
        if (values.size === 0) delete next[col];
        else next[col] = values;
        return next;
      });
    },
    []
  );

  const colUniqueValues = useCallback(
    (col: string): string[] => {
      const vals = new Set<string>();
      for (let r = 1; r <= ROW_COUNT; r++) {
        const v = computedValues[`${col}${r}`] ?? "";
        if (v !== "") vals.add(v);
      }
      return [...vals].sort();
    },
    [computedValues]
  );

  const handleResizeStart = useCallback(
    (col: string, clientX: number) => {
      setResizingCol(col);
      setResizeStart(clientX);
    },
    []
  );

  useEffect(() => {
    if (!resizingCol) return;
    const handleMove = (e: MouseEvent) => {
      const delta = e.clientX - resizeStart;
      const current = colWidths[resizingCol] ?? DEFAULT_COL_WIDTH;
      const newWidth = Math.max(40, current + delta);
      onColWidthsChange({ ...colWidths, [resizingCol]: newWidth });
      setResizeStart(e.clientX);
    };
    const handleUp = () => setResizingCol(null);
    window.addEventListener("mousemove", handleMove);
    window.addEventListener("mouseup", handleUp);
    return () => {
      window.removeEventListener("mousemove", handleMove);
      window.removeEventListener("mouseup", handleUp);
    };
  }, [resizingCol, resizeStart, colWidths, onColWidthsChange]);

  useEffect(() => {
    if (!autofillDragging) return;
    const handleMove = (e: MouseEvent) => {
      const grid = gridRef.current;
      if (!grid) return;
      const rows = grid.querySelectorAll("tbody tr");
      for (let i = 0; i < rows.length; i++) {
        const rect = rows[i].getBoundingClientRect();
        if (e.clientY >= rect.top && e.clientY <= rect.bottom) {
          setAutofillTarget(sortedRows[i]);
          break;
        }
      }
    };
    const handleUp = () => {
      if (autofillTarget !== null) handleAutofill(autofillTarget);
      setAutofillDragging(false);
      setAutofillTarget(null);
    };
    window.addEventListener("mousemove", handleMove);
    window.addEventListener("mouseup", handleUp);
    return () => {
      window.removeEventListener("mousemove", handleMove);
      window.removeEventListener("mouseup", handleUp);
    };
  }, [autofillDragging, autofillTarget, handleAutofill, sortedRows]);

  const fxDisplay = useMemo(() => {
    if (!selectedCell) return "";
    const p = cellToColRow(selectedCell);
    if (!p) return "";
    return getCellValue(data, p.col, p.row);
  }, [selectedCell, data]);

  const [fxEditing, setFxEditing] = useState(false);
  const [fxValue, setFxValue] = useState("");

  useEffect(() => {
    setFxValue(fxDisplay);
    setFxEditing(false);
  }, [fxDisplay]);

  const commitFx = useCallback(() => {
    if (!selectedCell) return;
    const p = cellToColRow(selectedCell);
    if (!p) return;
    pushUndo();
    onDataChange(setCellValue(data, p.col, p.row, fxValue));
    setFxEditing(false);
  }, [selectedCell, fxValue, data, onDataChange, pushUndo]);

  return (
    <div className="flex flex-col h-full" onKeyDown={handleKeyDown} tabIndex={0} ref={gridRef}>
      {validationError && (
        <div className="bg-red-100 border-b border-red-300 text-red-700 text-xs px-3 py-1.5">
          {validationError}
        </div>
      )}

      {/* Formula bar */}
      <div className="flex items-center bg-white border-b border-theme-grid px-2 py-1.5 gap-2 theme-transition shrink-0">
        <span className="text-xs font-mono bg-gray-100 border border-gray-300 rounded px-2 py-1 text-gray-600 w-14 text-center">
          {selectedCell || ""}
        </span>
        <span className="text-xs text-gray-400 px-1">fx</span>
        {fxEditing ? (
          <input
            ref={fxInputRef}
            type="text"
            value={fxValue}
            onChange={(e) => setFxValue(e.target.value)}
            onBlur={commitFx}
            onKeyDown={(e) => {
              if (e.key === "Enter") { e.preventDefault(); commitFx(); }
              if (e.key === "Escape") setFxEditing(false);
            }}
            className="flex-1 text-sm font-mono border border-indigo-300 rounded px-2 py-0.5 outline-none focus:ring-1 focus:ring-indigo-400"
          />
        ) : (
          <div
            className="flex-1 text-sm text-gray-700 font-mono truncate cursor-text px-1 py-0.5 rounded hover:bg-gray-50 min-h-[24px]"
            onClick={() => { setFxEditing(true); setTimeout(() => fxInputRef.current?.focus(), 0); }}
          >
            {fxDisplay}
          </div>
        )}
      </div>

      {/* Grid */}
      <div className="flex-1 overflow-auto">
        <table className="border-collapse text-sm select-none">
          <thead className="sticky top-0 z-10">
            <tr>
              <th className="w-10 bg-gray-100 border border-gray-300 text-gray-500 text-xs font-medium py-1.5 sticky left-0 z-20">
                #
              </th>
              {COLS.map((col) => (
                <th
                  key={col}
                  className="bg-gray-100 border border-gray-300 text-gray-500 text-xs font-semibold py-1.5 relative group"
                  style={{ width: colWidths[col] ?? DEFAULT_COL_WIDTH, minWidth: 40 }}
                >
                  <div className="flex items-center justify-center gap-1">
                    <span
                      className="cursor-pointer hover:text-gray-800"
                      onClick={() => handleSort(col)}
                    >
                      {col}
                      {sortState?.col === col && (
                        <span className="ml-0.5 text-[10px]">
                          {sortState.dir === "asc" ? "▲" : "▼"}
                        </span>
                      )}
                    </span>
                    <button
                      className="opacity-0 group-hover:opacity-100 text-[10px] text-gray-400 hover:text-gray-700 ml-1"
                      onClick={(e) => { e.stopPropagation(); setShowFilter(showFilter === col ? null : col); }}
                    >
                      ▼
                    </button>
                  </div>
                  {/* Resize handle */}
                  <div
                    className="absolute right-0 top-0 bottom-0 w-1.5 cursor-col-resize hover:bg-indigo-400"
                    onMouseDown={(e) => { e.preventDefault(); handleResizeStart(col, e.clientX); }}
                  />
                  {/* Filter dropdown */}
                  {showFilter === col && (
                    <div
                      className="absolute top-full left-0 z-30 bg-white border border-gray-300 rounded-lg shadow-lg p-2 min-w-[150px] text-left"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <p className="text-xs font-medium text-gray-600 mb-1.5">Filtrer {col}</p>
                      <div className="max-h-32 overflow-y-auto space-y-1">
                        {colUniqueValues(col).map((val) => (
                          <label key={val} className="flex items-center gap-1.5 text-xs text-gray-700 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={!filterState[col] || filterState[col].has(val)}
                              onChange={(e) => {
                                const current = filterState[col] ? new Set(filterState[col]) : new Set(colUniqueValues(col));
                                if (e.target.checked) current.add(val);
                                else current.delete(val);
                                handleFilter(col, current);
                              }}
                              className="rounded"
                            />
                            {val}
                          </label>
                        ))}
                      </div>
                      <div className="flex gap-1 mt-2 border-t pt-1.5">
                        <button
                          className="text-[10px] text-indigo-600 hover:underline"
                          onClick={() => handleFilter(col, new Set())}
                        >
                          Tout
                        </button>
                        <button
                          className="text-[10px] text-red-500 hover:underline ml-auto"
                          onClick={() => { handleFilter(col, new Set()); setShowFilter(null); }}
                        >
                          Reset
                        </button>
                      </div>
                    </div>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedRows.map((row) => (
              <tr key={row}>
                <td className="bg-gray-50 border border-gray-300 text-center text-xs text-gray-500 font-medium py-0.5 sticky left-0 z-[5]">
                  {row}
                </td>
                {COLS.map((col) => {
                  const id = `${col}${row}`;
                  const isSelected = selectedCell === id;
                  const isEditing = editingCell === id;
                  const rawValue = getCellValue(data, col, row);
                  const displayValue = computedValues[id] ?? "";
                  const hasFormula = isFormula(rawValue);
                  const isError = displayValue.startsWith("#");
                  const cellStyle = styles[id] || {};
                  const condStyle = getConditionalStyle(id, displayValue, conditionalRules);
                  const merged = { ...cellStyle, ...condStyle };
                  const formatted = formatNumber(displayValue, merged.numberFormat);
                  const validation = validations[id];
                  const isAutofillTarget =
                    autofillDragging && autofillTarget !== null && selectedCell &&
                    col === cellToColRow(selectedCell)?.col &&
                    ((autofillTarget > (cellToColRow(selectedCell)?.row ?? 0) && row <= autofillTarget && row > (cellToColRow(selectedCell)?.row ?? 0)) ||
                      (autofillTarget < (cellToColRow(selectedCell)?.row ?? 0) && row >= autofillTarget && row < (cellToColRow(selectedCell)?.row ?? 0)));

                  return (
                    <td
                      key={col}
                      className={`border border-gray-200 px-1.5 py-0.5 cursor-cell h-7 relative ${
                        isSelected ? "outline outline-2 outline-blue-500 bg-blue-50/30 z-[2]" : "hover:bg-gray-50/50"
                      } ${isError ? "text-red-600 text-xs" : ""} ${isAutofillTarget ? "bg-blue-100/50" : ""}`}
                      style={{
                        width: colWidths[col] ?? DEFAULT_COL_WIDTH,
                        fontWeight: merged.bold ? 700 : undefined,
                        fontStyle: merged.italic ? "italic" : undefined,
                        color: merged.color || undefined,
                        backgroundColor: isSelected ? undefined : merged.bgColor || undefined,
                        textAlign: merged.align || (!isNaN(Number(displayValue)) && displayValue !== "" ? "right" : "left"),
                      }}
                      onClick={() => { onSelectCell(id); setShowFilter(null); }}
                      onDoubleClick={() => startEdit(id)}
                    >
                      {isEditing ? (
                        validation?.type === "list" && validation.values ? (
                          <select
                            autoFocus
                            value={editValue}
                            onChange={(e) => { setEditValue(e.target.value); }}
                            onBlur={commitEdit}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") commitEdit();
                              if (e.key === "Escape") setEditingCell(null);
                            }}
                            className="w-full h-full border-none outline-none bg-white text-sm"
                          >
                            <option value="">--</option>
                            {validation.values.map((v) => (
                              <option key={v} value={v}>{v}</option>
                            ))}
                          </select>
                        ) : (
                          <input
                            ref={inputRef}
                            type="text"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            onBlur={commitEdit}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") { e.preventDefault(); e.stopPropagation(); commitEdit(); navigate(0, 1); }
                              if (e.key === "Escape") setEditingCell(null);
                              if (e.key === "Tab") { e.preventDefault(); e.stopPropagation(); commitEdit(); navigate(e.shiftKey ? -1 : 1, 0); }
                            }}
                            className="w-full h-full border-none outline-none bg-transparent text-sm"
                          />
                        )
                      ) : (
                        <span className={`text-sm block truncate ${hasFormula && !isError ? "text-gray-900" : ""}`}>
                          {formatted}
                        </span>
                      )}
                      {/* Autofill handle */}
                      {isSelected && !isEditing && (
                        <div
                          className="absolute bottom-0 right-0 w-2 h-2 bg-blue-600 cursor-crosshair z-[3]"
                          onMouseDown={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            setAutofillDragging(true);
                          }}
                        />
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
