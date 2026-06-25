from datetime import UTC, datetime

from app.workers.celery_app import celery


@celery.task(name="app.workers.tasks.ping.ping")
def ping() -> dict:
    """Tarea de prueba para verificar que el worker procesa la cola."""
    return {"pong": True, "at": datetime.now(UTC).isoformat()}
