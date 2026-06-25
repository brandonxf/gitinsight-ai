import type { AnalysisResult, Finding } from "./api";
import { Badge, Card, RiskLevel, SeverityBadge } from "../../components/ui";

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

export function OverviewTab({ result }: { result: AnalysisResult }) {
  const { structure } = result;
  const langs = Object.entries(result.languages).sort((a, b) => b[1] - a[1]);
  const totalLangFiles = langs.reduce((acc, [, n]) => acc + n, 0) || 1;

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Resumen
        </h3>
        <dl className="space-y-2 text-sm">
          <Row label="Lenguaje principal" value={result.primary_language ?? "—"} />
          <Row label="Arquitectura" value={structure.architecture?.pattern ?? "—"} />
          <Row label="Líneas de código" value={(structure.lines_of_code ?? 0).toLocaleString()} />
          <Row label="Archivos fuente" value={String(structure.total_source_files ?? 0)} />
          <Row label="Tamaño" value={bytesToHuman(structure.total_size_bytes)} />
          <div className="flex justify-between">
            <dt className="text-slate-500">Nivel de riesgo</dt>
            <dd><RiskLevel level={result.risk_level} /></dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-500">Quality score</dt>
            <dd className="font-semibold">{result.quality_score ?? "—"}/100</dd>
          </div>
        </dl>
      </Card>

      <Card>
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Frameworks y tecnologías
        </h3>
        <div className="flex flex-wrap gap-2">
          {result.frameworks.length === 0 && (
            <span className="text-sm text-slate-400">Ninguno detectado.</span>
          )}
          {result.frameworks.map((fw) => (
            <Badge key={fw}>{fw}</Badge>
          ))}
        </div>
      </Card>

      <Card>
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Lenguajes
        </h3>
        <div className="space-y-2">
          {langs.length === 0 && <span className="text-sm text-slate-400">—</span>}
          {langs.map(([lang, count]) => (
            <div key={lang}>
              <div className="mb-1 flex justify-between text-sm">
                <span>{lang}</span>
                <span className="text-slate-500">{count} archivos</span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-slate-700"
                  style={{ width: `${(count / totalLangFiles) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Estructura
        </h3>
        <ul className="max-h-64 space-y-1 overflow-auto text-sm font-mono">
          {(structure.tree ?? []).map((node) => (
            <li key={node.name}>
              <span className={node.type === "dir" ? "text-slate-900" : "text-slate-600"}>
                {node.type === "dir" ? "📁" : "📄"} {node.name}
              </span>
              {node.children && node.children.length > 0 && (
                <ul className="ml-5 text-slate-500">
                  {node.children.slice(0, 12).map((child) => (
                    <li key={child.name}>
                      {child.type === "dir" ? "📁" : "📄"} {child.name}
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
    <div className="flex justify-between">
      <dt className="text-slate-500">{label}</dt>
      <dd className="font-medium text-slate-900">{value}</dd>
    </div>
  );
}

function FindingList({ findings }: { findings: Finding[] }) {
  if (findings.length === 0) {
    return (
      <Card>
        <p className="text-sm text-slate-500">No se encontraron hallazgos en esta categoría. 🎉</p>
      </Card>
    );
  }
  return (
    <div className="space-y-2">
      {findings.map((f) => (
        <Card key={f.id} className="!p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="mb-1 flex items-center gap-2">
                <SeverityBadge severity={f.severity} />
                {f.rule_id && (
                  <span className="text-xs font-mono text-slate-400">{f.rule_id}</span>
                )}
              </div>
              <p className="text-sm text-slate-800">{f.message}</p>
              {f.suggestion && (
                <p className="mt-1 text-xs text-slate-500">💡 {f.suggestion}</p>
              )}
            </div>
            {f.file_path && (
              <code className="shrink-0 text-xs text-slate-500">
                {f.file_path}
                {f.line_start ? `:${f.line_start}` : ""}
              </code>
            )}
          </div>
        </Card>
      ))}
    </div>
  );
}

const QUALITY_CATEGORIES = new Set(["bug", "code_smell", "complexity", "duplication"]);
const SECURITY_CATEGORIES = new Set(["secret", "vuln", "insecure_config"]);

export function QualityTab({ findings }: { findings: Finding[] }) {
  return <FindingList findings={findings.filter((f) => QUALITY_CATEGORIES.has(f.category))} />;
}

export function SecurityTab({ findings }: { findings: Finding[] }) {
  return <FindingList findings={findings.filter((f) => SECURITY_CATEGORIES.has(f.category))} />;
}
