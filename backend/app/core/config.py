from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Skyrocket Trading Bot"
    # These match the variables in your docker-compose.yml
    DATABASE_URL: str
    ALPACA_API_KEY: str = "mn_test_key"
    ALPACA_SECRET_KEY: str = "mn_test_secret"

    class Config:
        case_sensitive = True

settings = Settings()