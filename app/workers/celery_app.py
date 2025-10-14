from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "rfp_backend",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.autodiscover_tasks(['app.workers'])