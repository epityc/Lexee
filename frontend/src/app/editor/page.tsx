"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import ThemePicker from "@/components/ThemePicker";
import SpreadsheetGrid, { setCellValue, cellToColRow } from "@/components/SpreadsheetGrid";
import type { CellData, CellFormulas } from "@/components/SpreadsheetGrid";
import CligChat from "@/components/CligChat";
import Toolbar from "@/components/Toolbar";
import SheetTabs from "@/components/SheetTabs";
import ChartPanel from "@/components/ChartPanel";
import { getMe, getFormulas, getWorkbook, updateWorkbook } from "@/lib/api";
import type { ClientInfo } from "@/lib/api";
import type { CellStyle, Sheet, ConditionalRule, ValidationRule } from "@/lib/types";
import { createEmptySheet } from "@/lib/types";

let sheetCounter = 1;
function newSheetId() {
  return `sheet_${Date.now()}_${sheetCounter++}`;
}

export default function EditorPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const workbookId = searchParams.get("id");

  const [apiKey, setApiKey] = useState("");
  const [client, setClient] = useState<ClientInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [engineOnline, setEngineOnline] = useState(false);
  const [activeTab, setActiveTab] = useState<"clig" | "engine">("clig");
  const [wbName, setWbName] = useState("Sans titre");
  const [editingName, setEditingName] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showChart, setShowChart] = useState(false);
  const nameInputRef = useRef<HTMLInputElement>(null);

  const [sheets, setSheets] = useState<Sheet[]>([createEmptySheet(newSheetId(), "Feuille 1")]);
  const [activeSheetId, setActiveSheetId] = useState(sheets[0].id);

  const activeSheet = sheets.find((s) => s.id === activeSheetId) || sheets[0];

  const [selectedCell, setSelectedCell] = useState<string | null>("A1");

  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const latestSheets = useRef(sheets);
  useEffect(() => { latestSheets.current = sheets; }, [sheets]);

  const updateActiveSheet = useCallback(
    (update: Partial<Sheet>) => {
      setSheets((prev) =>
        prev.map((s) => (s.id === activeSheetId ? { ...s, ...update } : s))
      );
    },
    [activeSheetId]
  );

  const [undoStack, setUndoStack] = useState<CellData[]>([]);
  const [redoStack, setRedoStack] = useState<CellData[]>([]);

  const pushUndo = useCallback(() => {
    setUndoStack((prev) => [...prev.slice(-50), JSON.parse(JSON.stringify(activeSheet.data))]);
    setRedoStack([]);
  }, [activeSheet.data]);

  const undo = useCallback(() => {
    setUndoStack((prev) => {
      if (prev.length === 0) return prev;
      const last = prev[prev.length - 1];
      setRedoStack((r) => [...r, JSON.parse(JSON.stringify(activeSheet.data))]);
      updateActiveSheet({ data: last });
      return prev.slice(0, -1);
    });
  }, [activeSheet.data, updateActiveSheet]);

  const redo = useCallback(() => {
    setRedoStack((prev) => {
      if (prev.length === 0) return prev;
      const last = prev[prev.length - 1];
      setUndoStack((u) => [...u, JSON.parse(JSON.stringify(activeSheet.data))]);
      updateActiveSheet({ data: last });
      return prev.slice(0, -1);
    });
  }, [activeSheet.data, updateActiveSheet]);

  useEffect(() => {
    const key = localStorage.getItem("nexusgrid_api_key");
    if (!key) { router.push("/"); return; }
    setApiKey(key);

    const wbId = workbookId ? parseInt(workbookId) : null;

    Promise.all([
      getMe(key),
      getFormulas(key),
      wbId ? getWorkbook(key, wbId) : Promise.resolve(null),
    ])
      .then(([clientData, , wbData]) => {
        setClient(clientData);
        setEngineOnline(true);
        if (wbData) {
          setWbName(wbData.name);
          const converted: CellData = {};
          for (const [col, rows] of Object.entries(wbData.data)) {
            converted[col] = {};
            for (const [rowStr, val] of Object.entries(rows as Record<string, string>)) {
              converted[col][parseInt(rowStr)] = val;
            }
          }
          const id = newSheetId();
          setSheets([{
            ...createEmptySheet(id, "Feuille 1"),
            data: converted,
            styles: {},
          }]);
          setActiveSheetId(id);
        }
      })
      .catch((err) => {
        if (err instanceof Error && (err.message.includes("invalide") || err.message.includes("401"))) {
          localStorage.removeItem("nexusgrid_api_key");
          router.push("/");
          return;
        }
        setError(err instanceof Error ? err.message : "Erreur");
      })
      .finally(() => setLoading(false));
  }, [router, workbookId]);

  const doSave = useCallback(async () => {
    if (!apiKey || !workbookId) return;
    setSaving(true);
    try {
      const sheet = latestSheets.current[0];
      if (!sheet) return;
      const serialized: Record<string, Record<string, string>> = {};
      for (const [col, rows] of Object.entries(sheet.data)) {
        serialized[col] = {};
        for (const [rowNum, val] of Object.entries(rows)) {
          if (val !== "") serialized[col][rowNum] = val;
        }
      }
      await updateWorkbook(apiKey, parseInt(workbookId), {
        data: serialized,
        formulas: {},
      });
    } catch { /* silent */ }
    finally { setSaving(false); }
  }, [apiKey, workbookId]);

  const scheduleAutoSave = useCallback(() => {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => doSave(), 2000);
  }, [doSave]);

  const handleDataChange = useCallback(
    (data: CellData) => {
      updateActiveSheet({ data });
      scheduleAutoSave();
    },
    [updateActiveSheet, scheduleAutoSave]
  );

  const handleStylesChange = useCallback(
    (styles: Record<string, CellStyle>) => {
      updateActiveSheet({ styles });
      scheduleAutoSave();
    },
    [updateActiveSheet, scheduleAutoSave]
  );

  const handleColWidthsChange = useCallback(
    (colWidths: Record<string, number>) => {
      updateActiveSheet({ colWidths });
    },
    [updateActiveSheet]
  );

  const handleInsertValue = useCallback(
    (cell: string, value: string, formula: string) => {
      const parsed = cellToColRow(cell);
      if (parsed) {
        const newData = setCellValue(activeSheet.data, parsed.col, parsed.row, formula || value);
        updateActiveSheet({ data: newData });
        setSelectedCell(cell);
        scheduleAutoSave();
      }
    },
    [activeSheet.data, updateActiveSheet, scheduleAutoSave]
  );

  const handleCreditsUpdate = useCallback((credits: number) => {
    setClient((prev) => (prev ? { ...prev, credits } : prev));
  }, []);

  const handleLogout = useCallback(() => {
    localStorage.removeItem("nexusgrid_api_key");
    localStorage.removeItem("nexusgrid_client");
    router.push("/");
  }, [router]);

  const handleNameSave = useCallback(async () => {
    setEditingName(false);
    if (!apiKey || !workbookId) return;
    try { await updateWorkbook(apiKey, parseInt(workbookId), { name: wbName }); }
    catch { /* silent */ }
  }, [apiKey, workbookId, wbName]);

  useEffect(() => {
    if (editingName && nameInputRef.current) {
      nameInputRef.current.focus();
      nameInputRef.current.select();
    }
  }, [editingName]);

  const handleExportPDF = useCallback(() => window.print(), []);

  const handleAddSheet = useCallback(() => {
    const id = newSheetId();
    const num = sheets.length + 1;
    setSheets((prev) => [...prev, createEmptySheet(id, `Feuille ${num}`)]);
    setActiveSheetId(id);
  }, [sheets.length]);

  const handleRenameSheet = useCallback((id: string, name: string) => {
    setSheets((prev) => prev.map((s) => (s.id === id ? { ...s, name } : s)));
  }, []);

  const handleDeleteSheet = useCallback(
    (id: string) => {
      setSheets((prev) => {
        const next = prev.filter((s) => s.id !== id);
        if (activeSheetId === id && next.length > 0) setActiveSheetId(next[0].id);
        return next;
      });
    },
    [activeSheetId]
  );

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-theme-body theme-transition">
        <div className="flex items-center gap-3 text-gray-500">
          <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Chargement...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-theme-body theme-transition">
        <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-lg">{error}</div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-theme-body theme-transition print:bg-white">
      {/* Header - hidden on print */}
      <header className="h-12 bg-theme-header text-theme-header flex items-center justify-between px-4 shrink-0 theme-transition print:hidden">
        <div className="flex items-center gap-3">
          <button
            onClick={() => { doSave(); router.push("/dashboard"); }}
            className="text-white/60 hover:text-white transition-colors flex items-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div className="h-4 w-px bg-white/20" />
          {editingName ? (
            <input
              ref={nameInputRef}
              type="text"
              value={wbName}
              onChange={(e) => setWbName(e.target.value)}
              onBlur={handleNameSave}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleNameSave();
                if (e.key === "Escape") setEditingName(false);
              }}
              className="text-sm font-semibold bg-white/10 text-white px-2 py-0.5 rounded border border-white/20 outline-none"
            />
          ) : (
            <h1
              className="text-sm font-semibold text-white cursor-pointer hover:bg-white/10 px-2 py-0.5 rounded"
              onClick={() => setEditingName(true)}
            >
              {wbName}
            </h1>
          )}
          <div className="flex items-center gap-1.5 ml-2">
            <span className={`w-1.5 h-1.5 rounded-full ${engineOnline ? "bg-green-400" : "bg-red-400"}`} />
            <span className="text-[10px] text-white/50">{engineOnline ? "ONLINE" : "OFFLINE"}</span>
          </div>
          {saving && <span className="text-[10px] text-white/40 ml-2">Sauvegarde...</span>}
        </div>
        <div className="flex items-center gap-3">
          {client && (
            <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
              client.credits > 10 ? "bg-green-500/20 text-green-300"
                : client.credits > 0 ? "bg-yellow-500/20 text-yellow-300"
                : "bg-red-500/20 text-red-300"
            }`}>
              {client.credits} credit{client.credits !== 1 ? "s" : ""}
            </span>
          )}
          <ThemePicker />
          <button onClick={handleLogout} className="text-xs text-white/50 hover:text-white px-2 py-1 rounded hover:bg-white/10">
            Deconnexion
          </button>
        </div>
      </header>

      {/* Toolbar - hidden on print */}
      <div className="print:hidden">
        <Toolbar
          selectedCell={selectedCell}
          styles={activeSheet.styles}
          onStylesChange={handleStylesChange}
          onUndo={undo}
          onRedo={redo}
          onExportPDF={handleExportPDF}
          onShowChart={() => setShowChart(!showChart)}
        />
      </div>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Spreadsheet + chart area */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {showChart && (
            <div className="print:hidden">
              <ChartPanel data={activeSheet.data} onClose={() => setShowChart(false)} />
            </div>
          )}
          <SpreadsheetGrid
            data={activeSheet.data}
            formulas={{}}
            styles={activeSheet.styles}
            validations={activeSheet.validations}
            conditionalRules={activeSheet.conditionalRules}
            colWidths={activeSheet.colWidths}
            onDataChange={handleDataChange}
            onStylesChange={handleStylesChange}
            onColWidthsChange={handleColWidthsChange}
            selectedCell={selectedCell}
            onSelectCell={setSelectedCell}
            onSave={doSave}
          />
        </main>

        {/* Right panel - hidden on print */}
        <aside className="w-[360px] border-l border-gray-300 flex flex-col shrink-0 bg-white print:hidden">
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveTab("clig")}
              className={`flex-1 text-sm font-semibold py-2.5 text-center transition-colors ${
                activeTab === "clig" ? "text-indigo-700 border-b-2 border-indigo-600" : "text-gray-400 hover:text-gray-600"
              }`}
            >
              CLIG AI
            </button>
            <button
              onClick={() => setActiveTab("engine")}
              className={`flex-1 text-sm font-semibold py-2.5 text-center transition-colors ${
                activeTab === "engine" ? "text-indigo-700 border-b-2 border-indigo-600" : "text-gray-400 hover:text-gray-600"
              }`}
            >
              FORMULES
            </button>
          </div>

          <div className="flex-1 overflow-hidden">
            {activeTab === "clig" ? (
              <CligChat
                apiKey={apiKey}
                gridData={activeSheet.data}
                selectedCell={selectedCell}
                onInsertValue={handleInsertValue}
                onCreditsUpdate={handleCreditsUpdate}
                engineOnline={engineOnline}
              />
            ) : (
              <div className="p-4 text-sm text-gray-500 overflow-y-auto h-full">
                <p className="font-semibold text-gray-700 mb-3">494 formules disponibles</p>
                <p className="text-xs text-gray-400 mb-4">Tapez une formule dans une cellule avec <code className="bg-gray-100 px-1 rounded">=</code></p>
                <div className="space-y-3">
                  {[
                    { cat: "Mathematiques", fns: "SOMME, MOYENNE, MIN, MAX, PRODUIT, ABS, ARRONDI, ENT, PUISSANCE, RACINE, LOG, LN, EXP, MOD" },
                    { cat: "Statistiques", fns: "NB, NBVAL, MEDIANE, ECARTYPE, VARIANCE, GRANDE_VALEUR, PETITE_VALEUR, RANG, NB_SI, SOMME_SI" },
                    { cat: "Logique", fns: "SI, ET, OU, NON" },
                    { cat: "Texte", fns: "CONCATENER, GAUCHE, DROITE, NBCAR, MAJUSCULE, MINUSCULE, SUPPRESPACE" },
                    { cat: "Date", fns: "AUJOURDHUI, MAINTENANT" },
                  ].map(({ cat, fns }) => (
                    <div key={cat}>
                      <p className="text-xs font-semibold text-gray-600 mb-1">{cat}</p>
                      <p className="text-[11px] text-gray-400 leading-relaxed">{fns}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </aside>
      </div>

      {/* Sheet tabs - hidden on print */}
      <div className="print:hidden">
        <SheetTabs
          sheets={sheets.map((s) => ({ id: s.id, name: s.name }))}
          activeSheet={activeSheetId}
          onSelect={setActiveSheetId}
          onAdd={handleAddSheet}
          onRename={handleRenameSheet}
          onDelete={handleDeleteSheet}
        />
      </div>
    </div>
  );
}
