from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    MODE: Literal["supabase", "selfhost"] = "supabase"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    DEBUG: bool = True

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 10080

    DATABASE_URL: str

    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    REDIS_URL: str = "redis://localhost:6379/0"

    STORAGE_BUCKET: str = "anpr-uploads"
    STORAGE_CROPS_BUCKET: str = "anpr-crops"

    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str = "anpr-uploads"

    WORKER_CONCURRENCY: int = 4
    WORKER_BATCH_SIZE: int = 10

    DETECTION_CONFIDENCE_THRESHOLD: float = 0.7
    FRAME_EXTRACTION_FPS: int = 2

    CORS_ORIGINS: str = "http://localhost:3000"

    PROMETHEUS_ENABLED: bool = True

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: Literal["json", "text"] = "json"

    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "changeme123"
    ADMIN_USERNAME: str = "admin"

    LICENSE_VALIDATION_URL: str = ""

    WEBHOOK_URL: str = ""
    EMAIL_SMTP_HOST: str = ""
    EMAIL_SMTP_PORT: int = 587
    EMAIL_FROM: str = "alerts@yourdomain.com"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
