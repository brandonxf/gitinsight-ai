# GitInsight AI

Plataforma web que analiza repositorios GitHub públicos con una combinación de
**análisis estático determinista** y **IA gratuita** (LLM local vía Ollama o free tier,
embeddings locales + RAG sobre PgVector).

> **Stack 100% gratuito y open-source.** Ver el documento de arquitectura completo en
> [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md).

## Estado

**Fase 1 — Pipeline determinista (sin IA).** El sistema clona un repo público de GitHub de
forma segura y ejecuta analizadores deterministas (tecnologías, estructura, calidad con Ruff,
complejidad ciclomática, seguridad con Bandit y detección de secretos), persiste los resultados
y los muestra en un dashboard con tabs (Overview / Quality / Security) con polling de progreso.
La capa de IA (síntesis, diagramas, chat RAG) llega en las Fases 2 y 3.

> Fase 0 (scaffolding: `docker compose up` levanta todo y `/api/v1/health` responde) completada.

## Stack

- **Frontend:** React + TypeScript + Vite + TailwindCSS + React Query
- **Backend:** Python + FastAPI + SQLAlchemy (async) + Alembic
- **Datos:** PostgreSQL 16 + pgvector · Redis 7
- **Colas:** Celery (worker + beat) + Flower
- **IA (gratis):** Ollama (local) / free tier OpenAI-compatible + embeddings locales
- **Infra:** Docker Compose + Nginx

## Requisitos

- Docker y Docker Compose
- (Opcional) Ollama para IA local — se levanta con el perfil `llm`

## Puesta en marcha

```bash
# 1. Copia la plantilla de entorno
cp .env.example .env

# 2. Levanta los servicios (sin LLM local)
make up

# 3. (Opcional) Levanta también Ollama y descarga el modelo
make up-llm
make pull-model

# 4. Aplica las migraciones (crea las tablas)
make migrate
```

### URLs

| Servicio | URL |
|---|---|
| App (vía Nginx) | http://localhost:8080 |
| API (directo) | http://localhost:8000/api/v1/health |
| Docs API (Swagger) | http://localhost:8000/docs |
| Frontend (directo) | http://localhost:5173 |
| Flower (colas) | http://localhost:5555 |

### Verificar la Fase 0

```bash
curl http://localhost:8000/api/v1/health
# -> {"status":"ok","checks":{"database":"ok","broker":"ok"}}

curl http://localhost:8000/api/v1/health/ping-task
# -> {"task_id":"...","queued":true}   (procesado por el worker Celery)
```

### Verificar la Fase 1

```bash
# 1. Inicia un análisis (202 + job_id)
curl -X POST http://localhost:8000/api/v1/analyses \
  -H "Content-Type: application/json" \
  -d '{"url":"https://github.com/owner/repo"}'

# 2. Sondea el estado hasta SUCCEEDED
curl http://localhost:8000/api/v1/analyses/<job_id>

# 3. Resultado agregado (lenguajes, frameworks, estructura, scores)
curl http://localhost:8000/api/v1/analyses/<job_id>/result

# 4. Hallazgos (filtros: ?category=secret&severity=high)
curl http://localhost:8000/api/v1/analyses/<job_id>/findings
```

O bien, desde la UI en http://localhost:8080: pega la URL del repo y observa el
dashboard con el progreso y las tabs Overview / Quality / Security.

## Comandos útiles

```bash
make help     # lista todos los comandos
make logs     # sigue los logs
make test     # tests del backend
make lint     # Ruff
make down     # detener todo
```

## Estructura

```
gitinsight-ai/
├── docs/ARQUITECTURA.md   # diseño técnico completo
├── backend/               # FastAPI + Celery
├── frontend/              # React + Vite
├── infra/                 # nginx, dockerfiles, init de postgres
└── docker-compose.yml
```
