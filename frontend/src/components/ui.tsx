import type { ReactNode } from "react";

import type { Severity } from "../features/analysis/api";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-xl border border-slate-200 bg-white p-5 shadow-sm ${className}`}>
      {children}
    </div>
  );
}

export function ProgressBar({ value }: { value: number }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
      <div
        className="h-full rounded-full bg-slate-900 transition-all duration-500"
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
}

const SEVERITY_STYLES: Record<Severity, string> = {
  critical: "bg-red-100 text-red-800 border-red-200",
  high: "bg-orange-100 text-orange-800 border-orange-200",
  medium: "bg-amber-100 text-amber-800 border-amber-200",
  low: "bg-sky-100 text-sky-800 border-sky-200",
  info: "bg-slate-100 text-slate-700 border-slate-200",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  const style = SEVERITY_STYLES[severity] ?? SEVERITY_STYLES.info;
  return (
    <span className={`inline-block rounded-md border px-2 py-0.5 text-xs font-medium ${style}`}>
      {severity}
    </span>
  );
}

export function Badge({ children }: { children: ReactNode }) {
  return (
    <span className="inline-block rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
      {children}
    </span>
  );
}

const RISK_STYLES: Record<string, string> = {
  high: "text-red-600",
  medium: "text-amber-600",
  low: "text-green-600",
};

export function RiskLevel({ level }: { level: string | null }) {
  if (!level) return <span className="text-slate-400">—</span>;
  return <span className={`font-semibold capitalize ${RISK_STYLES[level] ?? ""}`}>{level}</span>;
}
