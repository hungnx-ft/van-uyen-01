from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "VAN UYEN"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    SECRET_KEY: str = "development-only-change-this-secret-key-before-deploying"
    ALGORITHM: Literal["HS256"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, gt=0)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, gt=0)
    TOKEN_ISSUER: str = "van-uyen"
    TOKEN_AUDIENCE: str = "van-uyen-api"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/van_uyen_db"
    UPLOAD_DIR: str = "uploads"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    @model_validator(mode="after")
    def validate_production(self):
        if "*" in self.CORS_ORIGINS:
            raise ValueError("CORS_ORIGINS must list explicit frontend origins")
        if self.ENVIRONMENT == "production":
            if len(self.SECRET_KEY) < 32 or self.SECRET_KEY in {
                "development-only-change-this-secret-key-before-deploying",
                "supersecretkey_please_change_in_production",
            }:
                raise ValueError("Production requires a unique SECRET_KEY of at least 32 characters")
        return self


settings = Settings()
