# DataSense Backend - Celery
# Celery configuration
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.task_routes = {
    "app.worker.tasks.*": "main-queue"
}

if settings.LOCAL_MODE:
    celery_app.conf.broker_url = 'memory://'
    celery_app.conf.result_backend = 'db+sqlite:///celery_results.sqlite'
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = False
    celery_app.conf.task_store_eager_result = True
