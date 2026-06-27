import { useEffect, useRef } from "react";

/**
 * Parallax ligero para una sección (p. ej. el hero de la landing).
 *
 * Devuelve un `ref` para el contenedor. Cualquier elemento descendiente con el
 * atributo `data-parallax` se desplaza al hacer scroll y al mover el ratón:
 *
 *   data-parallax="0.2"        // factor de scroll (px desplazados por px scroleado)
 *   data-parallax-mouse="24"   // amplitud del seguimiento del puntero, en px
 *
 * Usa requestAnimationFrame para no bloquear el scroll y respeta
 * `prefers-reduced-motion` (si está activo, no aplica ningún movimiento).
 */
export function useParallax<T extends HTMLElement = HTMLElement>() {
  const ref = useRef<T>(null);

  useEffect(() => {
    const root = ref.current;
    if (!root) return;

    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (reduce.matches) return;

    const layers = Array.from(
      root.querySelectorAll<HTMLElement>("[data-parallax]"),
    );
    if (!layers.length) return;

    let mx = 0; // posición del ratón normalizada en [-1, 1]
    let my = 0;
    let ticking = false;

    const apply = () => {
      ticking = false;
      const scrolled = -root.getBoundingClientRect().top; // px scroleados dentro del hero
      for (const el of layers) {
        const s = parseFloat(el.dataset.parallax || "0"); // factor de scroll
        const m = parseFloat(el.dataset.parallaxMouse || "0"); // amplitud de ratón (px)
        const x = mx * m;
        const y = scrolled * s + my * m;
        el.style.transform = `translate3d(${x.toFixed(2)}px, ${y.toFixed(2)}px, 0)`;
      }
    };

    const request = () => {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(apply);
      }
    };

    const onMouse = (e: MouseEvent) => {
      mx = (e.clientX / window.innerWidth) * 2 - 1;
      my = (e.clientY / window.innerHeight) * 2 - 1;
      request();
    };

    for (const el of layers) el.style.willChange = "transform";
    apply();
    window.addEventListener("scroll", request, { passive: true });
    window.addEventListener("mousemove", onMouse, { passive: true });
    window.addEventListener("resize", request);

    return () => {
      window.removeEventListener("scroll", request);
      window.removeEventListener("mousemove", onMouse);
      window.removeEventListener("resize", request);
    };
  }, []);

  return ref;
}
