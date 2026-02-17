"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import ExcelGrid from "@/components/ExcelGrid";
import { getFormulas, getMe } from "@/lib/api";
import type { ClientInfo, FormulaMeta } from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const [apiKey, setApiKey] = useState("");
  const [client, setClient] = useState<ClientInfo | null>(null);
  const [formulas, setFormulas] = useState<Record<string, FormulaMeta>>({});
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const key = localStorage.getItem("lexee_api_key");
    if (!key) {
      router.push("/");
      return;
    }
    setApiKey(key);

    Promise.all([getMe(key), getFormulas(key)])
      .then(([clientData, formulaData]) => {
        setClient(clientData);
        setFormulas(formulaData.formulas);
        // Select first formula by default
        const keys = Object.keys(formulaData.formulas);
        if (keys.length > 0) setSelected(keys[0]);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Erreur");
        // If unauthorized, redirect to login
        if (
          err instanceof Error &&
          (err.message.includes("invalide") || err.message.includes("401"))
        ) {
          localStorage.removeItem("lexee_api_key");
          router.push("/");
        }
      })
      .finally(() => setLoading(false));
  }, [router]);

  function handleLogout() {
    localStorage.removeItem("lexee_api_key");
    localStorage.removeItem("lexee_client");
    router.push("/");
  }

  function handleCreditsUpdate(credits: number) {
    setClient((prev) => (prev ? { ...prev, credits } : prev));
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
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
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-lg">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-white">
      {/* Top bar */}
      <header className="h-12 bg-gray-900 text-white flex items-center justify-between px-4 shrink-0">
        <div className="flex items-center gap-3">
          <h1 className="text-base font-bold tracking-tight">
            <span className="text-green-400">Lex</span>ee
          </h1>
          <span className="text-xs text-gray-400 hidden sm:inline">
            Calculation Engine
          </span>
        </div>
        <div className="flex items-center gap-4">
          {client && (
            <>
              <span className="text-sm text-gray-300">{client.name}</span>
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-medium ${
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
          <button
            onClick={handleLogout}
            className="text-xs text-gray-400 hover:text-white transition-colors"
          >
            Deconnexion
          </button>
        </div>
      </header>

      {/* Status bar */}
      {client && client.status !== "active" && (
        <div className="bg-yellow-50 border-b border-yellow-200 text-yellow-800 text-xs px-4 py-2 text-center">
          Votre compte est en attente de paiement. Les calculs sont
          desactives.
        </div>
      )}

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <Sidebar
          formulas={formulas}
          selected={selected}
          onSelect={setSelected}
        />

        {/* Excel grid area */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {selected && formulas[selected] ? (
            <ExcelGrid
              key={selected}
              apiKey={apiKey}
              formulaKey={selected}
              meta={formulas[selected]}
              onCreditsUpdate={handleCreditsUpdate}
            />
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
              Selectionnez une formule dans le panneau de gauche.
            </div>
          )}
        </main>
      </div>

      {/* Bottom status bar (like Excel) */}
      <footer className="h-6 bg-green-600 flex items-center px-3 text-xs text-white shrink-0">
        <span>PRET</span>
        {selected && formulas[selected] && (
          <span className="ml-auto text-green-100">
            {formulas[selected].name} | {formulas[selected].variables.length}{" "}
            variable{formulas[selected].variables.length > 1 ? "s" : ""}
          </span>
        )}
      </footer>
    </div>
  );
}
