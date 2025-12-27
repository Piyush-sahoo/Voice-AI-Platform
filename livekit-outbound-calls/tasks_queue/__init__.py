"""Tasks queue package for Celery task management."""
from .celery_app import celery_app

__all__ = ["celery_app"]
