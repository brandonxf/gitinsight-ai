import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { AxiosError } from "axios";

import {
  ArrowRight,
  Bolt,
  Chat,
  Check,
  Code,
  Diagram,
  Gauge,
  GitBranch,
  Github,
  Layers,
  Lock,
  Logo,
  Search,
  Shield,
  Sparkles,
} from "../components/icons";
import { apiClient } from "../lib/apiClient";
import { useStartAnalysis } from "../features/analysis/hooks";

interface HealthResponse {
  status: string;
  checks: Record<string, string>;
}

const SAMPLE_REPOS = [
  "https://github.com/pallets/flask",
  "https://github.com/tiangolo/fastapi",
  "https://github.com/psf/requests",
];

const FEATURES = [
  { icon: Layers, title: "Detección de tecnologías", desc: "Lenguajes, frameworks y dependencias a partir de manifiestos y extensiones." },
  { icon: GitBranch, title: "Estructura y arquitectura", desc: "Árbol de carpetas y patrón arquitectónico inferido (monorepo, MVC, src-layout…)." },
  { icon: Gauge, title: "Calidad de código", desc: "Linting con Ruff, complejidad ciclomática y un quality score normalizado." },
  { icon: Shield, title: "Seguridad", desc: "Análisis con Bandit, detección de secretos por regex + entropía y nivel de riesgo." },
  { icon: Sparkles, title: "Síntesis con IA", desc: "Resumen, propósito y módulos del proyecto. Gratis con modelos locales.", soon: true },
  { icon: Chat, title: "Chat con el repo", desc: "Pregunta en lenguaje natural y recibe respuestas con citas a archivos (RAG).", soon: true },
];

const STEPS = [
  { n: "01", title: "Pega la URL", desc: "Cualquier repositorio público de GitHub. Validación segura anti-SSRF." },
  { n: "02", title: "Análisis asíncrono", desc: "Clonado superficial y pipeline determinista en workers, con progreso en vivo." },
  { n: "03", title: "Explora el dashboard", desc: "Overview, calidad y seguridad con hallazgos accionables por archivo." },
];

const STATS = [
  { value: "6", label: "analizadores" },
  { value: "100%", label: "open-source" },
  { value: "$0", label: "coste de IA" },
  { value: "< 30s", label: "por repo típico" },
];

export default function Home() {
  const [url, setUrl] = useState("");
  const start = useStartAnalysis();

  const { data: health } = useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: async () => (await apiClient.get("/health")).data,
    refetchInterval: 15000,
  });

  function submit(value: string) {
    const v = value.trim();
    if (v) start.mutate(v);
  }

  const errorMessage =
    start.error instanceof AxiosError
      ? (start.error.response?.data?.detail ?? "No se pudo iniciar el análisis.")
      : start.error
        ? "No se pudo iniciar el análisis."
        : null;

  const online = health?.status === "ok";

  return (
    <div className="min-h-screen bg-ink-950 text-slate-200">
      {/* NAVBAR */}
      <header className="sticky top-0 z-30 border-b border-white/5 bg-ink-950/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3.5">
          <a href="#top" className="flex items-center gap-2.5">
            <Logo className="h-8 w-8" />
            <span className="text-lg font-extrabold tracking-tight text-white">
              GitInsight<span className="text-gradient"> AI</span>
            </span>
          </a>
          <nav className="hidden items-center gap-7 text-sm font-medium text-slate-300 md:flex">
            <a href="#features" className="hover:text-white">Capacidades</a>
            <a href="#how" className="hover:text-white">Cómo funciona</a>
            <a href="#analizar" className="hover:text-white">Analizar</a>
          </nav>
          <div className="flex items-center gap-3">
            <span className="hidden items-center gap-2 text-xs text-slate-400 sm:flex">
              <span className={`h-2 w-2 rounded-full ${online ? "bg-emerald-400 animate-pulse-glow" : "bg-amber-400"}`} />
              {online ? "Operativo" : "Comprobando…"}
            </span>
            <a
              href="https://github.com/brandonxf/gitinsight-ai"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm font-medium text-slate-200 transition hover:bg-white/10"
            >
              <Github className="h-4 w-4" /> <span className="hidden sm:inline">GitHub</span>
            </a>
          </div>
        </div>
      </header>

      {/* HERO */}
      <section id="top" className="relative overflow-hidden">
        {/* glows */}
        <div className="pointer-events-none absolute inset-0 bg-grid opacity-60" />
        <div className="pointer-events-none absolute -top-40 left-1/2 h-[520px] w-[820px] -translate-x-1/2 rounded-full bg-electric-500/25 blur-[120px]" />
        <div className="pointer-events-none absolute right-0 top-24 h-72 w-72 rounded-full bg-aqua-500/20 blur-[110px]" />

        <div className="relative mx-auto max-w-3xl px-6 pb-16 pt-20 text-center sm:pt-28">
          <div className="animate-fade-up">
            <span className="chip mx-auto mb-6 border-electric-400/30 bg-electric-500/10 text-electric-200">
              <Bolt className="h-4 w-4" /> Determinista primero · IA después · 100% gratis
            </span>
          </div>
          <h1 className="animate-fade-up text-4xl font-extrabold leading-[1.08] tracking-tight text-white sm:text-6xl">
            Entiende cualquier repositorio
            <br />
            <span className="text-gradient">en segundos, no en horas</span>
          </h1>
          <p className="animate-fade-up mx-auto mt-6 max-w-xl text-lg text-slate-300">
            GitInsight AI clona un repo público de GitHub y te entrega tecnologías,
            arquitectura, calidad y seguridad en un dashboard accionable.
          </p>

          {/* INPUT */}
          <form
            id="analizar"
            onSubmit={(e) => {
              e.preventDefault();
              submit(url);
            }}
            className="animate-fade-up mx-auto mt-9 max-w-xl"
          >
            <div className="glass flex items-center gap-2 p-2 shadow-glow">
              <Search className="ml-2 h-5 w-5 shrink-0 text-slate-400" />
              <input
                type="url"
                required
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://github.com/owner/repo"
                className="flex-1 bg-transparent px-1 py-2.5 text-white placeholder:text-slate-500 focus:outline-none"
              />
              <button type="submit" disabled={start.isPending} className="btn-brand whitespace-nowrap">
                {start.isPending ? "Iniciando…" : "Analizar"}
                {!start.isPending && <ArrowRight className="h-4 w-4" />}
              </button>
            </div>
            {errorMessage && <p className="mt-3 text-sm text-red-400">{errorMessage}</p>}
          </form>

          {/* sample repos */}
          <div className="animate-fade-up mt-5 flex flex-wrap items-center justify-center gap-2 text-sm">
            <span className="text-slate-500">Prueba con:</span>
            {SAMPLE_REPOS.map((r) => (
              <button
                key={r}
                onClick={() => {
                  setUrl(r);
                  submit(r);
                }}
                className="chip glass-hover hover:text-white"
              >
                <Github className="h-3.5 w-3.5" />
                {r.replace("https://github.com/", "")}
              </button>
            ))}
          </div>
        </div>

        {/* STATS STRIP */}
        <div className="relative mx-auto max-w-4xl px-6 pb-16">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {STATS.map((s) => (
              <div key={s.label} className="glass p-4 text-center">
                <div className="text-2xl font-extrabold text-gradient">{s.value}</div>
                <div className="mt-1 text-xs uppercase tracking-wider text-slate-400">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section id="features" className="relative mx-auto max-w-6xl px-6 py-20">
        <div className="mb-12 text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-electric-300">Capacidades</p>
          <h2 className="mt-2 text-3xl font-bold text-white sm:text-4xl">
            Todo lo que un linter, parser o regex resuelve — sin gastar tokens
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-slate-400">
            El análisis determinista es gratis, rápido y reproducible. La IA se reserva
            para síntesis y razonamiento, con modelos locales sin coste.
          </p>
        </div>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <div key={f.title} className="glass glass-hover group relative p-6">
              <div className="mb-4 grid h-12 w-12 place-items-center rounded-xl bg-electric-500/15 text-electric-300 transition group-hover:bg-electric-500/25">
                <f.icon className="h-6 w-6" />
              </div>
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-white">{f.title}</h3>
                {f.soon && (
                  <span className="rounded-full bg-aqua-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase text-aqua-400">
                    Próximamente
                  </span>
                )}
              </div>
              <p className="mt-2 text-sm leading-relaxed text-slate-400">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how" className="relative overflow-hidden border-y border-white/5 bg-ink-900/40">
        <div className="pointer-events-none absolute left-1/2 top-0 h-64 w-[700px] -translate-x-1/2 rounded-full bg-electric-600/10 blur-[120px]" />
        <div className="relative mx-auto max-w-6xl px-6 py-20">
          <div className="mb-12 text-center">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-electric-300">Cómo funciona</p>
            <h2 className="mt-2 text-3xl font-bold text-white sm:text-4xl">Tres pasos, cero fricción</h2>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {STEPS.map((s, i) => (
              <div key={s.n} className="relative">
                <div className="glass h-full p-7">
                  <div className="text-5xl font-black text-gradient">{s.n}</div>
                  <h3 className="mt-4 text-lg font-semibold text-white">{s.title}</h3>
                  <p className="mt-2 text-sm text-slate-400">{s.desc}</p>
                </div>
                {i < STEPS.length - 1 && (
                  <ArrowRight className="absolute -right-4 top-1/2 hidden h-7 w-7 -translate-y-1/2 text-electric-500/50 md:block" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* STACK / TRUST */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <div className="glass relative overflow-hidden p-8 sm:p-12">
          <div className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-aqua-500/20 blur-[90px]" />
          <div className="relative grid items-center gap-8 lg:grid-cols-2">
            <div>
              <h2 className="text-3xl font-bold text-white">Stack 100% libre y gratuito</h2>
              <p className="mt-4 text-slate-400">
                FastAPI, Celery, PostgreSQL + pgvector, Redis, React y Vite. La capa de IA
                es agnóstica del proveedor: corre modelos locales con Ollama o un free tier,
                sin tarjeta de crédito.
              </p>
              <ul className="mt-6 space-y-3">
                {[
                  "Clonado seguro: shallow, sin hooks, límites de tamaño",
                  "Pipeline asíncrono con progreso en tiempo real",
                  "Hallazgos unificados por categoría y severidad",
                ].map((t) => (
                  <li key={t} className="flex items-start gap-3 text-sm text-slate-300">
                    <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-emerald-500/15 text-emerald-400">
                      <Check className="h-3.5 w-3.5" />
                    </span>
                    {t}
                  </li>
                ))}
              </ul>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {[
                { icon: Code, label: "FastAPI + Celery" },
                { icon: Layers, label: "PostgreSQL + pgvector" },
                { icon: Lock, label: "Bandit + secretos" },
                { icon: Diagram, label: "React + Vite" },
              ].map((it) => (
                <div key={it.label} className="glass glass-hover flex items-center gap-3 p-4">
                  <it.icon className="h-5 w-5 text-electric-300" />
                  <span className="text-sm font-medium text-slate-200">{it.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-3xl px-6 pb-24 text-center">
        <h2 className="text-3xl font-bold text-white sm:text-4xl">¿Listo para diseccionar un repo?</h2>
        <p className="mt-3 text-slate-400">Sin registro. Pega una URL y obtén tu análisis.</p>
        <a href="#analizar" className="btn-brand mt-7">
          Empezar ahora <ArrowRight className="h-4 w-4" />
        </a>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-white/5">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-8 text-sm text-slate-500 sm:flex-row">
          <div className="flex items-center gap-2">
            <Logo className="h-6 w-6" />
            <span className="font-semibold text-slate-300">GitInsight AI</span>
            <span className="text-slate-600">· Fase 1</span>
          </div>
          <p>Construido con FastAPI · Celery · React. 100% open-source.</p>
        </div>
      </footer>
    </div>
  );
}
