import type { ReactNode } from "react";

import type { AnalysisResult } from "./api";
import { Card, SectionTitle } from "../../components/ui";
import { Diagram, FileText, GitBranch, Layers, Sparkles } from "../../components/icons";
import { MermaidRenderer } from "../diagrams/MermaidRenderer";
import { Markdown } from "./markdown";

// ---------- INSIGHTS (explicación IA + diagrama) ----------

export function InsightsTab({ result }: { result: AnalysisResult }) {
  const ai = result.metrics?.ai;
  const hasExplanation = Boolean(result.summary || result.purpose || result.modules?.length);
  const diagram = result.diagrams?.architecture;

  if (ai && ai.available === false && !hasExplanation && !diagram) {
    return <AiUnavailable error={ai.error} />;
  }

  return (
    <div className="grid gap-5 lg:grid-cols-3">
      {/* Resumen + propósito */}
      <Card className="lg:col-span-2">
        <SectionTitle icon={<Sparkles className="h-4 w-4" />}>Explicación del proyecto</SectionTitle>
        {result.summary ? (
          <p className="text-sm leading-relaxed text-slate-200">{result.summary}</p>
        ) : (
          <p className="text-sm text-slate-500">Sin resumen disponible.</p>
        )}
        {result.purpose && (
          <div className="mt-4 rounded-xl border border-electric-400/20 bg-electric-500/5 p-4">
            <p className="mb-1 text-xs uppercase tracking-wider text-electric-300">Propósito</p>
            <p className="text-sm text-slate-200">{result.purpose}</p>
          </div>
        )}
        {ai?.model && (
          <p className="mt-4 flex items-center gap-1.5 text-xs text-slate-500">
            <Sparkles className="h-3.5 w-3.5" /> Generado por IA · modelo{" "}
            <code className="text-slate-400">{ai.model}</code>
          </p>
        )}
      </Card>

      {/* Módulos */}
      <Card>
        <SectionTitle icon={<Layers className="h-4 w-4" />}>Módulos principales</SectionTitle>
        {result.modules?.length ? (
          <ul className="space-y-3">
            {result.modules.map((m) => (
              <li key={m.name} className="border-b border-white/5 pb-3 last:border-0 last:pb-0">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-semibold text-white">{m.name}</span>
                  {m.path && (
                    <code className="shrink-0 rounded bg-ink-950/60 px-1.5 py-0.5 font-mono text-[11px] text-electric-300">
                      {m.path}
                    </code>
                  )}
                </div>
                {m.responsibility && (
                  <p className="mt-1 text-xs text-slate-400">{m.responsibility}</p>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-500">Sin módulos identificados.</p>
        )}
      </Card>

      {/* Flujo */}
      {result.flow_description && (
        <Card className="lg:col-span-3">
          <SectionTitle icon={<GitBranch className="h-4 w-4" />}>Flujo principal</SectionTitle>
          <p className="text-sm leading-relaxed text-slate-200">{result.flow_description}</p>
        </Card>
      )}

      {/* Diagrama de arquitectura */}
      {diagram && (
        <Card className="lg:col-span-3">
          <div className="flex items-center justify-between">
            <SectionTitle icon={<Diagram className="h-4 w-4" />}>Diagrama de arquitectura</SectionTitle>
            {result.diagrams?.source === "fallback" && (
              <span className="mb-4 text-xs text-slate-500">generado a partir de la estructura</span>
            )}
          </div>
          <div className="rounded-xl border border-white/5 bg-ink-950/40 p-4">
            <MermaidRenderer code={diagram} />
          </div>
        </Card>
      )}
    </div>
  );
}

function AiUnavailable({ error }: { error?: string }) {
  return (
    <Card className="flex flex-col items-center gap-3 py-14 text-center">
      <div className="grid h-14 w-14 place-items-center rounded-2xl bg-amber-500/15 text-amber-400">
        <Sparkles className="h-7 w-7" />
      </div>
      <p className="text-lg font-semibold text-white">IA no disponible</p>
      <p className="max-w-md text-sm text-slate-400">
        No se pudo generar la síntesis con IA para este análisis. Verifica que el modelo
        LLM (Ollama) esté levantado y descargado.
      </p>
      {error && <p className="max-w-md font-mono text-xs text-slate-600">{error}</p>}
    </Card>
  );
}

// ---------- DOCS (README generado) ----------

export function DocsTab({ result }: { result: AnalysisResult }) {
  const readme = result.generated_docs?.readme;
  if (!readme) {
    return (
      <Card className="flex flex-col items-center gap-3 py-14 text-center">
        <div className="grid h-14 w-14 place-items-center rounded-2xl bg-white/5 text-slate-400">
          <FileText className="h-7 w-7" />
        </div>
        <p className="text-lg font-semibold text-white">Sin documentación generada</p>
        <p className="max-w-sm text-sm text-slate-400">
          La generación de documentación requiere que la capa de IA esté disponible.
        </p>
      </Card>
    );
  }
  return (
    <Card>
      <div className="mb-4 flex items-center justify-between">
        <SectionTitle icon={<FileText className="h-4 w-4" />}>README generado</SectionTitle>
        <CopyButton text={readme} />
      </div>
      <Markdown source={readme} />
    </Card>
  );
}

function CopyButton({ text }: { text: string }): ReactNode {
  return (
    <button
      onClick={() => navigator.clipboard?.writeText(text)}
      className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-white/10"
    >
      Copiar Markdown
    </button>
  );
}
