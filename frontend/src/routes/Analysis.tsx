import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  Activity,
  ArrowRight,
  Code,
  FileText,
  Gauge,
  Github,
  Layers,
  Logo,
  Shield,
  Sparkles,
} from "../components/icons";
import { ProgressBar, RiskPill, ScoreRing } from "../components/ui";
import { useFindings, useJobPolling, useResult } from "../features/analysis/hooks";
import { DocsTab, InsightsTab } from "../features/analysis/insights";
import { OverviewTab, QualityTab, SecurityTab } from "../features/analysis/tabs";

const PHASES = [
  { key: "clone", label: "Clonando repositorio" },
  { key: "tech_detect", label: "Detectando tecnologías" },
  { key: "structure", label: "Analizando estructura" },
  { key: "quality_ruff", label: "Evaluando calidad (Ruff)" },
  { key: "complexity", label: "Midiendo complejidad" },
  { key: "security_bandit", label: "Escaneando seguridad (Bandit)" },
  { key: "secret_scan", label: "Buscando secretos" },
  { key: "explain", label: "Sintetizando con IA" },
  { key: "diagrams", label: "Generando diagrama" },
  { key: "docs_gen", label: "Redactando documentación" },
  { key: "persist", label: "Guardando resultados" },
];
const PHASE_LABELS: Record<string, string> = Object.fromEntries(
  PHASES.map((p) => [p.key, p.label]).concat([["done", "Completado"], ["error", "Error"]]),
);

type Tab = "overview" | "insights" | "quality" | "security" | "docs";
const SECURITY_CATS = ["secret", "vuln", "insecure_config"];

export default function Analysis() {
  const { jobId = "" } = useParams();
  const [tab, setTab] = useState<Tab>("overview");

  const job = useJobPolling(jobId);
  const done = job.data?.status === "SUCCEEDED";
  const failed = job.data?.status === "FAILED";
  const result = useResult(jobId, done);
  const findings = useFindings(jobId, done);

  const items = findings.data?.items ?? [];
  const securityCount = items.filter((f) => SECURITY_CATS.includes(f.category)).length;
  const qualityCount = items.length - securityCount;
  const repo = result.data?.repository;
  const structure = result.data?.structure;
  const complexity = (result.data?.metrics?.complexity ?? {}) as { average?: number };

  return (
    <div className="min-h-screen bg-ink-950 text-slate-300">
      {/* NAVBAR */}
      <header className="sticky top-0 z-30 border-b border-white/[0.06] bg-ink-950/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-10">
          <Link to="/" className="flex items-center gap-2.5">
            <Logo className="h-7 w-7" />
            <span className="font-display text-base font-bold tracking-tight text-white">
              GitInsight<span className="text-electric-400"> AI</span>
            </span>
          </Link>
          <Link to="/" className="btn-ghost !py-2">
            Nuevo análisis <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </header>

      <main className="relative mx-auto max-w-7xl px-6 py-10 lg:px-10">
        {job.isError && (
          <div className="panel border-red-500/30 p-5">
            <p className="text-sm text-red-400">No se pudo cargar el análisis (job no encontrado).</p>
          </div>
        )}

        {/* PROCESANDO */}
        {!done && !failed && job.data && (
          <ProcessingCard
            phase={job.data.phase}
            pct={job.data.progress_pct}
            label={PHASE_LABELS[job.data.phase ?? ""] ?? "En cola"}
          />
        )}

        {/* FALLIDO */}
        {failed && (
          <div className="panel border-red-500/30 p-6">
            <div className="flex items-start gap-4">
              <div className="grid h-11 w-11 shrink-0 place-items-center rounded-lg border border-red-500/30 text-red-400">
                <Shield className="h-6 w-6" />
              </div>
              <div>
                <h2 className="font-display font-semibold text-white">El análisis falló</h2>
                <p className="mt-1 text-sm text-red-300">
                  {job.data?.error_message ?? "Error desconocido."}
                </p>
                <Link to="/" className="btn-brand mt-4 !py-2">
                  Intentar con otro repo
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* RESULTADO */}
        {done && result.data && (
          <div className="animate-fade-up space-y-6">
            {/* HEADER DEL REPO */}
            <div className="panel overflow-hidden">
              <div className="flex flex-col gap-6 p-6 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <div className="mb-3 flex flex-wrap items-center gap-2">
                    <RiskPill level={result.data.risk_level} />
                    <span className="chip-mono border-electric-500/30 text-electric-200">
                      <Code className="h-3.5 w-3.5" />
                      {result.data.primary_language ?? "—"}
                    </span>
                  </div>
                  <h1 className="flex items-center gap-2.5 truncate font-display text-2xl font-bold text-white">
                    <Github className="h-6 w-6 shrink-0 text-slate-500" />
                    <span className="truncate">
                      {repo?.owner}
                      <span className="text-slate-600">/</span>
                      {repo?.name}
                    </span>
                  </h1>
                  <a
                    href={repo?.url}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-1.5 inline-block truncate font-mono text-xs text-slate-500 transition-colors hover:text-electric-300"
                  >
                    {repo?.url}
                  </a>
                  {repo?.commit_sha && (
                    <p className="mt-1 font-mono text-[11px] text-slate-600">
                      commit {repo.commit_sha.slice(0, 10)}
                    </p>
                  )}
                </div>
                <div className="flex shrink-0 items-center gap-5">
                  <div className="text-right">
                    <p className="font-mono text-[11px] uppercase tracking-widest text-slate-500">Quality</p>
                    <p className="text-sm text-slate-400">
                      {scoreVerdict(result.data.quality_score)}
                    </p>
                  </div>
                  <ScoreRing score={result.data.quality_score} />
                </div>
              </div>

              {/* STAT TILES */}
              <div className="grid gap-px border-t border-white/[0.06] bg-white/[0.06] sm:grid-cols-2 lg:grid-cols-4">
                <MiniStat icon={<Code className="h-5 w-5" />} label="Líneas de código" value={(structure?.lines_of_code ?? 0).toLocaleString()} />
                <MiniStat icon={<Layers className="h-5 w-5" />} label="Archivos fuente" value={String(structure?.total_source_files ?? 0)} />
                <MiniStat icon={<Gauge className="h-5 w-5" />} label="Complejidad media" value={complexity.average ? String(complexity.average) : "—"} />
                <MiniStat icon={<Shield className="h-5 w-5" />} label="Hallazgos totales" value={String(items.length)} accent="text-aqua-400" />
              </div>
            </div>

            {/* TABS */}
            <div className="flex flex-wrap gap-1.5 rounded-xl border border-white/[0.08] bg-ink-850 p-1.5">
              <TabPill icon={<Layers className="h-4 w-4" />} active={tab === "overview"} onClick={() => setTab("overview")}>
                Overview
              </TabPill>
              <TabPill icon={<Sparkles className="h-4 w-4" />} active={tab === "insights"} onClick={() => setTab("insights")}>
                Insights IA
              </TabPill>
              <TabPill icon={<Gauge className="h-4 w-4" />} active={tab === "quality"} onClick={() => setTab("quality")} count={qualityCount}>
                Calidad
              </TabPill>
              <TabPill icon={<Shield className="h-4 w-4" />} active={tab === "security"} onClick={() => setTab("security")} count={securityCount} danger>
                Seguridad
              </TabPill>
              <TabPill icon={<FileText className="h-4 w-4" />} active={tab === "docs"} onClick={() => setTab("docs")}>
                Docs
              </TabPill>
            </div>

            <div className="animate-fade-up">
              {tab === "overview" && <OverviewTab result={result.data} />}
              {tab === "insights" && <InsightsTab result={result.data} />}
              {tab === "quality" && <QualityTab findings={items} />}
              {tab === "security" && <SecurityTab findings={items} />}
              {tab === "docs" && <DocsTab result={result.data} />}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function scoreVerdict(score: number | null): string {
  if (score == null) return "—";
  if (score >= 80) return "Excelente";
  if (score >= 60) return "Bueno";
  if (score >= 40) return "Mejorable";
  return "Requiere atención";
}

function ProcessingCard({ phase, pct, label }: { phase: string | null; pct: number; label: string }) {
  return (
    <div className="panel overflow-hidden">
      {/* cabecera de instrumento */}
      <div className="flex items-center justify-between border-b border-white/[0.06] px-6 py-3.5">
        <div className="flex items-center gap-2.5 font-mono text-xs text-slate-400">
          <span className="h-1.5 w-1.5 rounded-full bg-aqua-500 animate-blink-soft" />
          analizando
        </div>
        <span className="font-mono text-[11px] uppercase tracking-widest text-electric-400">en curso</span>
      </div>

      <div className="p-6">
        <div className="flex items-center gap-4">
          <div className="grid h-11 w-11 shrink-0 place-items-center rounded-lg border border-electric-500/30 text-electric-300">
            <Activity className="h-6 w-6" />
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <span className="font-display font-semibold text-white">{label}</span>
              <span className="font-mono text-sm text-electric-300">{pct}%</span>
            </div>
            <div className="mt-2.5">
              <ProgressBar value={pct} />
            </div>
          </div>
        </div>

        {/* timeline de fases */}
        <div className="mt-7 grid grid-cols-4 gap-3 sm:grid-cols-6 lg:grid-cols-11">
          {PHASES.map((p, i) => {
            const reached = pct > 0 && (p.key === phase || isPast(p.key, phase, pct));
            const current = p.key === phase;
            return (
              <div key={p.key} className="flex flex-col items-center gap-1.5 text-center">
                <span className="font-mono text-[10px] text-slate-600">{String(i + 1).padStart(2, "0")}</span>
                <span
                  className={`h-1.5 w-full rounded-full transition-colors ${
                    current ? "bg-electric-400" : reached ? "bg-electric-600" : "bg-white/10"
                  }`}
                />
                <span className={`font-mono text-[10px] leading-tight ${current ? "text-electric-300" : "text-slate-600"}`}>
                  {p.label.split(" ")[0]}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function isPast(key: string, phase: string | null, pct: number): boolean {
  if (!phase) return false;
  const order = PHASES.map((p) => p.key);
  return order.indexOf(key) < order.indexOf(phase) || pct >= 100;
}

function MiniStat({
  icon,
  label,
  value,
  accent = "text-electric-300",
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  accent?: string;
}) {
  return (
    <div className="flex items-center gap-3 bg-ink-850 p-5">
      <div className={`grid h-10 w-10 shrink-0 place-items-center rounded-lg border border-white/[0.08] bg-ink-900 ${accent}`}>
        {icon}
      </div>
      <div className="min-w-0">
        <div className="truncate font-display text-xl font-bold text-white">{value}</div>
        <div className="truncate font-mono text-[11px] text-slate-500">{label}</div>
      </div>
    </div>
  );
}

function TabPill({
  icon,
  active,
  onClick,
  children,
  count,
  danger,
}: {
  icon: React.ReactNode;
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
  count?: number;
  danger?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors ${
        active ? "bg-electric-500 text-white" : "text-slate-300 hover:bg-white/[0.05]"
      }`}
    >
      {icon}
      {children}
      {count != null && count > 0 && (
        <span
          className={`rounded px-1.5 font-mono text-[11px] ${
            active ? "bg-white/20" : danger ? "bg-red-500/15 text-red-300" : "bg-white/10 text-slate-300"
          }`}
        >
          {count}
        </span>
      )}
    </button>
  );
}
