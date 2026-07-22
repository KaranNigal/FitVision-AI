import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "FitVision AI"
    API_V1_STR: str = "/api/v1"
    JWT_SECRET: str = "super_secret_hex_key_change_me_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 Hours
    
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres_secure_pass"
    POSTGRES_DB: str = "fitvision"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: str = "sqlite:///./fitvision.db"

    MEDIA_STORAGE_PATH: str = "./media"
    ALLOWED_ORIGINS: Union[str, List[str]] = "http://localhost:5173"

    @field_validator("ALLOWED_ORIGINS")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Create media directory if it doesn't exist
os.makedirs(settings.MEDIA_STORAGE_PATH, exist_ok=True)
os.makedirs(os.path.join(settings.MEDIA_STORAGE_PATH, "profile_pics"), exist_ok=True)
os.makedirs(os.path.join(settings.MEDIA_STORAGE_PATH, "workouts"), exist_ok=True)
os.makedirs(os.path.join(settings.MEDIA_STORAGE_PATH, "snapshots"), exist_ok=True)
