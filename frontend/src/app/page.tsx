"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [apiKey, setApiKey] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const client = await login(apiKey.trim());

      localStorage.setItem("lexee_api_key", apiKey.trim());
      localStorage.setItem("lexee_client", JSON.stringify(client));

      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur de connexion");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-theme-header theme-transition">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white tracking-tight">
            <span className="text-theme-accent theme-transition">Lex</span>ee
          </h1>
          <p className="mt-2 text-white/40">Calculation Engine</p>
        </div>

        {/* Login card */}
        <form
          onSubmit={handleSubmit}
          className="bg-white rounded-xl shadow-2xl p-8 space-y-6"
        >
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Connexion</h2>
            <p className="mt-1 text-sm text-gray-500">
              Entrez votre cle API pour acceder au moteur de calcul.
            </p>
          </div>

          <div>
            <label
              htmlFor="apiKey"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Cle API
            </label>
            <input
              id="apiKey"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="lx_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm
                         focus-ring-theme
                         placeholder:text-gray-400"
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !apiKey.trim()}
            className="w-full py-3 px-4 btn-primary disabled:bg-gray-300 disabled:text-gray-500
                       font-medium rounded-lg text-sm text-white"
          >
            {loading ? "Connexion..." : "Se connecter"}
          </button>

          <p className="text-xs text-center text-gray-400">
            Vous n&apos;avez pas de cle ? Contactez votre administrateur.
          </p>
        </form>
      </div>
    </div>
  );
}
