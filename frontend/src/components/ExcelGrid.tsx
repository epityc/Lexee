"use client";

import { useState, useCallback } from "react";
import type { FormulaMeta, CalculationResponse } from "@/lib/api";
import { calculate } from "@/lib/api";

interface ExcelGridProps {
  apiKey: string;
  formulaKey: string;
  meta: FormulaMeta;
  onCreditsUpdate: (credits: number) => void;
}

function validateField(raw: string, type: string, required: boolean): string {
  const trimmed = raw.trim();
  if (!trimmed) return required ? "Ce champ est requis." : "";

  if (type === "number") {
    if (isNaN(Number(trimmed))) return "Veuillez entrer un nombre valide (ex: 42 ou 3.14).";
  }

  if (type === "number[]") {
    const parts = trimmed.split(",");
    for (const part of parts) {
      const p = part.trim();
      if (p === "") continue;
      if (isNaN(Number(p))) return `"${p}" n'est pas un nombre valide.`;
    }
  }

  if (type === "json") {
    try {
      JSON.parse(trimmed);
    } catch {
      return "JSON invalide. Verifiez la syntaxe (guillemets, crochets, virgules).";
    }
  }

  return "";
}

export default function ExcelGrid({
  apiKey,
  formulaKey,
  meta,
  onCreditsUpdate,
}: ExcelGridProps) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [result, setResult] = useState<CalculationResponse | null>(null);
  const [globalError, setGlobalError] = useState("");
  const [loading, setLoading] = useState(false);

  const setValue = useCallback((name: string, val: string, type: string, required: boolean) => {
    setValues((prev) => ({ ...prev, [name]: val }));
    setTouched((prev) => ({ ...prev, [name]: true }));
    const err = validateField(val, type, required);
    setErrors((prev) => ({ ...prev, [name]: err }));
  }, []);

  const handleBlur = useCallback((name: string, type: string, required: boolean) => {
    setTouched((prev) => ({ ...prev, [name]: true }));
    const err = validateField(values[name] ?? "", type, required);
    setErrors((prev) => ({ ...prev, [name]: err }));
  }, [values]);

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
    let hasError = false;
    const newErrors: Record<string, string> = {};
    const newTouched: Record<string, boolean> = {};

    for (const v of meta.variables) {
      const raw = values[v.name] ?? "";
      newTouched[v.name] = true;
      const err = validateField(raw, v.type, v.required);
      newErrors[v.name] = err;
      if (err) hasError = true;
    }

    setTouched(newTouched);
    setErrors(newErrors);

    if (hasError) {
      setGlobalError("Corrigez les erreurs dans les champs avant de calculer.");
      return;
    }

    setGlobalError("");
    setResult(null);
    setLoading(true);

    try {
      const variables: Record<string, unknown> = {};
      for (const v of meta.variables) {
        const raw = values[v.name] ?? "";
        const parsed = parseValue(raw, v.type);
        if (parsed !== undefined) variables[v.name] = parsed;
      }

      const res = await calculate(apiKey, formulaKey, variables);
      setResult(res);
      onCreditsUpdate(res.credits_remaining);
    } catch (err) {
      setGlobalError(err instanceof Error ? err.message : "Erreur de calcul");
    } finally {
      setLoading(false);
    }
  }

  const hasErrors = Object.values(errors).some((e) => e !== "");

  return (
    <div className="flex flex-col h-full bg-theme-body theme-transition">
      {/* Formula bar */}
      <div className="flex items-center bg-theme-sidebar border-b border-theme-grid px-6 py-4 gap-4 shadow-sm theme-transition">
        <span className="text-xs font-mono bg-theme-grid-header border border-theme-grid rounded-md px-3 py-1.5 text-gray-500 tracking-wide theme-transition">
          fx
        </span>
        <div className="flex flex-col">
          <span className="text-base font-semibold text-gray-800">
            ={meta.name}(...)
          </span>
          <span className="text-xs text-gray-400 mt-0.5">
            Formule protegee — code source masque
          </span>
        </div>
      </div>

      {/* Column headers */}
      <div className="flex border-b border-theme-grid bg-theme-grid-header text-xs font-semibold text-gray-500 uppercase tracking-wider select-none theme-transition">
        <div className="w-12 text-center border-r border-theme-grid py-2.5"></div>
        <div className="w-[260px] border-r border-theme-grid px-4 py-2.5 text-center">
          Variable
        </div>
        <div className="flex-1 px-4 py-2.5 text-center">Valeur</div>
      </div>

      {/* Input rows */}
      <div className="flex-1 overflow-y-auto">
        {meta.variables.map((v, i) => {
          const fieldError = touched[v.name] ? errors[v.name] : "";
          const hasFieldError = !!fieldError;

          return (
            <div key={v.name} className="group">
              <div
                className={`flex transition-colors ${
                  hasFieldError ? "bg-red-50/60" : "hover:bg-black/[0.02]"
                }`}
              >
                {/* Row number */}
                <div className={`w-12 text-center text-xs py-5 border-r select-none theme-transition ${
                  hasFieldError
                    ? "text-red-400 bg-red-50/40 border-red-200"
                    : "text-gray-400 bg-theme-grid-header border-theme-grid"
                }`}>
                  {i + 1}
                </div>

                {/* Col A — label */}
                <div className={`w-[260px] border-r px-5 py-4 flex flex-col justify-center theme-transition ${
                  hasFieldError ? "border-red-200" : "border-theme-grid"
                }`}>
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm font-medium text-gray-700">{v.label}</span>
                    {v.required && (
                      <span className="text-red-400 text-xs font-bold">*</span>
                    )}
                  </div>
                  <span className="text-[11px] text-gray-400 mt-0.5">
                    {v.type === "number" && "Nombre"}
                    {v.type === "number[]" && "Nombres separes par des virgules"}
                    {v.type === "string" && "Texte"}
                    {v.type === "string[]" && "Textes separes par des virgules"}
                    {v.type === "json" && "Format JSON"}
                  </span>
                </div>

                {/* Col B — input */}
                <div className="flex-1 px-4 py-3 flex flex-col justify-center">
                  {v.type === "json" ? (
                    <textarea
                      value={values[v.name] ?? ""}
                      onChange={(e) => setValue(v.name, e.target.value, v.type, v.required)}
                      onBlur={() => handleBlur(v.name, v.type, v.required)}
                      placeholder={v.placeholder}
                      rows={2}
                      className={`w-full rounded-lg border px-4 py-3 text-xs font-mono
                        resize-y transition-all duration-150
                        ${hasFieldError
                          ? "border-red-300 bg-red-50 text-red-800 focus:outline-none focus:ring-2 focus:ring-red-400 focus:ring-offset-1 placeholder-red-300"
                          : "border-gray-200 bg-white text-gray-800 focus-ring-theme placeholder-gray-400"
                        }`}
                    />
                  ) : (
                    <input
                      type="text"
                      value={values[v.name] ?? ""}
                      onChange={(e) => setValue(v.name, e.target.value, v.type, v.required)}
                      onBlur={() => handleBlur(v.name, v.type, v.required)}
                      placeholder={v.placeholder}
                      className={`w-full rounded-lg border px-4 py-3 text-sm
                        transition-all duration-150
                        ${hasFieldError
                          ? "border-red-300 bg-red-50 text-red-800 focus:outline-none focus:ring-2 focus:ring-red-400 focus:ring-offset-1 placeholder-red-300"
                          : "border-gray-200 bg-white text-gray-800 focus-ring-theme placeholder-gray-400"
                        }`}
                    />
                  )}

                  {hasFieldError && (
                    <div className="flex items-center gap-1.5 mt-2 animate-fade-in">
                      <svg className="w-3.5 h-3.5 text-red-500 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                      <span className="text-xs text-red-600 font-medium">{fieldError}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="border-b border-theme-grid mx-4 theme-transition" />
            </div>
          );
        })}

        {/* Calculate button */}
        <div className="px-6 py-6">
          <button
            onClick={handleCalculate}
            disabled={loading}
            className={`w-full py-3.5 font-semibold rounded-xl text-sm
                       flex items-center justify-center gap-2 shadow-sm
                       ${loading
                         ? "bg-gray-200 text-gray-500 cursor-wait"
                         : hasErrors
                           ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                           : "btn-primary text-white"
                       }`}
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Calcul en cours...
              </>
            ) : (
              "CALCULER"
            )}
          </button>
        </div>

        {/* Global error */}
        {globalError && (
          <div className="mx-6 mb-4 bg-red-50 border border-red-200 text-red-700 px-5 py-4 rounded-xl text-sm flex items-start gap-3">
            <svg className="w-5 h-5 text-red-400 shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <span>{globalError}</span>
          </div>
        )}

        {/* Results — theme-aware */}
        {result && (
          <div className="mx-6 mb-6">
            <div className="rounded-xl result-border border overflow-hidden shadow-sm">
              <div className="flex result-header-bg text-xs font-semibold result-text uppercase tracking-wider select-none border-b result-border theme-transition">
                <div className="w-12 text-center border-r result-border py-3"></div>
                <div className="w-[240px] border-r result-border px-5 py-3 text-center">
                  Resultat
                </div>
                <div className="flex-1 px-5 py-3 text-center">Valeur</div>
              </div>
              {Object.entries(result.result).map(([key, val], i) => (
                <div
                  key={key}
                  className="flex border-b result-border last:border-b-0 result-row-hover transition-colors"
                >
                  <div className="w-12 text-center text-xs py-4 result-text opacity-50 border-r result-border select-none">
                    R{i + 1}
                  </div>
                  <div className="w-[240px] border-r result-border px-5 py-4 text-sm result-text font-medium">
                    {key}
                  </div>
                  <div className="flex-1 px-5 py-4 text-sm result-text font-semibold font-mono">
                    {typeof val === "object" ? JSON.stringify(val, null, 1) : String(val)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
