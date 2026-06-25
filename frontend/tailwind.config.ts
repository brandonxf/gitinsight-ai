import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "SFMono-Regular", "monospace"],
      },
      colors: {
        // Azul eléctrico — color de marca.
        electric: {
          50: "#eef4ff",
          100: "#dbe6ff",
          200: "#bdd2ff",
          300: "#8eb2ff",
          400: "#5886ff",
          500: "#2f5dff", // primario
          600: "#1539f5",
          700: "#0e2ae1",
          800: "#1325b6",
          900: "#16258f",
          950: "#0d1457",
        },
        // Cian de acento (para gradientes y datos).
        aqua: {
          400: "#22d3ee",
          500: "#06b6d4",
          600: "#0891b2",
        },
        ink: {
          950: "#070b1c",
          900: "#0b1124",
          850: "#0f1730",
          800: "#141d3b",
          700: "#1d2747",
        },
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(47,93,255,0.25), 0 8px 40px -8px rgba(47,93,255,0.45)",
        "glow-sm": "0 0 24px -6px rgba(47,93,255,0.5)",
        card: "0 1px 2px rgba(16,24,40,0.06), 0 8px 24px -12px rgba(16,24,40,0.18)",
      },
      backgroundImage: {
        "grid-dark":
          "linear-gradient(to right, rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.04) 1px, transparent 1px)",
        "brand-gradient": "linear-gradient(120deg, #2f5dff 0%, #06b6d4 100%)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        float: {
          "0%,100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-12px)" },
        },
        "pulse-glow": {
          "0%,100%": { opacity: "0.5" },
          "50%": { opacity: "1" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
        "gradient-x": {
          "0%,100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.6s cubic-bezier(0.16,1,0.3,1) both",
        float: "float 6s ease-in-out infinite",
        "pulse-glow": "pulse-glow 4s ease-in-out infinite",
        shimmer: "shimmer 1.6s infinite",
        "gradient-x": "gradient-x 6s ease infinite",
      },
    },
  },
  plugins: [],
} satisfies Config;
