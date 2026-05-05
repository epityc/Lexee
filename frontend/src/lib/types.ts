export interface CellStyle {
  bold?: boolean;
  italic?: boolean;
  color?: string;
  bgColor?: string;
  align?: "left" | "center" | "right";
  numberFormat?: "general" | "number" | "currency" | "percent" | "date";
}

export interface ValidationRule {
  type: "list" | "number" | "text";
  values?: string[];
  min?: number;
  max?: number;
}

export interface ConditionalRule {
  id: string;
  range: string;
  condition: "gt" | "lt" | "eq" | "neq" | "contains" | "empty" | "notEmpty";
  value?: string;
  style: CellStyle;
}

export interface Sheet {
  id: string;
  name: string;
  data: Record<string, Record<number, string>>;
  styles: Record<string, CellStyle>;
  validations: Record<string, ValidationRule>;
  conditionalRules: ConditionalRule[];
  colWidths: Record<string, number>;
  sortState: { col: string; dir: "asc" | "desc" } | null;
  filterState: Record<string, string[]>;
}

export type CellData = Record<string, Record<number, string>>;
export type CellFormulas = Record<string, string>;
export type CellStyles = Record<string, CellStyle>;

export function createEmptySheet(id: string, name: string): Sheet {
  return {
    id,
    name,
    data: {},
    styles: {},
    validations: {},
    conditionalRules: [],
    colWidths: {},
    sortState: null,
    filterState: {},
  };
}
