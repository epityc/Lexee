"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { loginWithEmail, signup, login } from "@/lib/api";

export default function AuthPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [apiKey, setApiKey] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      let client;
      if (showApiKey) {
        client = await login(apiKey.trim());
        localStorage.setItem("nexusgrid_api_key", apiKey.trim());
      } else if (mode === "login") {
        client = await loginWithEmail(email.trim(), password);
        if (client.api_key) localStorage.setItem("nexusgrid_api_key", client.api_key);
      } else {
        client = await signup(name.trim(), email.trim(), password);
        if (client.api_key) localStorage.setItem("nexusgrid_api_key", client.api_key);
      }

      localStorage.setItem("nexusgrid_client", JSON.stringify(client));
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setLoading(false);
    }
  }

  const switchMode = () => {
    setMode(mode === "login" ? "signup" : "login");
    setError("");
    setShowApiKey(false);
  };

  return (
    <div className="min-h-screen flex bg-gray-950">
      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden items-center justify-center">
        <div className="absolute inset-0 bg-gradient-to-br from-emerald-600 via-emerald-700 to-gray-950" />
        <div className="absolute inset-0 opacity-10">
          <svg className="w-full h-full" viewBox="0 0 800 800">
            <defs>
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="white" strokeWidth="0.5" />
              </pattern>
            </defs>
            <rect width="800" height="800" fill="url(#grid)" />
          </svg>
        </div>
        <div className="relative z-10 text-center px-12">
          <h1 className="text-6xl font-black text-white tracking-tight mb-4">
            CLIG
          </h1>
          <p className="text-xl text-emerald-200 font-medium mb-8">
            Le tableur intelligent
          </p>
          <div className="space-y-4 text-left max-w-sm mx-auto">
            {[
              { n: "494", t: "formules (parite Excel)" },
              { n: "IA", t: "integree pour analyser vos donnees" },
              { n: "10$", t: "a vie, paiement unique" },
            ].map(({ n, t }) => (
              <div key={n} className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center">
                  <span className="text-emerald-300 font-bold text-sm">{n}</span>
                </div>
                <span className="text-white/80 text-sm">{t}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right panel — form */}
      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden text-center mb-10">
            <h1 className="text-4xl font-black text-white tracking-tight">CLIG</h1>
            <p className="text-emerald-400 text-sm mt-1">Le tableur intelligent</p>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 shadow-2xl">
            <h2 className="text-2xl font-bold text-white mb-1">
              {showApiKey ? "Connexion par cle API" : mode === "login" ? "Connexion" : "Creer un compte"}
            </h2>
            <p className="text-sm text-gray-400 mb-8">
              {showApiKey
                ? "Entrez votre cle API pour acceder a Clig."
                : mode === "login"
                ? "Connectez-vous pour acceder a vos classeurs."
                : "Inscrivez-vous gratuitement. 50 credits offerts."}
            </p>

            <form onSubmit={handleSubmit} className="space-y-5">
              {showApiKey ? (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1.5">Cle API</label>
                  <input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="ng_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    required
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-sm text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                  />
                </div>
              ) : (
                <>
                  {mode === "signup" && (
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1.5">Nom complet</label>
                      <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="John Doe"
                        required
                        className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-sm text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                      />
                    </div>
                  )}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1.5">Email</label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="vous@exemple.com"
                      required
                      className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-sm text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1.5">Mot de passe</label>
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder={mode === "signup" ? "6 caracteres minimum" : "Votre mot de passe"}
                      required
                      minLength={mode === "signup" ? 6 : undefined}
                      className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-sm text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                    />
                  </div>
                </>
              )}

              {error && (
                <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-xl text-sm">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-semibold rounded-xl text-sm transition-all"
              >
                {loading
                  ? "Chargement..."
                  : showApiKey
                  ? "Se connecter"
                  : mode === "login"
                  ? "Se connecter"
                  : "Creer mon compte"}
              </button>
            </form>

            <div className="mt-6 space-y-3">
              {!showApiKey && (
                <p className="text-center text-sm text-gray-400">
                  {mode === "login" ? "Pas encore de compte ?" : "Deja un compte ?"}{" "}
                  <button onClick={switchMode} className="text-emerald-400 hover:text-emerald-300 font-medium transition-colors">
                    {mode === "login" ? "S'inscrire" : "Se connecter"}
                  </button>
                </p>
              )}
              <p className="text-center">
                <button
                  onClick={() => { setShowApiKey(!showApiKey); setError(""); }}
                  className="text-xs text-gray-500 hover:text-gray-400 transition-colors"
                >
                  {showApiKey ? "Connexion par email" : "Connexion par cle API"}
                </button>
              </p>
            </div>
          </div>

          <p className="text-center text-xs text-gray-600 mt-6">
            En continuant, vous acceptez les conditions d&apos;utilisation de Clig.
          </p>
        </div>
      </div>
    </div>
  );
}
