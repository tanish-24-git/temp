from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://compliance_user:compliance_pass@localhost:5432/compliance_db"

    # Ollama
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b"
    ollama_timeout: int = 30
    ollama_max_retries: int = 3

    # CORS
    api_cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Application
    environment: str = "development"
    log_level: str = "INFO"

    # File Upload
    max_upload_size: int = 52428800  # 50MB
    upload_dir: str = "./uploads"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
