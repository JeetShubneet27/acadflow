from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AcadFlow API"
    environment: str = "development"
    database_url: str = "sqlite:///./acadflow.db"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    storage_dir: str = "./storage"
    cors_origins: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
