"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import ThemePicker from "@/components/ThemePicker";
import SpreadsheetGrid, { setCellValue, cellToColRow } from "@/components/SpreadsheetGrid";
import CligChat from "@/components/CligChat";
import type { CellData } from "@/components/SpreadsheetGrid";
import { getMe, getFormulas } from "@/lib/api";
import type { ClientInfo } from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const [apiKey, setApiKey] = useState("");
  const [client, setClient] = useState<ClientInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [engineOnline, setEngineOnline] = useState(false);
  const [activeTab, setActiveTab] = useState<"clig" | "engine">("clig");

  const [gridData, setGridData] = useState<CellData>({});
  const [selectedCell, setSelectedCell] = useState<string | null>("A1");

  useEffect(() => {
    const key = localStorage.getItem("nexusgrid_api_key");
    if (!key) {
      router.push("/");
      return;
    }
    setApiKey(key);

    Promise.all([getMe(key), getFormulas(key)])
      .then(([clientData]) => {
        setClient(clientData);
        setEngineOnline(true);
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
  }, [router]);

  const handleLogout = useCallback(() => {
    localStorage.removeItem("nexusgrid_api_key");
    localStorage.removeItem("nexusgrid_client");
    router.push("/");
  }, [router]);

  const handleCreditsUpdate = useCallback((credits: number) => {
    setClient((prev) => (prev ? { ...prev, credits } : prev));
  }, []);

  const handleInsertValue = useCallback((cell: string, value: string) => {
    const parsed = cellToColRow(cell);
    if (parsed) {
      setGridData((prev) => setCellValue(prev, parsed.col, parsed.row, value));
      setSelectedCell(cell);
    }
  }, []);

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
          <h1 className="text-lg font-bold tracking-tight">
            <span className="text-white">Espace de Travail</span>
          </h1>
          <div className="h-5 w-px bg-white/20" />
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${engineOnline ? "bg-green-400" : "bg-red-400"}`} />
            <span className="text-xs text-white/60">
              LOGIC ENGINE: {engineOnline ? "ONLINE" : "OFFLINE"}
            </span>
          </div>
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
          <div className="h-5 w-px bg-white/20" />
          <span className="text-xs px-2 py-1 bg-yellow-500/20 text-yellow-300 rounded-full font-medium cursor-pointer">
            Console Active
          </span>
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
            onDataChange={setGridData}
            selectedCell={selectedCell}
            onSelectCell={setSelectedCell}
          />
        </main>

        {/* Right panel — CLIG AI / Logic Engine */}
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

          {/* Tab content */}
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
                    ? `Moteur en ligne — 494 formules disponibles`
                    : "Moteur hors ligne"}
                </p>
              </div>
            )}
          </div>

          {/* Memory section */}
          <div className="border-t border-gray-200 px-4 py-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-gray-600 uppercase tracking-wider flex items-center gap-1.5">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                MEMOIRE
              </span>
              <button className="text-xs text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1">
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                Ajouter
              </button>
            </div>
            <div className="border-2 border-dashed border-gray-200 rounded-xl py-6 text-center">
              <svg className="w-8 h-8 mx-auto text-gray-300 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
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
