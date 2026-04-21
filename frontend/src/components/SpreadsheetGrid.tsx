"use client";

import { useState, useRef, useCallback, useEffect } from "react";

export type CellData = Record<string, Record<number, string>>;

interface SpreadsheetGridProps {
  data: CellData;
  onDataChange: (data: CellData) => void;
  selectedCell: string | null;
  onSelectCell: (cell: string | null) => void;
}

const COLS = ["A", "B", "C", "D", "E", "F", "G"];
const ROW_COUNT = 20;

export function cellToColRow(cell: string): { col: string; row: number } | null {
  const m = cell.match(/^([A-G])(\d+)$/i);
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
  const m = range.match(/^([A-G])(\d+):([A-G])(\d+)$/i);
  if (!m) return [];
  const colStart = m[1].toUpperCase();
  const rowStart = parseInt(m[2]);
  const colEnd = m[3].toUpperCase();
  const rowEnd = parseInt(m[4]);

  const cells: { col: string; row: number }[] = [];
  const ci = COLS.indexOf(colStart);
  const ce = COLS.indexOf(colEnd);
  for (let c = ci; c <= ce; c++) {
    for (let r = rowStart; r <= rowEnd; r++) {
      cells.push({ col: COLS[c], row: r });
    }
  }
  return cells;
}

export function getNumericValues(data: CellData, range: string): number[] {
  const cells = parseCellRange(range);
  const values: number[] = [];
  for (const { col, row } of cells) {
    const v = getCellValue(data, col, row);
    const n = parseFloat(v);
    if (!isNaN(n)) values.push(n);
  }
  return values;
}

export default function SpreadsheetGrid({
  data,
  onDataChange,
  selectedCell,
  onSelectCell,
}: SpreadsheetGridProps) {
  const [editingCell, setEditingCell] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editingCell && inputRef.current) {
      inputRef.current.focus();
    }
  }, [editingCell]);

  const handleCellClick = useCallback((col: string, row: number) => {
    const cellId = `${col}${row}`;
    onSelectCell(cellId);
  }, [onSelectCell]);

  const handleCellDoubleClick = useCallback((col: string, row: number) => {
    const cellId = `${col}${row}`;
    setEditingCell(cellId);
    setEditValue(getCellValue(data, col, row));
  }, [data]);

  const commitEdit = useCallback(() => {
    if (!editingCell) return;
    const parsed = cellToColRow(editingCell);
    if (parsed) {
      onDataChange(setCellValue(data, parsed.col, parsed.row, editValue));
    }
    setEditingCell(null);
  }, [editingCell, editValue, data, onDataChange]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      commitEdit();
    } else if (e.key === "Escape") {
      setEditingCell(null);
    }
  }, [commitEdit]);

  const fxDisplay = selectedCell
    ? getCellValue(data, ...(() => { const p = cellToColRow(selectedCell); return p ? [p.col, p.row] as const : ["A", 1] as const; })())
    : "";

  return (
    <div className="flex flex-col h-full">
      {/* Formula bar */}
      <div className="flex items-center bg-white border-b border-theme-grid px-2 py-1.5 gap-2 theme-transition">
        <span className="text-xs font-mono bg-gray-100 border border-gray-300 rounded px-2 py-1 text-gray-600 w-12 text-center">
          {selectedCell || ""}
        </span>
        <span className="text-xs text-gray-400">fx</span>
        <span className="text-sm text-gray-700 font-mono flex-1 truncate">
          {fxDisplay}
        </span>
      </div>

      {/* Grid */}
      <div className="flex-1 overflow-auto">
        <table className="border-collapse w-full text-sm select-none">
          <thead>
            <tr>
              <th className="w-10 bg-gray-100 border border-gray-300 text-gray-500 text-xs font-medium py-1.5">#</th>
              {COLS.map((col) => (
                <th
                  key={col}
                  className="bg-gray-100 border border-gray-300 text-gray-500 text-xs font-semibold py-1.5 w-[120px] min-w-[120px]"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: ROW_COUNT }, (_, i) => i + 1).map((row) => (
              <tr key={row}>
                <td className="bg-gray-50 border border-gray-300 text-center text-xs text-gray-500 font-medium py-1">
                  {row}
                </td>
                {COLS.map((col) => {
                  const cellId = `${col}${row}`;
                  const isSelected = selectedCell === cellId;
                  const isEditing = editingCell === cellId;
                  const value = getCellValue(data, col, row);

                  return (
                    <td
                      key={col}
                      className={`border border-gray-200 px-1.5 py-0.5 cursor-cell h-8 ${
                        isSelected
                          ? "outline outline-2 outline-blue-500 bg-blue-50/30"
                          : "hover:bg-gray-50"
                      }`}
                      onClick={() => handleCellClick(col, row)}
                      onDoubleClick={() => handleCellDoubleClick(col, row)}
                    >
                      {isEditing ? (
                        <input
                          ref={inputRef}
                          type="text"
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          onBlur={commitEdit}
                          onKeyDown={handleKeyDown}
                          className="w-full h-full border-none outline-none bg-transparent text-sm"
                        />
                      ) : (
                        <span className={`text-sm ${!isNaN(Number(value)) && value !== "" ? "text-right block" : ""}`}>
                          {value}
                        </span>
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
