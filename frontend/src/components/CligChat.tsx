"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { calculate, FORMULA_NAME_MAP } from "@/lib/api";
import type { CellData } from "./SpreadsheetGrid";
import { getNumericValues, getCellValue, cellToColRow, parseCellRange } from "./SpreadsheetGrid";

interface CligChatProps {
  apiKey: string;
  gridData: CellData;
  selectedCell: string | null;
  onInsertValue: (cell: string, value: string, formula: string) => void;
  onCreditsUpdate: (credits: number) => void;
  engineOnline: boolean;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  formula?: string;
  computedValue?: string;
  targetCell?: string;
  isError?: boolean;
}

function detectFormulaIntent(
  prompt: string,
  gridData: CellData,
  selectedCell: string | null
): { formulaName: string; range: string; targetCell: string; description: string } | null {
  const lower = prompt.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");

  let formulaName = "";
  let description = "";

  if (lower.includes("moyenne") || lower.includes("average")) {
    formulaName = "MOYENNE";
    description = "Calcule la moyenne des valeurs numeriques";
  } else if (lower.includes("somme") || lower.includes("sum") || lower.includes("total") || lower.includes("additionn")) {
    formulaName = "SOMME";
    description = "Calcule la somme des valeurs numeriques";
  } else if (lower.includes("minimum") || lower.match(/\bmin\b/)) {
    formulaName = "MIN";
    description = "Trouve la valeur minimale";
  } else if (lower.includes("maximum") || lower.match(/\bmax\b/)) {
    formulaName = "MAX";
    description = "Trouve la valeur maximale";
  } else if (lower.includes("compt") || lower.includes("nombre") || lower.includes("count") || lower.includes("combien")) {
    formulaName = "NB";
    description = "Compte les valeurs numeriques";
  } else if (lower.includes("median")) {
    formulaName = "MEDIANE";
    description = "Calcule la mediane";
  } else {
    return null;
  }

  let dataRange = "";
  let dataCol = "";
  let lastDataRow = 0;

  const rangeMatch = prompt.match(/([A-G])(\d+):([A-G])(\d+)/i);
  if (rangeMatch) {
    dataRange = `${rangeMatch[1].toUpperCase()}${rangeMatch[2]}:${rangeMatch[3].toUpperCase()}${rangeMatch[4]}`;
    const endParsed = cellToColRow(`${rangeMatch[3].toUpperCase()}${rangeMatch[4]}`);
    if (endParsed) {
      lastDataRow = endParsed.row;
      dataCol = endParsed.col;
    }
  }

  if (!dataRange) {
    const colMatch = lower.match(/colonne\s+([a-g])/i);
    if (colMatch) {
      dataCol = colMatch[1].toUpperCase();
    } else {
      for (const col of ["A", "B", "C", "D", "E", "F", "G"]) {
        let count = 0;
        for (let r = 1; r <= 20; r++) {
          const v = getCellValue(gridData, col, r);
          if (v !== "" && !isNaN(Number(v))) count++;
        }
        if (count > 0) {
          dataCol = col;
          break;
        }
      }
    }

    if (dataCol) {
      let firstRow = 0;
      lastDataRow = 0;
      for (let r = 1; r <= 20; r++) {
        const v = getCellValue(gridData, dataCol, r);
        if (v !== "") {
          if (!firstRow) firstRow = r;
          lastDataRow = r;
        }
      }
      if (firstRow) {
        dataRange = `${dataCol}${firstRow}:${dataCol}${lastDataRow}`;
      }
    }
  }

  if (!dataRange) return null;

  const rowsMatch = prompt.match(/lignes?\s+(\d+)\s*(?:a|à)\s*(\d+)/i);
  if (rowsMatch && dataCol) {
    dataRange = `${dataCol}${rowsMatch[1]}:${dataCol}${rowsMatch[2]}`;
    lastDataRow = parseInt(rowsMatch[2]);
  }

  let targetCell = selectedCell || "";
  if (!targetCell && dataCol) {
    targetCell = `${dataCol}${lastDataRow + 1}`;
  }

  const rangeCells = parseCellRange(dataRange);
  const colsInRange = [...new Set(rangeCells.map(c => c.col))];
  const desc = colsInRange.length === 1
    ? `${description} de la colonne ${colsInRange[0]} (lignes ${rangeCells[0]?.row} a ${rangeCells[rangeCells.length - 1]?.row})`
    : `${description} de la plage ${dataRange}`;

  return {
    formulaName,
    range: dataRange,
    targetCell,
    description: desc,
  };
}

export default function CligChat({
  apiKey,
  gridData,
  selectedCell,
  onInsertValue,
  onCreditsUpdate,
  engineOnline,
}: CligChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = useCallback(async () => {
    const prompt = input.trim();
    if (!prompt) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: prompt }]);

    const intent = detectFormulaIntent(prompt, gridData, selectedCell);

    if (!intent) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Je n'ai pas compris la formule demandee. Essayez : \"Calcule la moyenne\", \"Fais la somme\", \"Trouve le minimum\", \"Compte les valeurs\".",
        },
      ]);
      return;
    }

    if (!engineOnline) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `${intent.description}.\n\nFormule : =${intent.formulaName}(${intent.range})\n\nLe moteur est hors ligne. Impossible de calculer le resultat.`,
          formula: `=${intent.formulaName}(${intent.range})`,
          targetCell: intent.targetCell,
          isError: true,
        },
      ]);
      return;
    }

    setLoading(true);

    try {
      const values = getNumericValues(gridData, intent.range);
      if (values.length === 0) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `Aucune valeur numerique trouvee dans la plage ${intent.range}.`,
            isError: true,
          },
        ]);
        setLoading(false);
        return;
      }

      const mapping = FORMULA_NAME_MAP[intent.formulaName];
      if (!mapping) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `Formule ${intent.formulaName} non supportee par le moteur.`,
            isError: true,
          },
        ]);
        setLoading(false);
        return;
      }

      const variables: Record<string, unknown> = { valeurs: values };
      if (mapping.key === "mediane") {
        variables["valeurs"] = values;
      }

      const res = await calculate(apiKey, mapping.key, variables);
      onCreditsUpdate(res.credits_remaining);

      const resultValue = res.result[mapping.resultField];
      const displayValue = typeof resultValue === "number"
        ? (Number.isInteger(resultValue) ? resultValue.toString() : parseFloat(resultValue.toFixed(6)).toString())
        : String(resultValue);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `${intent.description}.\n\nResultat : **${displayValue}**`,
          formula: `=${intent.formulaName}(${intent.range})`,
          computedValue: displayValue,
          targetCell: intent.targetCell,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Erreur de calcul : ${err instanceof Error ? err.message : "Erreur inconnue"}`,
          isError: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [input, gridData, selectedCell, apiKey, engineOnline, onInsertValue, onCreditsUpdate]);

  const handleInsert = useCallback((msg: ChatMessage) => {
    if (msg.computedValue && msg.targetCell && msg.formula) {
      onInsertValue(msg.targetCell, msg.computedValue, msg.formula);
    }
  }, [onInsertValue]);

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 text-xs mt-8 space-y-2">
            <p className="font-medium text-gray-500">CLIG AI</p>
            <p>Demandez un calcul en langage naturel.</p>
            <p className="text-[11px]">Ex: &quot;Calcule la moyenne&quot;, &quot;Fais la somme de A1:A7&quot;</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            {msg.role === "user" ? (
              <div className="bg-indigo-600 text-white text-sm px-4 py-2 rounded-2xl rounded-br-sm max-w-[85%]">
                {msg.content}
              </div>
            ) : (
              <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-4 py-3 max-w-[95%] shadow-sm space-y-2">
                <p className="text-sm text-gray-700 whitespace-pre-line">{msg.content}</p>

                {msg.formula && (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
                    <code className="text-xs text-indigo-700 font-mono">{msg.formula}</code>
                  </div>
                )}

                {msg.computedValue && msg.targetCell && (
                  <button
                    onClick={() => handleInsert(msg)}
                    className="w-full btn-primary text-white text-sm font-semibold py-2.5 rounded-xl"
                  >
                    Inserer {msg.computedValue} dans {msg.targetCell}
                  </button>
                )}

                {msg.isError && (
                  <div className="text-xs text-red-500 mt-1">
                    Verifiez les donnees et reessayez.
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm">
              <div className="flex items-center gap-2 text-gray-400 text-sm">
                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Calcul en cours...
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 px-3 py-3 bg-white">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
              }
            }}
            placeholder={`Demander pour ${selectedCell || "..."}...`}
            className="flex-1 text-sm border border-gray-200 rounded-xl px-4 py-2.5 focus-ring-theme"
            disabled={loading}
          />
          <button
            onClick={handleSubmit}
            disabled={loading || !input.trim()}
            className="p-2.5 btn-primary text-white rounded-xl disabled:opacity-40"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
        </div>
        <p className="text-[10px] text-gray-400 mt-1.5 text-center">
          L&apos;IA voit votre feuille de calcul en temps reel.
        </p>
      </div>
    </div>
  );
}
