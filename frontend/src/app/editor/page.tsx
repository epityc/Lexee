"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import ThemePicker from "@/components/ThemePicker";
import SpreadsheetGrid, {
  setCellValue,
  cellToColRow,
} from "@/components/SpreadsheetGrid";
import CligChat from "@/components/CligChat";
import type { CellData, CellFormulas } from "@/components/SpreadsheetGrid";
import { getMe, getFormulas, getWorkbook, updateWorkbook } from "@/lib/api";
import type { ClientInfo } from "@/lib/api";

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
  const nameInputRef = useRef<HTMLInputElement>(null);

  const [gridData, setGridData] = useState<CellData>({});
  const [cellFormulas, setCellFormulas] = useState<CellFormulas>({});
  const [selectedCell, setSelectedCell] = useState<string | null>("A1");

  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const latestData = useRef({ data: gridData, formulas: cellFormulas });

  useEffect(() => {
    latestData.current = { data: gridData, formulas: cellFormulas };
  }, [gridData, cellFormulas]);

  useEffect(() => {
    const key = localStorage.getItem("nexusgrid_api_key");
    if (!key) {
      router.push("/");
      return;
    }
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
            for (const [rowStr, val] of Object.entries(
              rows as Record<string, string>
            )) {
              converted[col][parseInt(rowStr)] = val;
            }
          }
          setGridData(converted);
          setCellFormulas(wbData.formulas || {});
        }
      })
      .catch((err) => {
        if (
          err instanceof Error &&
          (err.message.includes("invalide") || err.message.includes("401"))
        ) {
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
      const d = latestData.current.data;
      const serialized: Record<string, Record<string, string>> = {};
      for (const [col, rows] of Object.entries(d)) {
        serialized[col] = {};
        for (const [rowNum, val] of Object.entries(rows)) {
          if (val !== "") serialized[col][rowNum] = val;
        }
      }
      await updateWorkbook(apiKey, parseInt(workbookId), {
        data: serialized,
        formulas: latestData.current.formulas,
      });
    } catch {
      // silent
    } finally {
      setSaving(false);
    }
  }, [apiKey, workbookId]);

  const scheduleAutoSave = useCallback(() => {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => doSave(), 2000);
  }, [doSave]);

  const handleDataChange = useCallback(
    (data: CellData) => {
      setGridData(data);
      scheduleAutoSave();
    },
    [scheduleAutoSave]
  );

  const handleLogout = useCallback(() => {
    localStorage.removeItem("nexusgrid_api_key");
    localStorage.removeItem("nexusgrid_client");
    router.push("/");
  }, [router]);

  const handleCreditsUpdate = useCallback((credits: number) => {
    setClient((prev) => (prev ? { ...prev, credits } : prev));
  }, []);

  const handleInsertValue = useCallback(
    (cell: string, value: string, formula: string) => {
      const parsed = cellToColRow(cell);
      if (parsed) {
        setGridData((prev) => {
          const next = setCellValue(prev, parsed.col, parsed.row, value);
          return next;
        });
        setCellFormulas((prev) => ({ ...prev, [cell]: formula }));
        setSelectedCell(cell);
        scheduleAutoSave();
      }
    },
    [scheduleAutoSave]
  );

  const handleNameSave = useCallback(async () => {
    setEditingName(false);
    if (!apiKey || !workbookId) return;
    try {
      await updateWorkbook(apiKey, parseInt(workbookId), { name: wbName });
    } catch {
      // silent
    }
  }, [apiKey, workbookId, wbName]);

  useEffect(() => {
    if (editingName && nameInputRef.current) {
      nameInputRef.current.focus();
      nameInputRef.current.select();
    }
  }, [editingName]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-theme-body theme-transition">
        <div className="flex items-center gap-3 text-gray-500">
          <svg
            className="animate-spin h-5 w-5"
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
          Chargement...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-theme-body theme-transition">
        <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-lg">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-theme-body theme-transition">
      {/* Top bar */}
      <header className="h-14 bg-theme-header text-theme-header flex items-center justify-between px-6 shrink-0 theme-transition">
        <div className="flex items-center gap-4">
          <button
            onClick={() => {
              doSave();
              router.push("/dashboard");
            }}
            className="text-white/60 hover:text-white transition-colors flex items-center gap-1.5"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15 19l-7-7 7-7"
              />
            </svg>
            <span className="text-xs">Dashboard</span>
          </button>
          <div className="h-5 w-px bg-white/20" />
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
              className="text-sm font-semibold bg-white/10 text-white px-2 py-1 rounded border border-white/20 outline-none"
            />
          ) : (
            <h1
              className="text-sm font-semibold text-white cursor-pointer hover:bg-white/10 px-2 py-1 rounded transition-colors"
              onClick={() => setEditingName(true)}
              title="Cliquer pour renommer"
            >
              {wbName}
            </h1>
          )}
          <div className="h-5 w-px bg-white/20" />
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                engineOnline ? "bg-green-400" : "bg-red-400"
              }`}
            />
            <span className="text-xs text-white/60">
              {engineOnline ? "ONLINE" : "OFFLINE"}
            </span>
          </div>
          {saving && (
            <span className="text-xs text-white/40 ml-2">
              Sauvegarde...
            </span>
          )}
        </div>
        <div className="flex items-center gap-4">
          {client && (
            <>
              <span className="text-sm text-white/80 font-medium">
                {client.name?.substring(0, 2).toUpperCase()}
              </span>
              <span
                className={`text-xs px-3 py-1 rounded-full font-medium ${
                  client.credits > 10
                    ? "bg-green-500/20 text-green-300"
                    : client.credits > 0
                    ? "bg-yellow-500/20 text-yellow-300"
                    : "bg-red-500/20 text-red-300"
                }`}
              >
                {client.credits} credit{client.credits !== 1 ? "s" : ""}
              </span>
            </>
          )}
          <ThemePicker />
          <button
            onClick={handleLogout}
            className="text-xs text-white/50 hover:text-white transition-colors px-3 py-1.5 rounded-md hover:bg-white/10"
          >
            Deconnexion
          </button>
        </div>
      </header>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Spreadsheet area */}
        <main className="flex-1 flex flex-col overflow-hidden">
          <SpreadsheetGrid
            data={gridData}
            formulas={cellFormulas}
            onDataChange={handleDataChange}
            selectedCell={selectedCell}
            onSelectCell={setSelectedCell}
          />
        </main>

        {/* Right panel */}
        <aside className="w-[380px] border-l border-gray-300 flex flex-col shrink-0 bg-white">
          {/* Tabs */}
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveTab("clig")}
              className={`flex-1 text-sm font-semibold py-3 text-center transition-colors ${
                activeTab === "clig"
                  ? "text-indigo-700 border-b-2 border-indigo-600"
                  : "text-gray-400 hover:text-gray-600"
              }`}
            >
              CLIG AI
            </button>
            <button
              onClick={() => setActiveTab("engine")}
              className={`flex-1 text-sm font-semibold py-3 text-center transition-colors ${
                activeTab === "engine"
                  ? "text-indigo-700 border-b-2 border-indigo-600"
                  : "text-gray-400 hover:text-gray-600"
              }`}
            >
              LOGIC ENGINE
            </button>
          </div>

          <div className="flex-1 overflow-hidden">
            {activeTab === "clig" ? (
              <CligChat
                apiKey={apiKey}
                gridData={gridData}
                selectedCell={selectedCell}
                onInsertValue={handleInsertValue}
                onCreditsUpdate={handleCreditsUpdate}
                engineOnline={engineOnline}
              />
            ) : (
              <div className="p-4 text-center text-gray-400 text-sm mt-8">
                <p className="font-medium text-gray-500 mb-2">Logic Engine</p>
                <p className="text-xs">
                  {engineOnline
                    ? "Moteur en ligne — 494 formules disponibles"
                    : "Moteur hors ligne"}
                </p>
              </div>
            )}
          </div>

          {/* Memory section */}
          <div className="border-t border-gray-200 px-4 py-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-gray-600 uppercase tracking-wider flex items-center gap-1.5">
                <svg
                  className="w-3.5 h-3.5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                MEMOIRE
              </span>
            </div>
            <div className="border-2 border-dashed border-gray-200 rounded-xl py-6 text-center">
              <svg
                className="w-8 h-8 mx-auto text-gray-300 mb-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <p className="text-xs text-gray-400">PDF, CSV, XLSX, XLS, TXT</p>
              <p className="text-xs text-gray-400">Glissez ou cliquez</p>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
