import { useState } from "react";
import { AxiosError } from "axios";

import {
  ArrowRight,
  ArrowUpRight,
  Boxes,
  Chat,
  Check,
  Code,
  FileText,
  Gauge,
  GitBranch,
  Layers,
  Lock,
  Logo,
  Shield,
  Sparkles,
  Terminal,
} from "../components/icons";
import { CinematicHero } from "../components/CinematicHero";
import { MouseScrollHint } from "../components/MouseScrollHint";
import { Reveal } from "../components/Reveal";
import { useStartAnalysis } from "../features/analysis/hooks";

const SAMPLE_REPOS = [
  "https://github.com/pallets/flask",
  "https://github.com/tiangolo/fastapi",
  "https://github.com/psf/requests",
];

const REPORT = [
  { icon: Layers, title: "Overview", desc: "Lenguajes, arquitectura inferida, estructura de carpetas y métricas del repo de un vistazo." },
  { icon: Sparkles, title: "Insights IA", desc: "Resumen, propósito y módulos del proyecto, más un diagrama de arquitectura en Mermaid." },
  { icon: Gauge, title: "Calidad", desc: "Hallazgos de Ruff, complejidad ciclomática y un quality score normalizado de 0 a 100." },
  { icon: Shield, title: "Seguridad", desc: "Vulnerabilidades con Bandit, secretos por regex y entropía, y un nivel de riesgo claro." },
  { icon: FileText, title: "Docs", desc: "Un README mejorado, redactado por IA y anclado en la evidencia real del repositorio." },
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

export default function Home() {
  const [url, setUrl] = useState("");
  const start = useStartAnalysis();

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

  return (
    <div className="w-full overflow-x-hidden bg-ink-950 text-slate-300">
      {/* HERO CINEMATOGRÁFICO (experiencia con scroll) */}
      <CinematicHero />

      {/* ANALIZAR — destino del CTA del hero */}
      <section id="analizar" className="border-t border-white/[0.06]">
        <Reveal className="mx-auto max-w-3xl px-6 py-24 text-center lg:px-10">
          <p className="eyebrow justify-center"><span className="h-px w-7 bg-electric-500" />Analizar</p>
          <h2 className="mt-5 font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Pega un repositorio y empieza.
          </h2>
          <p className="mx-auto mt-4 max-w-md text-slate-400">
            Cualquier repo público de GitHub. Sin registro, sin configuración y sin coste.
          </p>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              submit(url);
            }}
            className="mx-auto mt-9 max-w-lg"
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

          <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
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
        </Reveal>
      </section>

      {/* EL INFORME — qué obtienes */}
      <section className="border-t border-white/[0.06] bg-ink-900/40">
        <div className="mx-auto max-w-7xl px-6 py-24 lg:px-10">
          <Reveal className="mb-14 flex flex-col justify-between gap-6 sm:flex-row sm:items-end">
            <div>
              <p className="eyebrow"><span className="h-px w-7 bg-electric-500" />El informe</p>
              <h2 className="mt-5 font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
                Un repositorio, cinco perspectivas.
              </h2>
            </div>
            <p className="max-w-xs text-sm text-slate-500">
              Cada pestaña del informe responde una pregunta distinta sobre el código.
            </p>
          </Reveal>
          <div className="grid gap-px overflow-hidden rounded-xl border border-white/[0.06] bg-white/[0.06] md:grid-cols-2 lg:grid-cols-3">
            {REPORT.map((r, i) => (
              <Reveal key={r.title} delay={i * 70} className="group bg-ink-850 p-7 transition-colors hover:bg-ink-800">
                <div className="grid h-11 w-11 place-items-center rounded-lg border border-white/[0.08] bg-ink-900 text-electric-300 transition-colors group-hover:border-electric-500/40 group-hover:text-electric-200">
                  <r.icon className="h-5 w-5" />
                </div>
                <h3 className="mt-5 font-display text-lg font-semibold text-white">{r.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-400">{r.desc}</p>
              </Reveal>
            ))}
            <Reveal delay={REPORT.length * 70} className="flex flex-col justify-center bg-ink-850 p-7">
              <p className="font-display text-lg font-semibold text-white">Todo en un solo enlace.</p>
              <p className="mt-2 text-sm text-slate-400">
                Comparte el informe o vuelve a generarlo cuando el repo cambie.
              </p>
              <a href="#analizar" className="mt-4 inline-flex items-center gap-1.5 font-mono text-xs text-electric-300 hover:text-electric-200">
                Probar ahora <ArrowRight className="h-3.5 w-3.5" />
              </a>
            </Reveal>
          </div>
        </div>
      </section>

      {/* CAPACIDADES */}
      <section id="capacidades" className="mx-auto max-w-7xl px-6 py-24 lg:px-10">
        <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr]">
          <Reveal className="lg:sticky lg:top-16 lg:self-start">
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
              <span className="chip-mono text-electric-300">ia</span>
            </div>
          </Reveal>

          <div className="panel divide-y divide-white/[0.06] overflow-hidden">
            {FEATURES.map((f, i) => (
              <Reveal key={f.title} delay={i * 70} className="group flex items-start gap-5 p-6 transition-colors hover:bg-ink-800">
                <div className="grid h-11 w-11 shrink-0 place-items-center rounded-lg border border-white/[0.08] bg-ink-900 text-electric-300 transition-colors group-hover:border-electric-500/40 group-hover:text-electric-200">
                  <f.icon className="h-5 w-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <h3 className="font-display font-semibold text-white">{f.title}</h3>
                    <span className="font-mono text-[11px] text-slate-600">{f.tag}</span>
                    {f.soon && (
                      <span className="rounded border border-electric-500/30 px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wide text-electric-300">
                        pronto
                      </span>
                    )}
                  </div>
                  <p className="mt-1.5 text-sm leading-relaxed text-slate-400">{f.desc}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* PROCESO */}
      <section id="proceso" className="border-y border-white/[0.06] bg-ink-900/40">
        <div className="mx-auto max-w-7xl px-6 py-24 lg:px-10">
          <Reveal className="mb-14 flex flex-col justify-between gap-6 sm:flex-row sm:items-end">
            <div>
              <p className="eyebrow"><span className="h-px w-7 bg-electric-500" />Proceso</p>
              <h2 className="mt-5 font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
                Tres pasos, cero fricción.
              </h2>
            </div>
            <p className="max-w-xs text-sm text-slate-500">
              Del enlace al informe sin registro, sin configuración y sin tarjeta.
            </p>
          </Reveal>
          <div className="grid gap-px overflow-hidden rounded-xl border border-white/[0.06] bg-white/[0.06] md:grid-cols-3">
            {STEPS.map((s, i) => (
              <Reveal key={s.n} delay={i * 90} className="bg-ink-850 p-8">
                <div className="flex items-baseline gap-3">
                  <span className="font-mono text-sm text-electric-400">{s.n}</span>
                  <span className="h-px flex-1 bg-white/[0.08]" />
                </div>
                <h3 className="mt-6 font-display text-lg font-semibold text-white">{s.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-400">{s.desc}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* STACK */}
      <section className="mx-auto max-w-7xl px-6 py-24 lg:px-10">
        <div className="grid items-center gap-12 lg:grid-cols-2">
          <Reveal>
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
          </Reveal>
          <div className="grid grid-cols-2 gap-px overflow-hidden rounded-xl border border-white/[0.06] bg-white/[0.06]">
            {[
              { icon: Code, label: "FastAPI + Celery", tag: "api · workers" },
              { icon: Layers, label: "PostgreSQL + pgvector", tag: "datos · vectores" },
              { icon: Lock, label: "Bandit + secretos", tag: "seguridad" },
              { icon: GitBranch, label: "React + Vite", tag: "frontend" },
            ].map((it, i) => (
              <Reveal key={it.label} delay={i * 70} className="bg-ink-850 p-6">
                <it.icon className="h-5 w-5 text-electric-300" />
                <div className="mt-4 font-display text-sm font-semibold text-white">{it.label}</div>
                <div className="mt-1 font-mono text-[11px] text-slate-600">{it.tag}</div>
              </Reveal>
            ))}
          </div>
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

      {/* Indicador para desplazarse despacio */}
      <MouseScrollHint />
    </div>
  );
}
