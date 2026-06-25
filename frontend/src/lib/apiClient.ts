import axios from "axios";

// En dev, Vite/Nginx hacen proxy de /api hacia el backend.
export const apiClient = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});
