import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    // Proxy del API en desarrollo (cuando se accede directo a Vite, sin Nginx)
    proxy: {
      "/api": {
        target: "http://backend:8000",
        changeOrigin: true,
      },
    },
  },
});
