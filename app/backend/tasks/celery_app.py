from celery import Celery
from celery.schedules import crontab

from app.backend.core.config import settings

celery_app = Celery(
    "ucuzbot",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Baku",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    "check-all-alerts": {
        "task": "app.backend.tasks.price_check.check_all_alerts",
        "schedule": crontab(minute=0, hour=f"*/{settings.PRICE_CHECK_INTERVAL_HOURS}"),
    },
    "cleanup-old-records": {
        "task": "app.backend.tasks.cleanup.cleanup_old_price_records",
        "schedule": crontab(minute=0, hour=3),
    },
}

celery_app.conf.include = [
    "app.backend.tasks.price_check",
    "app.backend.tasks.cleanup",
]
