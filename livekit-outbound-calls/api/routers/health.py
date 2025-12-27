"""Health check endpoints."""
import os
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "vobiz-voice-platform",
        "version": "1.0.0",
    }


@router.get("/ready")
async def ready_check():
    """
    Readiness check - verifies all dependencies are available.
    Returns 200 if all dependencies are healthy, 503 if any are down.
    """
    checks = {}
    
    # Check MongoDB
    try:
        from database.connection import get_database
        db = get_database()
        await db.command("ping")
        checks["mongodb"] = "ok"
    except Exception as e:
        checks["mongodb"] = f"failed: {str(e)}"
    
    # Check Redis (if configured)
    redis_host = os.getenv("REDIS_HOST")
    if redis_host:
        try:
            import redis
            r = redis.Redis(host=redis_host, port=int(os.getenv("REDIS_PORT", 6379)))
            r.ping()
            checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = f"failed: {str(e)}"
    
    # Determine overall status
    all_ok = all(v == "ok" for v in checks.values())
    status = "ready" if all_ok else "degraded"
    
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={
            "status": status,
            "service": "vobiz-voice-platform",
            "checks": checks,
        }
    )
