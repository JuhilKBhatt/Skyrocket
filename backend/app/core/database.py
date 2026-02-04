# backend/app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create engine using the URL from your docker-compose environment variables
engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency for API endpoints to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()