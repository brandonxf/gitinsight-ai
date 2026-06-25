import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Card, ProgressBar } from "../components/ui";
import { useFindings, useJobPolling, useResult } from "../features/analysis/hooks";
import { OverviewTab, QualityTab, SecurityTab } from "../features/analysis/tabs";

const PHASE_LABELS: Record<string, string> = {
  clone: "Clonando repositorio…",
  tech_detect: "Detectando tecnologías…",
  structure: "Analizando estructura…",
  quality_ruff: "Evaluando calidad (Ruff)…",
  complexity: "Midiendo complejidad…",
  security_bandit: "Escaneando seguridad (Bandit)…",
  secret_scan: "Buscando secretos…",
  persist: "Guardando resultados…",
  done: "Completado",
  error: "Error",
};

type Tab = "overview" | "quality" | "security";

export default function Analysis() {
  const { jobId = "" } = useParams();
  const [tab, setTab] = useState<Tab>("overview");

  const job = useJobPolling(jobId);
  const done = job.data?.status === "SUCCEEDED";
  const result = useResult(jobId, done);
  const findings = useFindings(jobId, done);

  const status = job.data?.status;
  const securityCount =
    findings.data?.items.filter((f) =>
      ["secret", "vuln", "insecure_config"].includes(f.category),
    ).length ?? 0;
  const qualityCount = (findings.data?.items.length ?? 0) - securityCount;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <Link to="/" className="text-lg font-bold">
            GitInsight AI
          </Link>
          <span className="text-xs text-slate-400">job {jobId.slice(0, 8)}</span>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-8">
        {job.isError && (
          <Card>
            <p className="text-sm text-red-600">No se pudo cargar el análisis.</p>
          </Card>
        )}

        {status && status !== "SUCCEEDED" && (
          <Card>
            <div className="mb-3 flex items-center justify-between">
              <span className="font-medium">
                {status === "FAILED"
                  ? "El análisis falló"
                  : PHASE_LABELS[job.data?.phase ?? ""] ?? "Procesando…"}
              </span>
              <span className="text-sm text-slate-500">{job.data?.progress_pct ?? 0}%</span>
            </div>
            <ProgressBar value={job.data?.progress_pct ?? 0} />
            {status === "FAILED" && job.data?.error_message && (
              <p className="mt-3 text-sm text-red-600">{job.data.error_message}</p>
            )}
          </Card>
        )}

        {done && result.data && (
          <>
            <div className="mb-6 flex gap-1 border-b border-slate-200">
              <TabButton active={tab === "overview"} onClick={() => setTab("overview")}>
                Overview
              </TabButton>
              <TabButton active={tab === "quality"} onClick={() => setTab("quality")}>
                Quality {qualityCount > 0 && <Count>{qualityCount}</Count>}
              </TabButton>
              <TabButton active={tab === "security"} onClick={() => setTab("security")}>
                Security {securityCount > 0 && <Count>{securityCount}</Count>}
              </TabButton>
            </div>

            {tab === "overview" && <OverviewTab result={result.data} />}
            {tab === "quality" && <QualityTab findings={findings.data?.items ?? []} />}
            {tab === "security" && <SecurityTab findings={findings.data?.items ?? []} />}
          </>
        )}
      </main>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
        active
          ? "border-slate-900 text-slate-900"
          : "border-transparent text-slate-500 hover:text-slate-800"
      }`}
    >
      {children}
    </button>
  );
}

function Count({ children }: { children: React.ReactNode }) {
  return (
    <span className="ml-1 rounded-full bg-slate-200 px-1.5 text-xs text-slate-700">
      {children}
    </span>
  );
}
