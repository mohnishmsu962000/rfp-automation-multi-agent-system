from celery import Celery
from app.core.config import get_settings
#imports

settings = get_settings()

celery_app = Celery(
    "rfp_backend",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        'app.workers.tasks',
        'app.workers.rfp_tasks'
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)