# Edge de producción: compila el frontend (Vite) y lo sirve con Caddy,
# que además hace de reverse proxy del API y gestiona HTTPS automático.
# Contexto de build: raíz del repo (necesita acceso a ./frontend e ./infra).

FROM node:22-slim AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci || npm install
COPY frontend/ ./
RUN npm run build

FROM caddy:2-alpine
COPY --from=build /app/dist /srv
COPY infra/caddy/Caddyfile /etc/caddy/Caddyfile
