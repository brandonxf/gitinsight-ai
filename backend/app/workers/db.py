"""Acceso async a la DB desde tareas Celery (síncronas).

Celery ejecuta tareas en hilos/procesos sin event loop; usamos `asyncio.run`
con un engine efímero (NullPool) por ejecución para evitar problemas de
"future attached to a different loop" entre tareas.
"""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings


def run_async[T](coro_fn: Callable[[async_sessionmaker[AsyncSession]], Awaitable[T]]) -> T:
    """Ejecuta `coro_fn(sessionmaker)` en un event loop nuevo con engine efímero."""

    async def _runner() -> T:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
        try:
            return await coro_fn(sessionmaker)
        finally:
            await engine.dispose()

    return asyncio.run(_runner())
