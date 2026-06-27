import { useState } from "react";

import type { AnalysisResult, Finding, Severity } from "./api";
import { Badge, Card, SectionTitle, SeverityBadge } from "../../components/ui";
import { Code, File, Folder, GitBranch, Idea, Layers, Shield } from "../../components/icons";

function bytesToHuman(bytes?: number): string {
  if (!bytes) return "—";
  const units = ["B", "KB", "MB", "GB"];
  let n = bytes;
  let i = 0;
  while (n >= 1024 && i < units.length - 1) {
    n /= 1024;
    i++;
  }
  return `${n.toFixed(1)} ${units[i]}`;
}

// Colores por lenguaje (estilo GitHub).
const LANG_COLORS: Record<string, string> = {
  Python: "#3776ab",
  JavaScript: "#f1e05a",
  TypeScript: "#3178c6",
  Go: "#00add8",
  Rust: "#dea584",
  Java: "#b07219",
  Ruby: "#701516",
  PHP: "#4f5d95",
  "C#": "#178600",
  C: "#555555",
  "C++": "#f34b7d",
  Shell: "#89e051",
  SQL: "#e38c00",
  Vue: "#41b883",
  Svelte: "#ff3e00",
  Kotlin: "#a97bff",
  Swift: "#f05138",
  Scala: "#c22d40",
};

function langColor(lang: string): string {
  return LANG_COLORS[lang] ?? "#3b82f6";
}

// ---------- OVERVIEW ----------

export function OverviewTab({ result }: { result: AnalysisResult }) {
  const { structure } = result;
  const langs = Object.entries(result.languages).sort((a, b) => b[1] - a[1]);
  const totalLangFiles = langs.reduce((acc, [, n]) => acc + n, 0) || 1;

  return (
    <div className="grid gap-5 lg:grid-cols-3">
      {/* Resumen */}
      <Card className="lg:col-span-2">
        <SectionTitle icon={<Code className="h-4 w-4" />}>Resumen del proyecto</SectionTitle>
        <div className="grid gap-x-8 gap-y-3 sm:grid-cols-2">
          <Row label="Lenguaje principal" value={result.primary_language ?? "—"} />
          <Row label="Arquitectura" value={structure.architecture?.pattern ?? "—"} />
          <Row label="Líneas de código" value={(structure.lines_of_code ?? 0).toLocaleString()} />
          <Row label="Archivos fuente" value={String(structure.total_source_files ?? 0)} />
          <Row label="Archivos totales" value={String(structure.total_files ?? 0)} />
          <Row label="Tamaño del repo" value={bytesToHuman(structure.total_size_bytes)} />
        </div>

        {structure.architecture?.signals && structure.architecture.signals.length > 0 && (
          <div className="mt-5 border-t border-white/5 pt-4">
            <p className="mb-2 text-xs uppercase tracking-wider text-slate-500">Señales detectadas</p>
            <div className="flex flex-wrap gap-2">
              {structure.architecture.signals.map((s) => (
                <Badge key={s}>{s}</Badge>
              ))}
            </div>
          </div>
        )}
      </Card>

      {/* Frameworks */}
      <Card>
        <SectionTitle icon={<Layers className="h-4 w-4" />}>Tecnologías</SectionTitle>
        <div className="flex flex-wrap gap-2">
          {result.frameworks.length === 0 && (
            <span className="text-sm text-slate-500">Ninguna detectada en la raíz.</span>
          )}
          {result.frameworks.map((fw) => (
            <span
              key={fw}
              className="chip border-electric-400/30 bg-electric-500/10 text-electric-200"
            >
              {fw}
            </span>
          ))}
        </div>
      </Card>

      {/* Lenguajes */}
      <Card className="lg:col-span-2">
        <SectionTitle icon={<Code className="h-4 w-4" />}>Distribución de lenguajes</SectionTitle>
        {/* barra apilada */}
        <div className="mb-4 flex h-3 w-full overflow-hidden rounded-full bg-white/5">
          {langs.map(([lang, count]) => (
            <div
              key={lang}
              style={{ width: `${(count / totalLangFiles) * 100}%`, background: langColor(lang) }}
              title={`${lang} · ${count}`}
            />
          ))}
        </div>
        <div className="grid gap-2 sm:grid-cols-2">
          {langs.length === 0 && <span className="text-sm text-slate-500">—</span>}
          {langs.map(([lang, count]) => (
            <div key={lang} className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-2 text-slate-200">
                <span className="h-3 w-3 rounded-sm" style={{ background: langColor(lang) }} />
                {lang}
              </span>
              <span className="text-slate-400">
                {count} <span className="text-slate-600">·</span>{" "}
                {Math.round((count / totalLangFiles) * 100)}%
              </span>
            </div>
          ))}
        </div>
      </Card>

      {/* Estructura */}
      <Card>
        <SectionTitle icon={<GitBranch className="h-4 w-4" />}>Estructura</SectionTitle>
        <ul className="max-h-72 space-y-1 overflow-auto pr-1 text-sm">
          {(structure.tree ?? []).map((node) => (
            <li key={node.name}>
              <span className={`flex items-center gap-1.5 ${node.type === "dir" ? "font-medium text-electric-200" : "text-slate-300"}`}>
                {node.type === "dir" ? (
                  <Folder className="h-3.5 w-3.5 shrink-0 text-electric-400" />
                ) : (
                  <File className="h-3.5 w-3.5 shrink-0 text-slate-500" />
                )}
                {node.name}
              </span>
              {node.children && node.children.length > 0 && (
                <ul className="ml-5 mt-0.5 space-y-0.5 border-l border-white/5 pl-3 text-slate-400">
                  {node.children.slice(0, 14).map((child) => (
                    <li key={child.name} className="flex items-center gap-1.5">
                      {child.type === "dir" ? (
                        <Folder className="h-3.5 w-3.5 shrink-0 text-electric-400/70" />
                      ) : (
                        <File className="h-3.5 w-3.5 shrink-0 text-slate-600" />
                      )}
                      {child.name}
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-white/5 py-1.5">
      <dt className="text-sm text-slate-400">{label}</dt>
      <dd className="text-sm font-semibold text-white">{value}</dd>
    </div>
  );
}

// ---------- FINDINGS ----------

const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low", "info"];

function FindingList({ findings, kind }: { findings: Finding[]; kind: "quality" | "security" }) {
  const [filter, setFilter] = useState<Severity | "all">("all");

  const counts = SEVERITY_ORDER.reduce(
    (acc, s) => ({ ...acc, [s]: findings.filter((f) => f.severity === s).length }),
    {} as Record<Severity, number>,
  );
  const visible = filter === "all" ? findings : findings.filter((f) => f.severity === filter);
  const active = SEVERITY_ORDER.filter((s) => counts[s] > 0);

  if (findings.length === 0) {
    return (
      <Card className="flex flex-col items-center gap-3 py-14 text-center">
        <div className="grid h-14 w-14 place-items-center rounded-2xl bg-emerald-500/15 text-emerald-400">
          <Shield className="h-7 w-7" />
        </div>
        <p className="text-lg font-semibold text-white">Sin hallazgos</p>
        <p className="max-w-sm text-sm text-slate-400">
          {kind === "security"
            ? "No se detectaron secretos ni vulnerabilidades en el análisis estático."
            : "El código no disparó hallazgos de calidad. ¡Buen trabajo!"}
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* filtros por severidad */}
      <div className="flex flex-wrap items-center gap-2">
        <FilterChip active={filter === "all"} onClick={() => setFilter("all")}>
          Todos <span className="opacity-60">{findings.length}</span>
        </FilterChip>
        {active.map((s) => (
          <FilterChip key={s} active={filter === s} onClick={() => setFilter(s)}>
            <SeverityBadge severity={s} /> <span className="opacity-70">{counts[s]}</span>
          </FilterChip>
        ))}
      </div>

      <div className="space-y-2.5">
        {visible.map((f) => (
          <FindingCard key={f.id} f={f} />
        ))}
      </div>
    </div>
  );
}

function FilterChip({
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
      className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-medium transition ${
        active
          ? "border-electric-400/40 bg-electric-500/15 text-white"
          : "border-white/10 bg-white/5 text-slate-300 hover:bg-white/10"
      }`}
    >
      {children}
    </button>
  );
}

const SEVERITY_BAR: Record<Severity, string> = {
  critical: "bg-red-500",
  high: "bg-orange-500",
  medium: "bg-amber-500",
  low: "bg-sky-500",
  info: "bg-slate-500",
};

function FindingCard({ f }: { f: Finding }) {
  return (
    <div className="glass glass-hover relative overflow-hidden p-4 pl-5">
      <span className={`absolute inset-y-0 left-0 w-1 ${SEVERITY_BAR[f.severity] ?? "bg-slate-500"}`} />
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="mb-1.5 flex flex-wrap items-center gap-2">
            <SeverityBadge severity={f.severity} />
            <span className="rounded bg-white/5 px-1.5 py-0.5 text-xs font-medium uppercase text-slate-400">
              {f.category.replace("_", " ")}
            </span>
            {f.rule_id && (
              <span className="font-mono text-xs text-electric-300">{f.rule_id}</span>
            )}
          </div>
          <p className="text-sm text-slate-100">{f.message}</p>
          {f.suggestion && (
            <p className="mt-1.5 flex items-start gap-1.5 text-xs text-slate-400">
              <Idea className="mt-0.5 h-3.5 w-3.5 shrink-0 text-aqua-400" /> {f.suggestion}
            </p>
          )}
        </div>
        {f.file_path && (
          <code className="shrink-0 rounded-md bg-ink-950/60 px-2 py-1 font-mono text-xs text-slate-400">
            {f.file_path}
            {f.line_start ? <span className="text-electric-300">:{f.line_start}</span> : ""}
          </code>
        )}
      </div>
    </div>
  );
}

const QUALITY_CATEGORIES = new Set(["bug", "code_smell", "complexity", "duplication"]);
const SECURITY_CATEGORIES = new Set(["secret", "vuln", "insecure_config"]);

export function QualityTab({ findings }: { findings: Finding[] }) {
  return <FindingList kind="quality" findings={findings.filter((f) => QUALITY_CATEGORIES.has(f.category))} />;
}

export function SecurityTab({ findings }: { findings: Finding[] }) {
  return <FindingList kind="security" findings={findings.filter((f) => SECURITY_CATEGORIES.has(f.category))} />;
}
