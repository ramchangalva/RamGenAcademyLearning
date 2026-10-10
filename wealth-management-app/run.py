"""
Production runner script
"""
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=9000,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else 4,
        log_level="info" if not settings.DEBUG else "debug"
    )
