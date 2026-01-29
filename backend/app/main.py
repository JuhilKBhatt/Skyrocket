from fastapi import FastAPI
from app.core.config import settings
import os

app = FastAPI(title=settings.PROJECT_NAME)

@app.get("/")
def readnY_root():
    return {
        "message": "Welcome to Project Skyrocket 🚀",
        "environment": "Production" if os.getenv("ALPACA_API_KEY") else "Development",
        "docs_url": "/docs"
    }

@app.get("/health")
def health_check():
    """
    Docker uses this to check if the backend is alive.
    """
    return {"status": "healthy", "database_url": settings.DATABASE_URL}

@app.get("/api/test")
def test_endpoint():
    return {"data": "This data came from the Python Backend!"}