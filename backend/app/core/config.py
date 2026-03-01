# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Skyrocket Trading Bot"
    
    # Database
    DATABASE_URL: str
    
    # Alpaca Keys (Removing hardcoded defaults forces it to read from your .env)
    ALPACA_API_KEY: str
    ALPACA_SECRET_KEY: str
    ALPACA_BASE_URL: str = "https://paper-api.alpaca.markets"

    # This config tells Pydantic to look for a .env file if running locally,
    # but it will seamlessly use Docker's injected environment variables when in the container.
    model_config = SettingsConfigDict(
        env_file="../.env", 
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True
    )

settings = Settings()