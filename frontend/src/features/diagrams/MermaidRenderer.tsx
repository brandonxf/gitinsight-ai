import { useEffect, useId, useRef, useState } from "react";
import mermaid from "mermaid";

let initialized = false;

function ensureInit() {
  if (initialized) return;
  mermaid.initialize({
    startOnLoad: false,
    theme: "dark",
    securityLevel: "strict",
    fontFamily: "inherit",
    themeVariables: {
      background: "transparent",
      primaryColor: "#1b2440",
      primaryBorderColor: "#2f5dff",
      primaryTextColor: "#e2e8f0",
      lineColor: "#475569",
    },
  });
  initialized = true;
}

/** Renderiza un diagrama Mermaid; muestra el código fuente si el parseo falla. */
export function MermaidRenderer({ code }: { code: string }) {
  const id = useId().replace(/:/g, "");
  const ref = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (!code?.trim()) return;
    ensureInit();
    mermaid
      .render(`mmd-${id}`, code)
      .then(({ svg }) => {
        if (!cancelled && ref.current) {
          ref.current.innerHTML = svg;
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Diagrama inválido");
      });
    return () => {
      cancelled = true;
    };
  }, [code, id]);

  if (error) {
    return (
      <div className="space-y-2">
        <p className="text-sm text-amber-400">No se pudo renderizar el diagrama.</p>
        <pre className="overflow-auto rounded-lg bg-ink-950/60 p-4 text-xs text-slate-400">
          {code}
        </pre>
      </div>
    );
  }

  return <div ref={ref} className="mermaid-container flex justify-center overflow-auto" />;
}
