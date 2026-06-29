# DataSense Backend - Celery
# Celery configuration
from celery import Celery
from app.core.config import settings

if settings.LOCAL_MODE:
    broker_url = 'memory://'
    result_backend = 'cache+memory://'
else:
    broker_url = settings.REDIS_URL
    result_backend = settings.REDIS_URL

celery_app = Celery(
    "worker",
    broker=broker_url,
    backend=result_backend,
    include=["app.worker.tasks"]
)

celery_app.conf.task_routes = {
    "app.worker.tasks.*": "main-queue"
}

if settings.LOCAL_MODE:
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = False
    celery_app.conf.task_store_eager_result = True
