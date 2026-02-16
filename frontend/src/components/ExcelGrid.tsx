"use client";

import { useState } from "react";
import type { FormulaMeta, CalculationResponse } from "@/lib/api";
import { calculate } from "@/lib/api";

interface ExcelGridProps {
  apiKey: string;
  formulaKey: string;
  meta: FormulaMeta;
  onCreditsUpdate: (credits: number) => void;
}

export default function ExcelGrid({
  apiKey,
  formulaKey,
  meta,
  onCreditsUpdate,
}: ExcelGridProps) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [result, setResult] = useState<CalculationResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function setValue(name: string, val: string) {
    setValues((prev) => ({ ...prev, [name]: val }));
  }

  function parseValue(raw: string, type: string): unknown {
    if (!raw.trim()) return undefined;

    if (type === "number") return parseFloat(raw);
    if (type === "number[]")
      return raw.split(",").map((s) => parseFloat(s.trim()));
    if (type === "string[]")
      return raw.split(",").map((s) => s.trim());
    if (type === "json") return JSON.parse(raw);
    return raw;
  }

  async function handleCalculate() {
    setError("");
    setResult(null);
    setLoading(true);

    try {
      const variables: Record<string, unknown> = {};
      for (const v of meta.variables) {
        const raw = values[v.name] ?? "";
        if (v.required && !raw.trim()) {
          setError(`Le champ "${v.label}" est requis.`);
          setLoading(false);
          return;
        }
        const parsed = parseValue(raw, v.type);
        if (parsed !== undefined) variables[v.name] = parsed;
      }

      const res = await calculate(apiKey, formulaKey, variables);
      setResult(res);
      onCreditsUpdate(res.credits_remaining);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur de calcul");
    } finally {
      setLoading(false);
    }
  }

  const colA = "w-[220px]";
  const colB = "flex-1";

  return (
    <div className="flex flex-col h-full">
      {/* Formula bar */}
      <div className="flex items-center bg-gray-50 border-b border-gray-300 px-3 py-2 gap-3">
        <span className="text-xs font-mono bg-white border border-gray-300 rounded px-2 py-1 text-gray-500">
          fx
        </span>
        <span className="text-sm font-semibold text-gray-800">
          ={meta.name}(...)
        </span>
        <span className="text-xs text-gray-400 ml-auto">
          Formule protegee — code source masque
        </span>
      </div>

      {/* Column headers */}
      <div className="flex border-b border-gray-400 bg-gray-100 text-xs font-semibold text-gray-600 select-none">
        <div className="w-10 text-center border-r border-gray-300 py-1"></div>
        <div className={`${colA} border-r border-gray-300 px-2 py-1 text-center`}>
          A
        </div>
        <div className={`${colB} px-2 py-1 text-center`}>B</div>
      </div>

      {/* Input rows */}
      <div className="flex-1 overflow-y-auto">
        {meta.variables.map((v, i) => (
          <div
            key={v.name}
            className="flex border-b border-gray-200 hover:bg-blue-50/30 transition-colors"
          >
            {/* Row number */}
            <div className="w-10 text-center text-xs text-gray-400 py-2 bg-gray-50 border-r border-gray-200 select-none">
              {i + 1}
            </div>
            {/* Col A — label */}
            <div
              className={`${colA} border-r border-gray-200 cell-readonly flex items-center gap-1`}
            >
              <span>{v.label}</span>
              {v.required && <span className="text-red-400 text-xs">*</span>}
            </div>
            {/* Col B — input */}
            <div className={`${colB}`}>
              {v.type === "json" ? (
                <textarea
                  value={values[v.name] ?? ""}
                  onChange={(e) => setValue(v.name, e.target.value)}
                  placeholder={v.placeholder}
                  rows={2}
                  className="cell-input resize-y font-mono text-xs"
                />
              ) : (
                <input
                  type="text"
                  value={values[v.name] ?? ""}
                  onChange={(e) => setValue(v.name, e.target.value)}
                  placeholder={v.placeholder}
                  className="cell-input"
                />
              )}
            </div>
          </div>
        ))}

        {/* Calculate button row */}
        <div className="px-4 py-4 bg-gray-50 border-b border-gray-300">
          <button
            onClick={handleCalculate}
            disabled={loading}
            className="w-full py-2.5 bg-green-600 hover:bg-green-700 disabled:bg-gray-300
                       text-white font-semibold rounded-lg transition-colors text-sm
                       flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <svg
                  className="animate-spin h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                Calcul en cours...
              </>
            ) : (
              "CALCULER"
            )}
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="mx-4 mt-3 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="mt-1">
            <div className="flex border-b border-gray-400 bg-green-50 text-xs font-semibold text-green-800 select-none">
              <div className="w-10 text-center border-r border-gray-300 py-1"></div>
              <div
                className={`${colA} border-r border-gray-300 px-2 py-1 text-center`}
              >
                RESULTAT
              </div>
              <div className={`${colB} px-2 py-1 text-center`}>VALEUR</div>
            </div>
            {Object.entries(result.result).map(([key, val], i) => (
              <div
                key={key}
                className="flex border-b border-green-100 hover:bg-green-50/50"
              >
                <div className="w-10 text-center text-xs text-green-400 py-2 bg-green-50/50 border-r border-green-100 select-none">
                  R{i + 1}
                </div>
                <div
                  className={`${colA} border-r border-green-100 cell-readonly text-green-700`}
                >
                  {key}
                </div>
                <div className={`${colB} cell-result`}>
                  {typeof val === "object" ? JSON.stringify(val) : String(val)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
