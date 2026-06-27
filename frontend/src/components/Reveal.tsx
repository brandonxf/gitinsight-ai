import { useRef, type ReactNode } from "react";
import { motion, useInView } from "framer-motion";

/**
 * Aparición al hacer scroll, con el mismo estilo que el portafolio:
 * fundido + desplazamiento hacia arriba (sin desenfoque), una sola vez,
 * disparado por `useInView` con margen negativo para anticipar la entrada.
 */
export function Reveal({
  children,
  className = "",
  delay = 0,
  y = 40,
  as = "div",
}: {
  children: ReactNode;
  className?: string;
  /** Retardo en milisegundos (para escalonar tarjetas). */
  delay?: number;
  /** Desplazamiento vertical inicial en px. */
  y?: number;
  as?: "div" | "section";
}) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const MotionTag = as === "section" ? motion.section : motion.div;

  return (
    <MotionTag
      ref={ref}
      className={className}
      initial={{ opacity: 0, y }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.8, delay: delay / 1000, ease: [0.25, 0.1, 0.25, 1] }}
    >
      {children}
    </MotionTag>
  );
}
