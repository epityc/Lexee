import type { CellData } from "@/components/SpreadsheetGrid";
import { COLS } from "@/components/SpreadsheetGrid";

function getMaxRow(data: CellData): number {
  let max = 0;
  for (const col of Object.keys(data)) {
    for (const r of Object.keys(data[col])) {
      const n = Number(r);
      if (n > max) max = n;
    }
  }
  return max;
}

function getUsedCols(data: CellData): string[] {
  return COLS.filter((c) => data[c] && Object.keys(data[c]).length > 0);
}

function shiftRows(data: CellData, validRows: number[], usedCols: string[]): CellData {
  const newData: CellData = {};
  validRows.forEach((srcRow, i) => {
    const destRow = i + 1;
    for (const col of usedCols) {
      const val = data[col]?.[srcRow];
      if (val !== undefined && val !== "") {
        if (!newData[col]) newData[col] = {};
        newData[col][destRow] = val;
      }
    }
  });
  return newData;
}

export function removeEmptyRows(data: CellData): CellData {
  const usedCols = getUsedCols(data);
  if (usedCols.length === 0) return data;
  const maxRow = getMaxRow(data);
  const validRows: number[] = [];
  for (let r = 1; r <= maxRow; r++) {
    const isEmpty = usedCols.every((c) => !data[c]?.[r] || data[c][r].trim() === "");
    if (!isEmpty) validRows.push(r);
  }
  return shiftRows(data, validRows, usedCols);
}

export function removeDuplicates(data: CellData, col: string): CellData {
  const usedCols = getUsedCols(data);
  const maxRow = getMaxRow(data);
  const seen = new Set<string>();
  const validRows: number[] = [];
  for (let r = 1; r <= maxRow; r++) {
    const val = data[col]?.[r] ?? "";
    if (!seen.has(val)) {
      seen.add(val);
      validRows.push(r);
    }
  }
  return shiftRows(data, validRows, usedCols);
}

function normalizePhone(raw: string): string {
  const digits = raw.replace(/[^\d+]/g, "");
  let national = "";
  if (digits.startsWith("+33")) {
    national = digits.slice(3);
  } else if (digits.startsWith("0033")) {
    national = digits.slice(4);
  } else if (digits.startsWith("33") && digits.length >= 11) {
    national = digits.slice(2);
  } else if (digits.startsWith("0")) {
    national = digits.slice(1);
  } else {
    return raw;
  }
  // strip leading spaces/zeros that crept in
  national = national.replace(/\s/g, "");
  if (national.length !== 9) return raw;
  const groups = [
    national[0],
    national.slice(1, 3),
    national.slice(3, 5),
    national.slice(5, 7),
    national.slice(7, 9),
  ];
  return `+33 ${groups.join(" ")}`;
}

export function normalizePhones(data: CellData, col: string): CellData {
  const colData = data[col] ?? {};
  const newCol: Record<number, string> = {};
  for (const [rowStr, val] of Object.entries(colData)) {
    newCol[Number(rowStr)] = val.trim() ? normalizePhone(val) : val;
  }
  return { ...data, [col]: newCol };
}

export function splitNameColumn(data: CellData, col: string, nextCol: string): CellData {
  const colData = data[col] ?? {};
  const newCol: Record<number, string> = {};
  const newNext: Record<number, string> = { ...(data[nextCol] ?? {}) };
  for (const [rowStr, val] of Object.entries(colData)) {
    const row = Number(rowStr);
    const spaceIdx = val.indexOf(" ");
    if (spaceIdx === -1) {
      newCol[row] = val;
    } else {
      newCol[row] = val.slice(0, spaceIdx);
      newNext[row] = val.slice(spaceIdx + 1);
    }
  }
  return { ...data, [col]: newCol, [nextCol]: newNext };
}

export function fixCasing(data: CellData, col: string): CellData {
  const colData = data[col] ?? {};
  const newCol: Record<number, string> = {};
  for (const [rowStr, val] of Object.entries(colData)) {
    newCol[Number(rowStr)] = val.trim()
      ? val.toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase())
      : val;
  }
  return { ...data, [col]: newCol };
}
