from celery import Celery
from kombu import Queue
import os

# Env vars
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Include tasks module so tasks are registered on worker startup
celery_app.conf.include = ["backend.app.tasks"]

celery_app.conf.task_default_queue = "celery"

celery_app.conf.task_routes = {
    "backend.app.tasks.validate_document_task": {"queue": "validation-queue"},
    "backend.app.tasks.revalidate_folder_task": {"queue": "validation-queue"},
}

celery_app.conf.task_queues = [
    Queue("celery"),
    Queue("validation-queue"),
]

