"""
Celery application configuration.
"""
import os
from celery import Celery

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

# Create Celery app
celery_app = Celery(
    "vobiz_queue",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks_queue.tasks"],
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Task tracking
    task_track_started=True,
    
    # Reliability
    task_acks_late=True,  # Acknowledge after task completion
    task_reject_on_worker_lost=True,  # Re-queue if worker dies
    
    # Timeouts
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=270,  # Soft limit before hard kill
    
    # Result expiration
    result_expires=3600,  # Results expire after 1 hour
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_concurrency=4,  # 4 concurrent tasks per worker
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
)

# Task routing
celery_app.conf.task_routes = {
    "tasks_queue.tasks.make_single_call": {"queue": "calls"},
    "tasks_queue.tasks.execute_campaign": {"queue": "campaigns"},
}
