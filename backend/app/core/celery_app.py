# DataSense Backend - Celery
# TODO: Celery/Redis asenkron kuyruk yönetimi eklenecek
from celery import Celery
from backend.app.core.config import settings

celery_app = Celery(
    "datasense_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Celery görevlerinin (tasks) nerede olduğunu otomatik taraması için yönlendirme yapıyoruz
celery_app.autodiscover_tasks(["backend.app.tasks"])