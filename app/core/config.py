from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "transactions_db"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: str
    REDIS_URL: str
    OPENROUTER_API: str

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
