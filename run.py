"""
Simple script to run the TradePulse AI application
"""
import uvicorn
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    import sys
    import io
    # Fix encoding for Windows console
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    from app.core.config import settings
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Server will be available at: http://localhost:8888")
    print(f"API docs available at: http://localhost:8888/api/docs")
    print("-" * 60)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8888,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
