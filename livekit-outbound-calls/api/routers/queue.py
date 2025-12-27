"""Queue health and management endpoints."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/queue", tags=["Queue"])


@router.get("/health")
async def queue_health():
    """
    Check Celery queue health by triggering a health check task.
    """
    try:
        from tasks_queue.tasks import health_check
        
        # Send task to Celery and wait for result (5 second timeout)
        result = health_check.apply_async()
        task_result = result.get(timeout=5)
        
        return {
            "status": "healthy",
            "celery": "connected",
            "task_id": result.id,
            "task_result": task_result,
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "celery": "disconnected",
                "error": str(e),
            }
        )


@router.get("/stats")
async def queue_stats():
    """
    Get Celery queue statistics.
    """
    try:
        from tasks_queue.celery_app import celery_app
        
        # Get registered tasks
        registered_tasks = list(celery_app.tasks.keys())
        
        # Filter out internal Celery tasks
        our_tasks = [t for t in registered_tasks if t.startswith("tasks_queue")]
        
        return {
            "status": "ok",
            "registered_tasks": our_tasks,
            "broker_url": celery_app.conf.broker_url.split("@")[-1] if celery_app.conf.broker_url else None,
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )
