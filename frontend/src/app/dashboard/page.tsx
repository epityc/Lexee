"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import ThemePicker from "@/components/ThemePicker";
import {
  getMe,
  listWorkbooks,
  createWorkbook,
  deleteWorkbook,
  importWorkbook,
} from "@/lib/api";
import type { ClientInfo, WorkbookSummary } from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const [apiKey, setApiKey] = useState("");
  const [client, setClient] = useState<ClientInfo | null>(null);
  const [workbooks, setWorkbooks] = useState<WorkbookSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [importing, setImporting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadData = useCallback(async (key: string) => {
    try {
      const [clientData, wbData] = await Promise.all([
        getMe(key),
        listWorkbooks(key),
      ]);
      setClient(clientData);
      setWorkbooks(wbData.workbooks);
    } catch (err) {
      if (
        err instanceof Error &&
        (err.message.includes("invalide") || err.message.includes("401"))
      ) {
        localStorage.removeItem("nexusgrid_api_key");
        router.push("/");
        return;
      }
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    const key = localStorage.getItem("nexusgrid_api_key");
    if (!key) {
      router.push("/");
      return;
    }
    setApiKey(key);
    loadData(key);
  }, [router, loadData]);

  const handleLogout = useCallback(() => {
    localStorage.removeItem("nexusgrid_api_key");
    localStorage.removeItem("nexusgrid_client");
    router.push("/");
  }, [router]);

  const handleCreate = useCallback(async () => {
    if (!apiKey || creating) return;
    setCreating(true);
    try {
      const wb = await createWorkbook(apiKey, "Sans titre");
      router.push(`/editor?id=${wb.id}`);
    } catch {
      setError("Impossible de creer le classeur.");
    } finally {
      setCreating(false);
    }
  }, [apiKey, creating, router]);

  const handleImport = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file || !apiKey) return;
      setImporting(true);
      try {
        const wb = await importWorkbook(apiKey, file);
        router.push(`/editor?id=${wb.id}`);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Erreur lors de l'import."
        );
      } finally {
        setImporting(false);
        if (fileInputRef.current) fileInputRef.current.value = "";
      }
    },
    [apiKey, router]
  );

  const handleDelete = useCallback(
    async (id: number, name: string) => {
      if (!confirm(`Supprimer le classeur "${name}" ?`)) return;
      try {
        await deleteWorkbook(apiKey, id);
        setWorkbooks((prev) => prev.filter((wb) => wb.id !== id));
      } catch {
        setError("Impossible de supprimer le classeur.");
      }
    },
    [apiKey]
  );

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString("fr-FR", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

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

  return (
    <div className="min-h-screen bg-theme-body theme-transition">
      {/* Header */}
      <header className="h-14 bg-theme-header text-theme-header flex items-center justify-between px-6 shrink-0 theme-transition">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-bold tracking-tight">
            <span className="text-theme-accent theme-transition">Nexus</span>
            <span className="text-white"> Grid</span>
          </h1>
        </div>
        <div className="flex items-center gap-4">
          {client && (
            <>
              <span className="text-sm text-white/80 font-medium">
                {client.name}
              </span>
              <span
                className={`text-xs px-3 py-1 rounded-full font-medium ${
                  client.plan === "pro"
                    ? "bg-indigo-500/20 text-indigo-300"
                    : "bg-gray-500/20 text-gray-300"
                }`}
              >
                {client.plan === "pro" ? "PRO" : "FREE"}
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

      <div className="max-w-6xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            {error}
            <button
              onClick={() => setError("")}
              className="ml-3 text-red-500 hover:text-red-700"
            >
              x
            </button>
          </div>
        )}

        {/* Subscription card */}
        <div className="mb-8 rounded-xl border border-gray-200 bg-white overflow-hidden">
          <div className="p-6 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                Votre abonnement
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                {client?.plan === "pro"
                  ? "Vous beneficiez de toutes les fonctionnalites Pro."
                  : "Passez a Pro pour debloquer toutes les formules et l'import illimite."}
              </p>
            </div>
            {client?.plan === "pro" ? (
              <div className="text-right">
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-bold text-gray-900">12</span>
                  <span className="text-lg text-gray-500">&euro;/mois</span>
                </div>
                <span className="inline-block mt-1 text-xs px-3 py-1 rounded-full bg-green-100 text-green-700 font-medium">
                  Actif
                </span>
              </div>
            ) : (
              <div className="text-right">
                <div className="flex items-baseline gap-1 mb-2">
                  <span className="text-3xl font-bold text-gray-900">12</span>
                  <span className="text-lg text-gray-500">&euro;/mois</span>
                </div>
                <button className="btn-primary text-white text-sm font-medium px-5 py-2 rounded-lg">
                  Passer a Pro
                </button>
              </div>
            )}
          </div>
          <div className="border-t border-gray-100 px-6 py-4 bg-gray-50 grid grid-cols-3 gap-6 text-center">
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {client?.credits ?? 0}
              </p>
              <p className="text-xs text-gray-500">Credits restants</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">494</p>
              <p className="text-xs text-gray-500">Formules disponibles</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {workbooks.length}
              </p>
              <p className="text-xs text-gray-500">Classeurs</p>
            </div>
          </div>
        </div>

        {/* Workbooks section */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">
            Mes classeurs
          </h2>
          <div className="flex items-center gap-3">
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx,.xls"
              className="hidden"
              onChange={handleImport}
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={importing}
              className="flex items-center gap-2 text-sm font-medium px-4 py-2.5 rounded-lg border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 transition-colors disabled:opacity-50"
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
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
                />
              </svg>
              {importing ? "Import..." : "Importer"}
            </button>
            <button
              onClick={handleCreate}
              disabled={creating}
              className="flex items-center gap-2 text-sm font-medium px-4 py-2.5 rounded-lg btn-primary text-white disabled:opacity-50"
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
                  d="M12 4v16m8-8H4"
                />
              </svg>
              {creating ? "Creation..." : "Nouveau classeur"}
            </button>
          </div>
        </div>

        {workbooks.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-xl border border-gray-200">
            <svg
              className="w-16 h-16 mx-auto text-gray-300 mb-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
              />
            </svg>
            <p className="text-gray-500 mb-1 font-medium">
              Aucun classeur
            </p>
            <p className="text-sm text-gray-400 mb-6">
              Creez un nouveau classeur ou importez un fichier CSV/XLSX.
            </p>
            <div className="flex items-center justify-center gap-3">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="text-sm font-medium px-4 py-2.5 rounded-lg border border-gray-300 bg-white hover:bg-gray-50 text-gray-700"
              >
                Importer un fichier
              </button>
              <button
                onClick={handleCreate}
                className="text-sm font-medium px-4 py-2.5 rounded-lg btn-primary text-white"
              >
                Nouveau classeur
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {workbooks.map((wb) => (
              <div
                key={wb.id}
                className="group bg-white rounded-xl border border-gray-200 hover:border-gray-300 hover:shadow-md transition-all cursor-pointer overflow-hidden"
                onClick={() => router.push(`/editor?id=${wb.id}`)}
              >
                {/* Grid preview placeholder */}
                <div className="h-32 bg-gray-50 border-b border-gray-100 p-3 relative">
                  <div className="grid grid-cols-4 gap-px h-full">
                    {Array.from({ length: 16 }).map((_, i) => (
                      <div
                        key={i}
                        className="bg-white border border-gray-100 rounded-sm"
                      />
                    ))}
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(wb.id, wb.name);
                    }}
                    className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-md bg-white border border-gray-200 hover:bg-red-50 hover:border-red-200 hover:text-red-600 text-gray-400"
                  >
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
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  </button>
                </div>
                <div className="p-4">
                  <h3 className="font-medium text-gray-900 truncate">
                    {wb.name}
                  </h3>
                  <p className="text-xs text-gray-400 mt-1">
                    Modifie le {formatDate(wb.updated_at)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
