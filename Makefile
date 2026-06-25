.DEFAULT_GOAL := help
COMPOSE := docker compose

.PHONY: help up down build logs ps restart migrate revision shell-backend test lint fmt pull-model

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

up: ## Levanta todos los servicios
	$(COMPOSE) up -d --build

up-llm: ## Levanta todos los servicios incluyendo Ollama (LLM local)
	$(COMPOSE) --profile llm up -d --build

down: ## Detiene y elimina los contenedores
	$(COMPOSE) down

build: ## Reconstruye las imágenes
	$(COMPOSE) build

logs: ## Sigue los logs de todos los servicios
	$(COMPOSE) logs -f

ps: ## Lista el estado de los servicios
	$(COMPOSE) ps

restart: ## Reinicia los servicios
	$(COMPOSE) restart

migrate: ## Aplica las migraciones de la base de datos
	$(COMPOSE) exec backend alembic upgrade head

revision: ## Crea una nueva migración autogenerada (uso: make revision m="mensaje")
	$(COMPOSE) exec backend alembic revision --autogenerate -m "$(m)"

shell-backend: ## Abre una shell dentro del contenedor backend
	$(COMPOSE) exec backend bash

test: ## Ejecuta los tests del backend
	$(COMPOSE) exec backend pytest

lint: ## Ejecuta Ruff (lint)
	$(COMPOSE) exec backend ruff check .

fmt: ## Formatea el código con Ruff
	$(COMPOSE) exec backend ruff format .

pull-model: ## Descarga el modelo LLM por defecto en Ollama
	$(COMPOSE) exec ollama ollama pull qwen2.5-coder:3b
