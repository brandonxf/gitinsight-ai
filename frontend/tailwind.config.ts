import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        // Display con carácter técnico (no Inter por defecto).
        display: ['"Space Grotesk"', "ui-sans-serif", "system-ui", "sans-serif"],
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "SFMono-Regular", "monospace"],
      },
      colors: {
        // Marca: azul profesional sólido (sin degradados).
        electric: {
          50: "#eff5ff",
          100: "#dbe8fe",
          200: "#bfd7fe",
          300: "#93bbfd",
          400: "#609afa",
          500: "#3b82f6", // primario
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
          950: "#172554",
        },
        // Acento secundario: misma familia azul (tono más claro), nunca un 2º color.
        aqua: {
          400: "#609afa",
          500: "#3b82f6",
          600: "#2563eb",
        },
        // Lienzo grafito: casi negro neutro-frío, plano (sin brillo).
        ink: {
          950: "#0a0c11",
          900: "#0e1118",
          850: "#12161f",
          800: "#171c27",
          700: "#222936",
        },
      },
      boxShadow: {
        // Sombras nítidas y discretas (instrumento), nada de halos difusos.
        panel: "0 1px 0 0 rgba(255,255,255,0.03) inset, 0 1px 2px rgba(0,0,0,0.5)",
        "panel-lg": "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 24px 48px -24px rgba(0,0,0,0.8)",
        "ring-iris": "0 0 0 1px rgba(91,91,214,0.5), 0 0 0 4px rgba(91,91,214,0.15)",
      },
      backgroundImage: {
        // Retícula tipo plano técnico (blueprint).
        "grid-blueprint":
          "linear-gradient(to right, rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.035) 1px, transparent 1px)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(14px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        // Barrido del escáner del instrumento (firma).
        "scan-sweep": {
          "0%": { left: "2%", opacity: "0" },
          "8%": { opacity: "1" },
          "92%": { opacity: "1" },
          "100%": { left: "98%", opacity: "0" },
        },
        // Parpadeo sutil de "lectura" en curso.
        "blink-soft": {
          "0%,100%": { opacity: "0.35" },
          "50%": { opacity: "1" },
        },
        // Llenado de las barras de cada estrato al ser escaneado.
        "bar-fill": {
          "0%": { transform: "scaleX(0.05)" },
          "100%": { transform: "scaleX(1)" },
        },
        ticker: {
          "0%,100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-1px)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.55s cubic-bezier(0.16,1,0.3,1) both",
        "scan-sweep": "scan-sweep 3.6s cubic-bezier(0.5,0,0.5,1) infinite",
        "blink-soft": "blink-soft 1.4s ease-in-out infinite",
        "bar-fill": "bar-fill 1.2s cubic-bezier(0.16,1,0.3,1) both",
      },
    },
  },
  plugins: [],
} satisfies Config;
