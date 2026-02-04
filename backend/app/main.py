# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import settings as settings_router
import os

app = FastAPI(title=settings.PROJECT_NAME)

origins = [
    "http://localhost:5173", # Dev
    "http://localhost:80",   # Prod
    "http://localhost",      # (Standard)
    "http://127.0.0.1"
]

# ENABLE CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REGISTER ROUTER
app.include_router(settings_router.router)
