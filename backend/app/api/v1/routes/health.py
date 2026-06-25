from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import engine
from app.workers.celery_app import celery

router = APIRouter()


@router.get("/health")
async def health():
    """Liveness + readiness: comprueba DB y broker de Celery."""
    checks: dict[str, str] = {}

    # PostgreSQL
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["database"] = f"error: {exc}"

    # Redis / Celery broker
    try:
        celery.connection().ensure_connection(max_retries=1)
        checks["broker"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["broker"] = f"error: {exc}"

    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}


@router.get("/health/ping-task")
async def ping_task():
    """Encola la tarea de prueba 'ping' en Celery y devuelve su id."""
    from app.workers.tasks.ping import ping

    result = ping.delay()
    return {"task_id": result.id, "queued": True}
