import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { AxiosError } from "axios";

import { apiClient } from "../lib/apiClient";
import { useStartAnalysis } from "../features/analysis/hooks";

interface HealthResponse {
  status: string;
  checks: Record<string, string>;
}

export default function Home() {
  const [url, setUrl] = useState("");
  const start = useStartAnalysis();

  // Verifica el estado del backend.
  const { data: health } = useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: async () => (await apiClient.get("/health")).data,
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    start.mutate(url.trim());
  }

  const errorMessage =
    start.error instanceof AxiosError
      ? (start.error.response?.data?.detail ?? "No se pudo iniciar el análisis.")
      : start.error
        ? "No se pudo iniciar el análisis."
        : null;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-xl">
        <h1 className="text-3xl font-bold mb-2">GitInsight AI</h1>
        <p className="text-slate-600 mb-6">
          Análisis automático de repositorios GitHub: tecnologías, calidad y seguridad.
        </p>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="url"
            required
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://github.com/owner/repo"
            className="flex-1 rounded-lg border border-slate-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
          <button
            type="submit"
            disabled={start.isPending}
            className="rounded-lg bg-slate-900 px-5 py-2 text-white font-medium hover:bg-slate-700 disabled:opacity-60"
          >
            {start.isPending ? "Iniciando…" : "Analizar"}
          </button>
        </form>

        {errorMessage && <p className="mt-3 text-sm text-red-600">{errorMessage}</p>}

        <div className="mt-6 text-sm text-slate-500">
          Backend:{" "}
          <span className={health?.status === "ok" ? "text-green-600" : "text-amber-600"}>
            {health?.status ?? "comprobando…"}
          </span>
        </div>
      </div>
    </div>
  );
}
