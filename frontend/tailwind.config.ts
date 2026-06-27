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
        // Marca: iris (azul-violeta confiado), usado SÓLIDO, no como glow.
        electric: {
          50: "#eef0ff",
          100: "#e0e2ff",
          200: "#c4c7ff",
          300: "#a3a4ff",
          400: "#8385fb",
          500: "#5b5bd6", // primario
          600: "#4f46c9",
          700: "#4239a8",
          800: "#362f86",
          900: "#2c2a6b",
          950: "#1b1942",
        },
        // Señal cálida (ámbar) para lecturas de datos y contraste cálido/frío.
        aqua: {
          400: "#ffc24b",
          500: "#ffb020",
          600: "#e69100",
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
        "brand-gradient": "linear-gradient(115deg, #8385fb 0%, #5b5bd6 45%, #ffb020 130%)",
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
