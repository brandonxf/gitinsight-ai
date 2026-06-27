import type { ReactNode } from "react";

import type { Severity } from "../features/analysis/api";

export function Card({
  children,
  className = "",
  hover = false,
}: {
  children: ReactNode;
  className?: string;
  hover?: boolean;
}) {
  return (
    <div className={`glass ${hover ? "glass-hover" : ""} p-5 ${className}`}>{children}</div>
  );
}

export function SectionTitle({ icon, children }: { icon?: ReactNode; children: ReactNode }) {
  return (
    <h3 className="mb-4 flex items-center gap-2 font-mono text-[11px] font-medium uppercase tracking-[0.18em] text-electric-300">
      {icon}
      {children}
    </h3>
  );
}

export function ProgressBar({ value }: { value: number; animated?: boolean }) {
  return (
    <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-white/10">
      <div
        className="h-full rounded-full bg-electric-500 transition-all duration-700"
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
}

const SEVERITY_STYLES: Record<Severity, string> = {
  critical: "bg-red-500/15 text-red-300 border-red-500/30",
  high: "bg-orange-500/15 text-orange-300 border-orange-500/30",
  medium: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  low: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  info: "bg-slate-500/15 text-slate-300 border-slate-500/30",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  const style = SEVERITY_STYLES[severity] ?? SEVERITY_STYLES.info;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-semibold uppercase tracking-wide ${style}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {severity}
    </span>
  );
}

export function Badge({ children }: { children: ReactNode }) {
  return <span className="chip">{children}</span>;
}

const RISK_STYLES: Record<string, { text: string; ring: string; label: string }> = {
  high: { text: "text-red-300", ring: "border-red-500/40 bg-red-500/10", label: "Alto" },
  medium: { text: "text-amber-300", ring: "border-amber-500/40 bg-amber-500/10", label: "Medio" },
  low: { text: "text-emerald-300", ring: "border-emerald-500/40 bg-emerald-500/10", label: "Bajo" },
};

export function RiskPill({ level }: { level: string | null }) {
  if (!level) return <span className="text-slate-500">—</span>;
  const s = RISK_STYLES[level] ?? RISK_STYLES.low;
  return (
    <span className={`inline-flex items-center gap-2 rounded-md border px-2.5 py-1 font-mono text-xs font-medium uppercase tracking-wide ${s.ring} ${s.text}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      Riesgo {s.label}
    </span>
  );
}

/** Anillo de puntuación 0–100 con degradado de marca. */
export function ScoreRing({ score, size = 132 }: { score: number | null; size?: number }) {
  const value = score ?? 0;
  const r = (size - 16) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (value / 100) * c;
  const color = value >= 75 ? "#22c55e" : value >= 45 ? "#3b82f6" : "#f59e0b";
  return (
    <div className="relative grid place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} stroke="rgba(255,255,255,0.08)" strokeWidth="10" fill="none" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke={color}
          strokeWidth="10"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 1s cubic-bezier(0.16,1,0.3,1)" }}
        />
      </svg>
      <div className="absolute text-center">
        <div className="text-3xl font-extrabold text-white">{score ?? "—"}</div>
        <div className="text-[10px] font-medium uppercase tracking-widest text-slate-400">/ 100</div>
      </div>
    </div>
  );
}

export function StatTile({
  icon,
  label,
  value,
  accent = "text-electric-300",
}: {
  icon: ReactNode;
  label: string;
  value: ReactNode;
  accent?: string;
}) {
  return (
    <div className="glass glass-hover flex items-center gap-3 p-4">
      <div className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-white/5 ${accent}`}>
        {icon}
      </div>
      <div className="min-w-0">
        <div className="truncate text-lg font-bold text-white">{value}</div>
        <div className="truncate text-xs text-slate-400">{label}</div>
      </div>
    </div>
  );
}
