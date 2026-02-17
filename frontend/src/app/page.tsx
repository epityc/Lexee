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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white tracking-tight">
            <span className="text-green-400">Lex</span>ee
          </h1>
          <p className="mt-2 text-gray-400">Calculation Engine</p>
        </div>

        {/* Login card */}
        <form
          onSubmit={handleSubmit}
          className="bg-white rounded-xl shadow-2xl p-8 space-y-6"
        >
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Connexion</h2>
            <p className="mt-1 text-sm text-gray-500">
              Entrez votre clé API pour accéder au moteur de calcul.
            </p>
          </div>

          <div>
            <label
              htmlFor="apiKey"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Clé API
            </label>
            <input
              id="apiKey"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="lx_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm
                         focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent
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
            className="w-full py-3 px-4 bg-green-600 hover:bg-green-700 disabled:bg-gray-300
                       text-white font-medium rounded-lg transition-colors text-sm"
          >
            {loading ? "Connexion..." : "Se connecter"}
          </button>

          <p className="text-xs text-center text-gray-400">
            Vous n&apos;avez pas de clé ? Contactez votre administrateur.
          </p>
        </form>
      </div>
    </div>
  );
}
