import { useEffect, useState } from "react";

/**
 * Indicador fijo abajo-centro que invita a desplazarse despacio para apreciar
 * la animación del hero. Se desvanece en cuanto el usuario empieza a hacer
 * scroll. Decorativo (aria-hidden).
 */
export function MouseScrollHint() {
  const [hidden, setHidden] = useState(false);

  useEffect(() => {
    const onScroll = () => setHidden(window.scrollY > 120);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div
      aria-hidden="true"
      className={`scroll-hint fixed bottom-6 left-1/2 z-[60] flex -translate-x-1/2 flex-col items-center gap-2 ${
        hidden ? "pointer-events-none translate-y-3 opacity-0" : "opacity-100"
      }`}
    >
      <svg
        width="26"
        height="40"
        viewBox="0 0 26 40"
        fill="none"
        className="text-slate-300"
        aria-hidden="true"
      >
        <rect x="1.5" y="1.5" width="23" height="37" rx="11.5" stroke="currentColor" strokeWidth="2" />
        <line className="animate-wheel" x1="13" y1="9" x2="13" y2="15" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      </svg>
      <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-400">
        Desplázate despacio
      </span>
    </div>
  );
}
