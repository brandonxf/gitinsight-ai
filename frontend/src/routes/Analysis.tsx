import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  ArrowRight,
  Bolt,
  Code,
  Gauge,
  Github,
  Layers,
  Logo,
  Shield,
} from "../components/icons";
import { Card, ProgressBar, RiskPill, ScoreRing } from "../components/ui";
import { useFindings, useJobPolling, useResult } from "../features/analysis/hooks";
import { OverviewTab, QualityTab, SecurityTab } from "../features/analysis/tabs";

const PHASES = [
  { key: "clone", label: "Clonando repositorio" },
  { key: "tech_detect", label: "Detectando tecnologías" },
  { key: "structure", label: "Analizando estructura" },
  { key: "quality_ruff", label: "Evaluando calidad (Ruff)" },
  { key: "complexity", label: "Midiendo complejidad" },
  { key: "security_bandit", label: "Escaneando seguridad (Bandit)" },
  { key: "secret_scan", label: "Buscando secretos" },
  { key: "persist", label: "Guardando resultados" },
];
const PHASE_LABELS: Record<string, string> = Object.fromEntries(
  PHASES.map((p) => [p.key, p.label]).concat([["done", "Completado"], ["error", "Error"]]),
);

type Tab = "overview" | "quality" | "security";
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
    <div className="min-h-screen bg-ink-950 text-slate-200">
      {/* NAVBAR */}
      <header className="sticky top-0 z-30 border-b border-white/5 bg-ink-950/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3.5">
          <Link to="/" className="flex items-center gap-2.5">
            <Logo className="h-8 w-8" />
            <span className="text-lg font-extrabold tracking-tight text-white">
              GitInsight<span className="text-gradient"> AI</span>
            </span>
          </Link>
          <Link
            to="/"
            className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm font-medium text-slate-200 hover:bg-white/10"
          >
            Nuevo análisis <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </header>

      {/* glow bg */}
      <div className="relative">
        <div className="pointer-events-none absolute -top-24 left-1/2 h-72 w-[760px] -translate-x-1/2 rounded-full bg-electric-600/15 blur-[120px]" />

        <main className="relative mx-auto max-w-6xl px-6 py-8">
          {job.isError && (
            <Card className="border-red-500/30">
              <p className="text-sm text-red-400">No se pudo cargar el análisis (job no encontrado).</p>
            </Card>
          )}

          {/* PROCESANDO */}
          {!done && !failed && job.data && (
            <ProcessingCard
              phase={job.data.phase}
              pct={job.data.progress_pct}
              label={PHASE_LABELS[job.data.phase ?? ""] ?? "En cola…"}
            />
          )}

          {/* FALLIDO */}
          {failed && (
            <Card className="border-red-500/30">
              <div className="flex items-start gap-4">
                <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-red-500/15 text-red-400">
                  <Shield className="h-6 w-6" />
                </div>
                <div>
                  <h2 className="font-semibold text-white">El análisis falló</h2>
                  <p className="mt-1 text-sm text-red-300">
                    {job.data?.error_message ?? "Error desconocido."}
                  </p>
                  <Link to="/" className="btn-brand mt-4 !py-2 text-sm">
                    Intentar con otro repo
                  </Link>
                </div>
              </div>
            </Card>
          )}

          {/* RESULTADO */}
          {done && result.data && (
            <div className="animate-fade-up space-y-6">
              {/* HEADER DEL REPO */}
              <Card className="overflow-hidden !p-0">
                <div className="flex flex-col gap-6 p-6 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <div className="mb-2 flex flex-wrap items-center gap-2">
                      <RiskPill level={result.data.risk_level} />
                      <span className="chip border-electric-400/30 bg-electric-500/10 text-electric-200">
                        <Code className="h-3.5 w-3.5" />
                        {result.data.primary_language ?? "—"}
                      </span>
                    </div>
                    <h1 className="flex items-center gap-2 truncate text-2xl font-bold text-white">
                      <Github className="h-6 w-6 shrink-0 text-slate-400" />
                      <span className="truncate">
                        {repo?.owner}
                        <span className="text-slate-500">/</span>
                        {repo?.name}
                      </span>
                    </h1>
                    <a
                      href={repo?.url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-1 inline-block truncate font-mono text-sm text-slate-400 hover:text-electric-300"
                    >
                      {repo?.url}
                    </a>
                    {repo?.commit_sha && (
                      <p className="mt-1 font-mono text-xs text-slate-600">
                        commit {repo.commit_sha.slice(0, 10)}
                      </p>
                    )}
                  </div>
                  <div className="flex shrink-0 items-center gap-4">
                    <div className="text-right">
                      <p className="text-xs uppercase tracking-wider text-slate-500">Quality score</p>
                      <p className="text-sm text-slate-400">
                        {scoreVerdict(result.data.quality_score)}
                      </p>
                    </div>
                    <ScoreRing score={result.data.quality_score} />
                  </div>
                </div>

                {/* STAT TILES */}
                <div className="grid gap-px border-t border-white/5 bg-white/5 sm:grid-cols-2 lg:grid-cols-4">
                  <MiniStat icon={<Code className="h-5 w-5" />} label="Líneas de código" value={(structure?.lines_of_code ?? 0).toLocaleString()} />
                  <MiniStat icon={<Layers className="h-5 w-5" />} label="Archivos fuente" value={String(structure?.total_source_files ?? 0)} />
                  <MiniStat icon={<Gauge className="h-5 w-5" />} label="Complejidad media" value={complexity.average ? String(complexity.average) : "—"} />
                  <MiniStat icon={<Shield className="h-5 w-5" />} label="Hallazgos totales" value={String(items.length)} accent="text-amber-300" />
                </div>
              </Card>

              {/* TABS */}
              <div className="flex gap-1.5 rounded-xl border border-white/10 bg-white/5 p-1.5">
                <TabPill icon={<Layers className="h-4 w-4" />} active={tab === "overview"} onClick={() => setTab("overview")}>
                  Overview
                </TabPill>
                <TabPill icon={<Bolt className="h-4 w-4" />} active={tab === "quality"} onClick={() => setTab("quality")} count={qualityCount}>
                  Calidad
                </TabPill>
                <TabPill icon={<Shield className="h-4 w-4" />} active={tab === "security"} onClick={() => setTab("security")} count={securityCount} danger>
                  Seguridad
                </TabPill>
              </div>

              <div className="animate-fade-up">
                {tab === "overview" && <OverviewTab result={result.data} />}
                {tab === "quality" && <QualityTab findings={items} />}
                {tab === "security" && <SecurityTab findings={items} />}
              </div>
            </div>
          )}
        </main>
      </div>
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
    <Card className="overflow-hidden">
      <div className="flex items-center gap-4">
        <div className="relative grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-electric-500/15 text-electric-300">
          <span className="absolute inset-0 animate-ping rounded-xl bg-electric-500/20" />
          <Bolt className="relative h-6 w-6" />
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-white">{label}…</span>
            <span className="font-mono text-sm text-electric-300">{pct}%</span>
          </div>
          <div className="mt-2">
            <ProgressBar value={pct} />
          </div>
        </div>
      </div>

      {/* timeline de fases */}
      <div className="mt-6 grid grid-cols-4 gap-2 sm:grid-cols-8">
        {PHASES.map((p) => {
          const reached = pct > 0 && (p.key === phase || isPast(p.key, phase, pct));
          const current = p.key === phase;
          return (
            <div key={p.key} className="flex flex-col items-center gap-1.5 text-center">
              <span
                className={`h-2 w-full rounded-full transition-colors ${
                  current ? "bg-electric-400" : reached ? "bg-electric-600" : "bg-white/10"
                }`}
              />
              <span className={`text-[10px] leading-tight ${current ? "text-electric-300" : "text-slate-500"}`}>
                {p.label.split(" ")[0]}
              </span>
            </div>
          );
        })}
      </div>
    </Card>
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
    <div className="flex items-center gap-3 bg-ink-900/40 p-4">
      <div className={`grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-white/5 ${accent}`}>
        {icon}
      </div>
      <div className="min-w-0">
        <div className="truncate text-xl font-bold text-white">{value}</div>
        <div className="truncate text-xs text-slate-400">{label}</div>
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
      className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold transition ${
        active ? "bg-brand-gradient text-white shadow-glow-sm" : "text-slate-300 hover:bg-white/5"
      }`}
    >
      {icon}
      {children}
      {count != null && count > 0 && (
        <span
          className={`rounded-full px-1.5 text-xs ${
            active ? "bg-white/20" : danger ? "bg-red-500/20 text-red-300" : "bg-white/10 text-slate-300"
          }`}
        >
          {count}
        </span>
      )}
    </button>
  );
}
