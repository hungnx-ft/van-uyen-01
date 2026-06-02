import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import ClassVar

class Settings(BaseSettings):
    PROJECT_NAME: str = "VAN UYEN"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = "supersecretkey_please_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "van_uyen_db"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/van_uyen_db"

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
