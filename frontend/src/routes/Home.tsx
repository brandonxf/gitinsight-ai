import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { AxiosError } from "axios";

import {
  Activity,
  ArrowRight,
  ArrowUpRight,
  Boxes,
  Chat,
  Check,
  Code,
  Gauge,
  GitBranch,
  Github,
  Layers,
  Lock,
  Logo,
  Shield,
  Sparkles,
  Terminal,
} from "../components/icons";
import { apiClient } from "../lib/apiClient";
import { useStartAnalysis } from "../features/analysis/hooks";
import { useParallax } from "../lib/useParallax";

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
  { icon: Boxes, title: "Estructura y arquitectura", desc: "Árbol de carpetas y patrón arquitectónico inferido: monorepo, MVC, src-layout.", tag: "tree" },
  { icon: Layers, title: "Detección de tecnologías", desc: "Lenguajes, frameworks y dependencias a partir de manifiestos y extensiones.", tag: "manifests" },
  { icon: Gauge, title: "Calidad de código", desc: "Linting con Ruff, complejidad ciclomática y un quality score normalizado.", tag: "ruff" },
  { icon: Shield, title: "Seguridad", desc: "Bandit, detección de secretos por regex y entropía, y nivel de riesgo.", tag: "bandit" },
  { icon: Sparkles, title: "Síntesis con IA", desc: "Resumen, propósito y módulos del proyecto. Gratis con modelos locales.", tag: "ollama", soon: true },
  { icon: Chat, title: "Chat con el repo", desc: "Pregunta en lenguaje natural y recibe respuestas con citas a archivos.", tag: "rag", soon: true },
];

const STEPS = [
  { n: "01", title: "Pega la URL", desc: "Cualquier repositorio público de GitHub. Validación segura anti-SSRF." },
  { n: "02", title: "Análisis en workers", desc: "Clonado superficial y pipeline determinista, con progreso en tiempo real." },
  { n: "03", title: "Explora el informe", desc: "Overview, calidad, seguridad, IA y README, accionables por archivo." },
];

const STATS = [
  { value: "06", label: "analizadores" },
  { value: "100%", label: "open-source" },
  { value: "$0", label: "coste de IA" },
  { value: "<30s", label: "repo típico" },
];

export default function Home() {
  const [url, setUrl] = useState("");
  const start = useStartAnalysis();
  const heroRef = useParallax<HTMLElement>();

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
    <div className="min-h-screen bg-ink-950 text-slate-300">
      {/* NAVBAR */}
      <header className="sticky top-0 z-30 border-b border-white/[0.06] bg-ink-950/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-10">
          <a href="#top" className="flex items-center gap-2.5">
            <Logo className="h-7 w-7" />
            <span className="font-display text-base font-bold tracking-tight text-white">
              GitInsight<span className="text-electric-400"> AI</span>
            </span>
          </a>
          <nav className="hidden items-center gap-9 font-mono text-xs uppercase tracking-widest text-slate-400 md:flex">
            <a href="#capacidades" className="transition-colors hover:text-white">Capacidades</a>
            <a href="#proceso" className="transition-colors hover:text-white">Proceso</a>
            <a href="#analizar" className="transition-colors hover:text-white">Analizar</a>
          </nav>
          <div className="flex items-center gap-4">
            <span className="hidden items-center gap-2 font-mono text-[11px] uppercase tracking-wider text-slate-500 sm:flex">
              <span className={`h-1.5 w-1.5 rounded-full ${online ? "bg-emerald-400 animate-blink-soft" : "bg-amber-400"}`} />
              {online ? "operativo" : "comprobando"}
            </span>
            <a
              href="https://github.com/brandonxf/gitinsight-ai"
              target="_blank"
              rel="noreferrer"
              className="btn-ghost !py-2"
            >
              <Github className="h-4 w-4" /> <span className="hidden sm:inline">GitHub</span>
            </a>
          </div>
        </div>
      </header>

      {/* HERO */}
      <section id="top" ref={heroRef} className="relative overflow-hidden border-b border-white/[0.06]">
        {/* capas de fondo con parallax */}
        <div data-parallax="0.18" className="pointer-events-none absolute inset-0 bg-grid [mask-image:radial-gradient(ellipse_70%_60%_at_60%_30%,black,transparent)]" />
        <div data-parallax="0.28" data-parallax-mouse="22" className="pointer-events-none absolute -top-40 left-[58%] h-[460px] w-[620px] rounded-full bg-electric-600/18 blur-[130px]" />
        <div data-parallax="0.12" data-parallax-mouse="-32" className="pointer-events-none absolute right-[6%] top-44 h-64 w-64 rounded-full bg-aqua-500/12 blur-[120px]" />

        <div className="relative mx-auto grid max-w-7xl items-center gap-14 px-6 py-20 lg:grid-cols-[1.05fr_0.95fr] lg:gap-10 lg:px-10 lg:py-28">
          {/* columna izquierda: tesis */}
          <div className="animate-fade-up">
            <p className="eyebrow">
              <span className="h-px w-7 bg-electric-500" />
              Análisis estático · Síntesis con IA
            </p>
            <h1 className="mt-6 font-display text-5xl font-bold leading-[1.04] tracking-[-0.02em] text-white sm:text-6xl">
              Lee cualquier repositorio
              <br />
              como si lo hubieras
              <br />
              <span className="text-gradient">escrito tú.</span>
            </h1>
            <p className="mt-7 max-w-md text-base leading-relaxed text-slate-400">
              GitInsight disecciona un repo público de GitHub y te entrega su arquitectura,
              calidad y seguridad. Lo determinista es gratis e instantáneo; la IA razona
              sobre el resto.
            </p>

            {/* input instrumento */}
            <form
              id="analizar"
              onSubmit={(e) => {
                e.preventDefault();
                submit(url);
              }}
              className="mt-9 max-w-lg"
            >
              <div className="panel flex items-center gap-2 p-1.5 focus-within:border-electric-500/60 focus-within:shadow-ring-iris">
                <span className="hidden select-none items-center gap-1.5 pl-3 font-mono text-xs text-slate-500 sm:flex">
                  <Terminal className="h-4 w-4" />
                  repo
                </span>
                <input
                  type="url"
                  required
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="github.com/owner/repo"
                  className="min-w-0 flex-1 bg-transparent px-3 py-2.5 font-mono text-sm text-white placeholder:text-slate-600 focus:outline-none"
                />
                <button type="submit" disabled={start.isPending} className="btn-brand whitespace-nowrap">
                  {start.isPending ? "Iniciando" : "Analizar"}
                  {!start.isPending && <ArrowRight className="h-4 w-4" />}
                </button>
              </div>
              {errorMessage && <p className="mt-3 text-sm text-red-400">{errorMessage}</p>}
            </form>

            <div className="mt-5 flex flex-wrap items-center gap-2">
              <span className="readout text-slate-600">prueba:</span>
              {SAMPLE_REPOS.map((r) => (
                <button
                  key={r}
                  onClick={() => {
                    setUrl(r);
                    submit(r);
                  }}
                  className="chip-mono transition-colors hover:border-electric-500/40 hover:text-white"
                >
                  {r.replace("https://github.com/", "")}
                </button>
              ))}
            </div>
          </div>

          {/* columna derecha: instrumento (firma) */}
          <div className="animate-fade-up [animation-delay:120ms]">
            <ScanInstrument />
          </div>
        </div>

        {/* tira de medidas */}
        <div className="relative border-t border-white/[0.06]">
          <div className="mx-auto grid max-w-7xl grid-cols-2 divide-x divide-white/[0.06] px-6 sm:grid-cols-4 lg:px-10">
            {STATS.map((s) => (
              <div key={s.label} className="px-2 py-6 text-center sm:py-7">
                <div className="font-display text-3xl font-bold text-white">{s.value}</div>
                <div className="mt-1 font-mono text-[11px] uppercase tracking-widest text-slate-500">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CAPACIDADES */}
      <section id="capacidades" className="mx-auto max-w-7xl px-6 py-24 lg:px-10">
        <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr]">
          <div className="lg:sticky lg:top-28 lg:self-start">
            <p className="eyebrow"><span className="h-px w-7 bg-electric-500" />Capacidades</p>
            <h2 className="mt-5 font-display text-3xl font-bold leading-tight tracking-tight text-white sm:text-4xl">
              Lo que un linter, un parser y una regex resuelven, sin gastar un token.
            </h2>
            <p className="mt-5 max-w-sm text-slate-400">
              El análisis determinista es rápido, gratis y reproducible. La IA se reserva
              para lo que de verdad necesita razonamiento.
            </p>
            <div className="mt-7 flex items-center gap-2">
              <span className="chip-mono">determinista</span>
              <ArrowRight className="h-4 w-4 text-slate-600" />
              <span className="chip-mono text-aqua-400">ia</span>
            </div>
          </div>

          <div className="panel divide-y divide-white/[0.06] overflow-hidden">
            {FEATURES.map((f) => (
              <div key={f.title} className="group flex items-start gap-5 p-6 transition-colors hover:bg-ink-800">
                <div className="grid h-11 w-11 shrink-0 place-items-center rounded-lg border border-white/[0.08] bg-ink-900 text-electric-300 transition-colors group-hover:border-electric-500/40 group-hover:text-electric-200">
                  <f.icon className="h-5 w-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <h3 className="font-display font-semibold text-white">{f.title}</h3>
                    <span className="font-mono text-[11px] text-slate-600">{f.tag}</span>
                    {f.soon && (
                      <span className="rounded border border-aqua-500/30 px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wide text-aqua-400">
                        pronto
                      </span>
                    )}
                  </div>
                  <p className="mt-1.5 text-sm leading-relaxed text-slate-400">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PROCESO — secuencia real, por eso va numerada */}
      <section id="proceso" className="border-y border-white/[0.06] bg-ink-900/40">
        <div className="mx-auto max-w-7xl px-6 py-24 lg:px-10">
          <div className="mb-14 flex flex-col justify-between gap-6 sm:flex-row sm:items-end">
            <div>
              <p className="eyebrow"><span className="h-px w-7 bg-electric-500" />Proceso</p>
              <h2 className="mt-5 font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
                Tres pasos, cero fricción.
              </h2>
            </div>
            <p className="max-w-xs text-sm text-slate-500">
              Del enlace al informe sin registro, sin configuración y sin tarjeta.
            </p>
          </div>
          <div className="grid gap-px overflow-hidden rounded-xl border border-white/[0.06] bg-white/[0.06] md:grid-cols-3">
            {STEPS.map((s) => (
              <div key={s.n} className="bg-ink-850 p-8">
                <div className="flex items-baseline gap-3">
                  <span className="font-mono text-sm text-electric-400">{s.n}</span>
                  <span className="h-px flex-1 bg-white/[0.08]" />
                </div>
                <h3 className="mt-6 font-display text-lg font-semibold text-white">{s.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-400">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* STACK */}
      <section className="mx-auto max-w-7xl px-6 py-24 lg:px-10">
        <div className="grid items-center gap-12 lg:grid-cols-2">
          <div>
            <p className="eyebrow"><span className="h-px w-7 bg-electric-500" />Stack</p>
            <h2 className="mt-5 font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
              100% libre, de la API al modelo.
            </h2>
            <p className="mt-5 max-w-md text-slate-400">
              FastAPI, Celery, PostgreSQL + pgvector, Redis, React y Vite. La capa de IA es
              agnóstica del proveedor: corre modelos locales con Ollama o un free tier, sin
              tarjeta de crédito.
            </p>
            <ul className="mt-8 space-y-4">
              {[
                "Clonado seguro: superficial, sin hooks y con límites de tamaño",
                "Pipeline asíncrono con progreso en tiempo real",
                "Hallazgos unificados por categoría y severidad",
              ].map((t) => (
                <li key={t} className="flex items-start gap-3 text-sm text-slate-300">
                  <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded border border-emerald-500/30 text-emerald-400">
                    <Check className="h-3 w-3" />
                  </span>
                  {t}
                </li>
              ))}
            </ul>
          </div>
          <div className="grid grid-cols-2 gap-px overflow-hidden rounded-xl border border-white/[0.06] bg-white/[0.06]">
            {[
              { icon: Code, label: "FastAPI + Celery", tag: "api · workers" },
              { icon: Layers, label: "PostgreSQL + pgvector", tag: "datos · vectores" },
              { icon: Lock, label: "Bandit + secretos", tag: "seguridad" },
              { icon: GitBranch, label: "React + Vite", tag: "frontend" },
            ].map((it) => (
              <div key={it.label} className="bg-ink-850 p-6">
                <it.icon className="h-5 w-5 text-electric-300" />
                <div className="mt-4 font-display text-sm font-semibold text-white">{it.label}</div>
                <div className="mt-1 font-mono text-[11px] text-slate-600">{it.tag}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-white/[0.06]">
        <div className="mx-auto max-w-7xl px-6 py-24 text-center lg:px-10">
          <Activity className="mx-auto h-8 w-8 text-electric-400" />
          <h2 className="mt-6 font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Pon un repositorio bajo el microscopio.
          </h2>
          <p className="mx-auto mt-4 max-w-md text-slate-400">
            Sin registro. Pega una URL y recibe el informe completo en segundos.
          </p>
          <a href="#analizar" className="btn-brand mt-8">
            Empezar ahora <ArrowRight className="h-4 w-4" />
          </a>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-white/[0.06]">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-6 py-9 text-sm text-slate-500 sm:flex-row lg:px-10">
          <div className="flex items-center gap-2.5">
            <Logo className="h-6 w-6" />
            <span className="font-display font-semibold text-slate-300">GitInsight AI</span>
            <span className="font-mono text-xs text-slate-600">· fase 1</span>
          </div>
          <a
            href="https://github.com/brandonxf/gitinsight-ai"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 font-mono text-xs text-slate-500 transition-colors hover:text-slate-300"
          >
            open-source en GitHub <ArrowUpRight className="h-3.5 w-3.5" />
          </a>
        </div>
      </footer>
    </div>
  );
}

/* ----------------------------------------------------------------------------
 * Firma: instrumento de "escaneo" que disecciona un repo por estratos.
 * Una línea de barrido recorre los estratos mientras se completan sus lecturas.
 * -------------------------------------------------------------------------- */

const STRATA = [
  { icon: Boxes, label: "structure", value: "142 archivos", bars: [5, 8, 4, 7, 6, 9, 5, 7, 4, 6], tone: "bg-electric-500/70" },
  { icon: Gauge, label: "quality", value: "score 86", bars: [6, 4, 7, 5, 8, 5, 6, 7, 5, 8], tone: "bg-electric-400/70" },
  { icon: Shield, label: "security", value: "0 secretos", bars: [3, 5, 4, 6, 4, 5, 3, 6, 4, 5], tone: "bg-emerald-500/70" },
  { icon: Sparkles, label: "synthesis", value: "IA lista", bars: [7, 9, 6, 8, 7, 9, 6, 8, 7, 9], tone: "bg-aqua-500/70" },
];

function ScanInstrument() {
  return (
    <div className="panel relative overflow-hidden shadow-panel-lg" aria-hidden="true">
      {/* cabecera del instrumento */}
      <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-3">
        <div className="flex items-center gap-2 font-mono text-xs text-slate-400">
          <span className="h-1.5 w-1.5 rounded-full bg-aqua-500 animate-blink-soft" />
          repo ▸ pallets/flask
        </div>
        <span className="font-mono text-[11px] uppercase tracking-widest text-electric-400">scanning</span>
      </div>

      {/* estratos + línea de barrido */}
      <div className="relative px-5 py-5">
        <div className="scanline" />
        <div className="space-y-4">
          {STRATA.map((s, i) => (
            <div key={s.label} className="flex items-center gap-3">
              <div className="flex w-28 shrink-0 items-center gap-2 font-mono text-xs text-slate-400">
                <s.icon className="h-4 w-4 text-slate-500" />
                {s.label}
              </div>
              <div className="flex h-9 flex-1 items-end gap-1">
                {s.bars.map((h, j) => (
                  <span
                    key={j}
                    className={`flex-1 origin-bottom rounded-sm animate-bar-fill ${s.tone}`}
                    style={{ height: `${h * 10}%`, animationDelay: `${i * 180 + j * 40}ms` }}
                  />
                ))}
              </div>
              <div className="w-24 shrink-0 text-right font-mono text-[11px] text-slate-300">{s.value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* pie de lectura */}
      <div className="flex items-center justify-between border-t border-white/[0.06] px-5 py-3 font-mono text-[11px] text-slate-500">
        <span>determinista · 6 analizadores</span>
        <span className="text-emerald-400">● riesgo bajo</span>
      </div>
    </div>
  );
}
