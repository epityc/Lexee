type CellStore = Record<string, string>;
type CellRef = { col: number; row: number };

const COL_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

export function colToIndex(col: string): number {
  let n = 0;
  for (const c of col.toUpperCase()) n = n * 26 + c.charCodeAt(0) - 64;
  return n - 1;
}

export function indexToCol(i: number): string {
  let s = "";
  let n = i + 1;
  while (n > 0) {
    n--;
    s = COL_LETTERS[n % 26] + s;
    n = Math.floor(n / 26);
  }
  return s;
}

export function cellId(col: number, row: number): string {
  return `${indexToCol(col)}${row + 1}`;
}

export function parseRef(ref: string): CellRef | null {
  const m = ref.match(/^([A-Z]+)(\d+)$/i);
  if (!m) return null;
  return { col: colToIndex(m[1]), row: parseInt(m[2]) - 1 };
}

function expandRange(a: CellRef, b: CellRef): CellRef[] {
  const refs: CellRef[] = [];
  const c1 = Math.min(a.col, b.col), c2 = Math.max(a.col, b.col);
  const r1 = Math.min(a.row, b.row), r2 = Math.max(a.row, b.row);
  for (let c = c1; c <= c2; c++)
    for (let r = r1; r <= r2; r++)
      refs.push({ col: c, row: r });
  return refs;
}

function resolveValues(args: string, cells: CellStore, evaluate: (expr: string, cells: CellStore) => number | string): number[] {
  const parts = splitArgs(args);
  const nums: number[] = [];
  for (const part of parts) {
    const trimmed = part.trim();
    const rangeMatch = trimmed.match(/^([A-Z]+\d+):([A-Z]+\d+)$/i);
    if (rangeMatch) {
      const a = parseRef(rangeMatch[1]);
      const b = parseRef(rangeMatch[2]);
      if (a && b) {
        for (const ref of expandRange(a, b)) {
          const raw = cells[cellId(ref.col, ref.row)] ?? "";
          if (raw === "") continue;
          const v = raw.startsWith("=") ? evaluate(raw, cells) : parseFloat(raw);
          if (typeof v === "number" && !isNaN(v)) nums.push(v);
        }
      }
    } else {
      const singleRef = parseRef(trimmed);
      if (singleRef) {
        const raw = cells[cellId(singleRef.col, singleRef.row)] ?? "";
        if (raw !== "") {
          const v = raw.startsWith("=") ? evaluate(raw, cells) : parseFloat(raw);
          if (typeof v === "number" && !isNaN(v)) nums.push(v);
        }
      } else {
        const n = parseFloat(trimmed);
        if (!isNaN(n)) nums.push(n);
      }
    }
  }
  return nums;
}

function splitArgs(s: string): string[] {
  const args: string[] = [];
  let depth = 0, current = "";
  for (const ch of s) {
    if (ch === "(") { depth++; current += ch; }
    else if (ch === ")") { depth--; current += ch; }
    else if (ch === ";" && depth === 0) { args.push(current); current = ""; }
    else if (ch === "," && depth === 0) { args.push(current); current = ""; }
    else { current += ch; }
  }
  if (current) args.push(current);
  return args;
}

function evalArg(arg: string, cells: CellStore): number | string {
  const trimmed = arg.trim();
  if (trimmed.startsWith("\"") && trimmed.endsWith("\"")) return trimmed.slice(1, -1);
  if (trimmed.startsWith("'") && trimmed.endsWith("'")) return trimmed.slice(1, -1);
  const ref = parseRef(trimmed);
  if (ref) {
    const raw = cells[cellId(ref.col, ref.row)] ?? "";
    if (raw.startsWith("=")) return evaluate(raw, cells);
    const n = parseFloat(raw);
    return isNaN(n) ? raw : n;
  }
  const n = parseFloat(trimmed);
  if (!isNaN(n)) return n;
  if (trimmed.startsWith("=")) return evaluate(trimmed, cells);
  return trimmed;
}

const FUNCTIONS: Record<string, (args: string, cells: CellStore) => number | string> = {
  SOMME: (args, cells) => {
    const vals = resolveValues(args, cells, evaluate);
    return vals.reduce((a, b) => a + b, 0);
  },
  SUM: (args, cells) => FUNCTIONS.SOMME(args, cells),
  MOYENNE: (args, cells) => {
    const vals = resolveValues(args, cells, evaluate);
    return vals.length === 0 ? 0 : vals.reduce((a, b) => a + b, 0) / vals.length;
  },
  AVERAGE: (args, cells) => FUNCTIONS.MOYENNE(args, cells),
  MIN: (args, cells) => {
    const vals = resolveValues(args, cells, evaluate);
    return vals.length === 0 ? 0 : Math.min(...vals);
  },
  MAX: (args, cells) => {
    const vals = resolveValues(args, cells, evaluate);
    return vals.length === 0 ? 0 : Math.max(...vals);
  },
  NB: (args, cells) => resolveValues(args, cells, evaluate).length,
  COUNT: (args, cells) => FUNCTIONS.NB(args, cells),
  NBVAL: (args, cells) => {
    const parts = splitArgs(args);
    let count = 0;
    for (const part of parts) {
      const trimmed = part.trim();
      const rangeMatch = trimmed.match(/^([A-Z]+\d+):([A-Z]+\d+)$/i);
      if (rangeMatch) {
        const a = parseRef(rangeMatch[1]);
        const b = parseRef(rangeMatch[2]);
        if (a && b) {
          for (const ref of expandRange(a, b)) {
            const raw = cells[cellId(ref.col, ref.row)] ?? "";
            if (raw !== "") count++;
          }
        }
      }
    }
    return count;
  },
  COUNTA: (args, cells) => FUNCTIONS.NBVAL(args, cells),
  MEDIANE: (args, cells) => {
    const vals = resolveValues(args, cells, evaluate).sort((a, b) => a - b);
    if (vals.length === 0) return 0;
    const mid = Math.floor(vals.length / 2);
    return vals.length % 2 ? vals[mid] : (vals[mid - 1] + vals[mid]) / 2;
  },
  MEDIAN: (args, cells) => FUNCTIONS.MEDIANE(args, cells),
  ECARTYPE: (args, cells) => {
    const vals = resolveValues(args, cells, evaluate);
    if (vals.length < 2) return 0;
    const mean = vals.reduce((a, b) => a + b, 0) / vals.length;
    const variance = vals.reduce((sum, v) => sum + (v - mean) ** 2, 0) / (vals.length - 1);
    return Math.sqrt(variance);
  },
  STDEV: (args, cells) => FUNCTIONS.ECARTYPE(args, cells),
  VARIANCE: (args, cells) => {
    const vals = resolveValues(args, cells, evaluate);
    if (vals.length < 2) return 0;
    const mean = vals.reduce((a, b) => a + b, 0) / vals.length;
    return vals.reduce((sum, v) => sum + (v - mean) ** 2, 0) / (vals.length - 1);
  },
  VAR: (args, cells) => FUNCTIONS.VARIANCE(args, cells),
  ABS: (args, cells) => Math.abs(Number(evalArg(args, cells))),
  ARRONDI: (args, cells) => {
    const parts = splitArgs(args);
    const val = Number(evalArg(parts[0], cells));
    const dec = parts[1] ? Number(evalArg(parts[1], cells)) : 0;
    const f = Math.pow(10, dec);
    return Math.round(val * f) / f;
  },
  ROUND: (args, cells) => FUNCTIONS.ARRONDI(args, cells),
  ENT: (args, cells) => Math.floor(Number(evalArg(args, cells))),
  INT: (args, cells) => FUNCTIONS.ENT(args, cells),
  PLAFOND: (args, cells) => Math.ceil(Number(evalArg(args, cells))),
  CEILING: (args, cells) => FUNCTIONS.PLAFOND(args, cells),
  PLANCHER: (args, cells) => Math.floor(Number(evalArg(args, cells))),
  FLOOR: (args, cells) => FUNCTIONS.PLANCHER(args, cells),
  PUISSANCE: (args, cells) => {
    const parts = splitArgs(args);
    return Math.pow(Number(evalArg(parts[0], cells)), Number(evalArg(parts[1], cells)));
  },
  POWER: (args, cells) => FUNCTIONS.PUISSANCE(args, cells),
  RACINE: (args, cells) => Math.sqrt(Number(evalArg(args, cells))),
  SQRT: (args, cells) => FUNCTIONS.RACINE(args, cells),
  LOG: (args, cells) => {
    const parts = splitArgs(args);
    const val = Number(evalArg(parts[0], cells));
    const base = parts[1] ? Number(evalArg(parts[1], cells)) : 10;
    return Math.log(val) / Math.log(base);
  },
  LN: (args, cells) => Math.log(Number(evalArg(args, cells))),
  EXP: (args, cells) => Math.exp(Number(evalArg(args, cells))),
  MOD: (args, cells) => {
    const parts = splitArgs(args);
    return Number(evalArg(parts[0], cells)) % Number(evalArg(parts[1], cells));
  },
  PRODUIT: (args, cells) => {
    const vals = resolveValues(args, cells, evaluate);
    return vals.reduce((a, b) => a * b, 1);
  },
  PRODUCT: (args, cells) => FUNCTIONS.PRODUIT(args, cells),
  PI: () => Math.PI,
  ALEA: () => Math.random(),
  RAND: () => Math.random(),
  SI: (args, cells) => {
    const parts = splitArgs(args);
    const condition = evalCondition(parts[0].trim(), cells);
    return condition
      ? evalArg(parts[1] ?? "0", cells)
      : evalArg(parts[2] ?? "0", cells);
  },
  IF: (args, cells) => FUNCTIONS.SI(args, cells),
  ET: (args, cells) => {
    const parts = splitArgs(args);
    return parts.every(p => {
      const v = evalArg(p, cells);
      return v !== 0 && v !== "";
    }) ? 1 : 0;
  },
  AND: (args, cells) => FUNCTIONS.ET(args, cells),
  OU: (args, cells) => {
    const parts = splitArgs(args);
    return parts.some(p => {
      const v = evalArg(p, cells);
      return v !== 0 && v !== "";
    }) ? 1 : 0;
  },
  OR: (args, cells) => FUNCTIONS.OU(args, cells),
  NON: (args, cells) => evalArg(args, cells) ? 0 : 1,
  NOT: (args, cells) => FUNCTIONS.NON(args, cells),
  CONCATENER: (args, cells) => {
    const parts = splitArgs(args);
    return parts.map(p => String(evalArg(p, cells))).join("");
  },
  CONCATENATE: (args, cells) => FUNCTIONS.CONCATENER(args, cells),
  GAUCHE: (args, cells) => {
    const parts = splitArgs(args);
    const s = String(evalArg(parts[0], cells));
    const n = parts[1] ? Number(evalArg(parts[1], cells)) : 1;
    return s.substring(0, n);
  },
  LEFT: (args, cells) => FUNCTIONS.GAUCHE(args, cells),
  DROITE: (args, cells) => {
    const parts = splitArgs(args);
    const s = String(evalArg(parts[0], cells));
    const n = parts[1] ? Number(evalArg(parts[1], cells)) : 1;
    return s.substring(s.length - n);
  },
  RIGHT: (args, cells) => FUNCTIONS.DROITE(args, cells),
  NBCAR: (args, cells) => String(evalArg(args, cells)).length,
  LEN: (args, cells) => FUNCTIONS.NBCAR(args, cells),
  MAJUSCULE: (args, cells) => String(evalArg(args, cells)).toUpperCase(),
  UPPER: (args, cells) => FUNCTIONS.MAJUSCULE(args, cells),
  MINUSCULE: (args, cells) => String(evalArg(args, cells)).toLowerCase(),
  LOWER: (args, cells) => FUNCTIONS.MINUSCULE(args, cells),
  SUPPRESPACE: (args, cells) => String(evalArg(args, cells)).trim(),
  TRIM: (args, cells) => FUNCTIONS.SUPPRESPACE(args, cells),
  AUJOURDHUI: () => new Date().toISOString().slice(0, 10),
  TODAY: () => new Date().toISOString().slice(0, 10),
  MAINTENANT: () => new Date().toISOString().slice(0, 19).replace("T", " "),
  NOW: () => new Date().toISOString().slice(0, 19).replace("T", " "),
  GRANDE_VALEUR: (args, cells) => {
    const parts = splitArgs(args);
    const vals = resolveValues(parts[0], cells, evaluate).sort((a, b) => b - a);
    const k = Number(evalArg(parts[1], cells));
    return vals[k - 1] ?? "#N/A";
  },
  LARGE: (args, cells) => FUNCTIONS.GRANDE_VALEUR(args, cells),
  PETITE_VALEUR: (args, cells) => {
    const parts = splitArgs(args);
    const vals = resolveValues(parts[0], cells, evaluate).sort((a, b) => a - b);
    const k = Number(evalArg(parts[1], cells));
    return vals[k - 1] ?? "#N/A";
  },
  SMALL: (args, cells) => FUNCTIONS.PETITE_VALEUR(args, cells),
  RANG: (args, cells) => {
    const parts = splitArgs(args);
    const val = Number(evalArg(parts[0], cells));
    const vals = resolveValues(parts[1], cells, evaluate).sort((a, b) => b - a);
    const idx = vals.indexOf(val);
    return idx === -1 ? "#N/A" : idx + 1;
  },
  RANK: (args, cells) => FUNCTIONS.RANG(args, cells),
  NB_SI: (args, cells) => {
    const parts = splitArgs(args);
    const vals = resolveValues(parts[0], cells, evaluate);
    const crit = Number(evalArg(parts[1], cells));
    return vals.filter(v => v === crit).length;
  },
  COUNTIF: (args, cells) => FUNCTIONS.NB_SI(args, cells),
  SOMME_SI: (args, cells) => {
    const parts = splitArgs(args);
    const range = parts[0].trim();
    const critRaw = parts[1].trim();
    const sumRange = parts[2] ? parts[2].trim() : range;
    const rangeMatch = range.match(/^([A-Z]+\d+):([A-Z]+\d+)$/i);
    const sumMatch = sumRange.match(/^([A-Z]+\d+):([A-Z]+\d+)$/i);
    if (!rangeMatch || !sumMatch) return "#ERROR";
    const a1 = parseRef(rangeMatch[1]), b1 = parseRef(rangeMatch[2]);
    const a2 = parseRef(sumMatch[1]), b2 = parseRef(sumMatch[2]);
    if (!a1 || !b1 || !a2 || !b2) return "#ERROR";
    const critRefs = expandRange(a1, b1);
    const sumRefs = expandRange(a2, b2);
    const critVal = Number(evalArg(critRaw, cells));
    let total = 0;
    for (let i = 0; i < critRefs.length && i < sumRefs.length; i++) {
      const cv = cells[cellId(critRefs[i].col, critRefs[i].row)] ?? "";
      const sv = cells[cellId(sumRefs[i].col, sumRefs[i].row)] ?? "";
      const cn = parseFloat(cv.startsWith("=") ? String(evaluate(cv, cells)) : cv);
      const sn = parseFloat(sv.startsWith("=") ? String(evaluate(sv, cells)) : sv);
      if (!isNaN(cn) && cn === critVal && !isNaN(sn)) total += sn;
    }
    return total;
  },
  SUMIF: (args, cells) => FUNCTIONS.SOMME_SI(args, cells),
};

function evalCondition(expr: string, cells: CellStore): boolean {
  const ops = [">=", "<=", "<>", "!=", ">", "<", "="] as const;
  for (const op of ops) {
    const idx = expr.indexOf(op);
    if (idx !== -1) {
      const left = evalArg(expr.substring(0, idx), cells);
      const right = evalArg(expr.substring(idx + op.length), cells);
      const l = Number(left), r = Number(right);
      const ln = isNaN(l) ? left : l;
      const rn = isNaN(r) ? right : r;
      switch (op) {
        case ">=": return ln >= rn;
        case "<=": return ln <= rn;
        case "<>": case "!=": return ln !== rn;
        case ">": return ln > rn;
        case "<": return ln < rn;
        case "=": return ln === rn;
      }
    }
  }
  const v = evalArg(expr, cells);
  return v !== 0 && v !== "";
}

function evaluateExpression(expr: string, cells: CellStore): number | string {
  const trimmed = expr.trim();

  const funcMatch = trimmed.match(/^([A-Za-z_]+)\(([\s\S]+)\)$/);
  if (funcMatch) {
    const fname = funcMatch[1].toUpperCase();
    const fargs = funcMatch[2];
    const fn = FUNCTIONS[fname];
    if (fn) return fn(fargs, cells);
    return `#NAME?`;
  }

  const ref = parseRef(trimmed);
  if (ref) {
    const raw = cells[cellId(ref.col, ref.row)] ?? "";
    if (raw.startsWith("=")) return evaluate(raw, cells);
    const n = parseFloat(raw);
    return isNaN(n) ? raw : n;
  }

  if (trimmed.startsWith("\"") && trimmed.endsWith("\"")) return trimmed.slice(1, -1);

  const num = parseFloat(trimmed);
  if (!isNaN(num) && String(num) === trimmed) return num;

  const addParts = splitByOps(trimmed, ["+", "-"]);
  if (addParts.length > 1) {
    let result = Number(evaluateExpression(addParts[0].expr, cells));
    for (let i = 1; i < addParts.length; i++) {
      const val = Number(evaluateExpression(addParts[i].expr, cells));
      if (addParts[i].op === "+") result += val;
      else result -= val;
    }
    return result;
  }

  const mulParts = splitByOps(trimmed, ["*", "/"]);
  if (mulParts.length > 1) {
    let result = Number(evaluateExpression(mulParts[0].expr, cells));
    for (let i = 1; i < mulParts.length; i++) {
      const val = Number(evaluateExpression(mulParts[i].expr, cells));
      if (mulParts[i].op === "*") result *= val;
      else if (val !== 0) result /= val;
      else return "#DIV/0!";
    }
    return result;
  }

  return isNaN(Number(trimmed)) ? trimmed : Number(trimmed);
}

function splitByOps(expr: string, ops: string[]): { op: string; expr: string }[] {
  const parts: { op: string; expr: string }[] = [];
  let depth = 0, current = "", lastOp = "";
  for (let i = 0; i < expr.length; i++) {
    const ch = expr[i];
    if (ch === "(") { depth++; current += ch; }
    else if (ch === ")") { depth--; current += ch; }
    else if (depth === 0 && ops.includes(ch) && i > 0) {
      parts.push({ op: lastOp, expr: current });
      current = "";
      lastOp = ch;
    } else {
      current += ch;
    }
  }
  if (current) parts.push({ op: lastOp, expr: current });
  return parts.length > 1 ? parts : [];
}

export function evaluate(formula: string, cells: CellStore): number | string {
  if (!formula.startsWith("=")) return formula;
  try {
    return evaluateExpression(formula.substring(1), cells);
  } catch {
    return "#ERROR!";
  }
}

export function formatResult(value: number | string): string {
  if (typeof value === "number") {
    if (!isFinite(value)) return "#ERROR!";
    return Number.isInteger(value) ? value.toString() : parseFloat(value.toFixed(8)).toString();
  }
  return String(value);
}

export function isFormula(value: string): boolean {
  return value.startsWith("=");
}

export function getDependencies(formula: string): string[] {
  if (!formula.startsWith("=")) return [];
  const deps: string[] = [];
  const expr = formula.substring(1);
  const refPattern = /([A-Z]+\d+)/gi;
  let match;
  while ((match = refPattern.exec(expr)) !== null) {
    deps.push(match[1].toUpperCase());
  }
  return [...new Set(deps)];
}
