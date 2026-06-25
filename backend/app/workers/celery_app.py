from celery import Celery

from app.core.config import settings

celery = Celery(
    "gitinsight",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks.ping", "app.workers.tasks.analyze"],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_time_limit=600,
    task_soft_time_limit=540,
    worker_max_tasks_per_child=50,
    task_default_queue="analysis",
    task_routes={
        "app.workers.tasks.ping.*": {"queue": "maintenance"},
    },
)
