from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "GradeOps"
    secret_key: str = "gradeops-dev-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    database_url: str = "postgresql://gradeops:gradeops@localhost:5432/gradeops"
    upload_dir: str = "./uploads"
    openai_api_key: str = ""
    use_mock_ai: bool = True
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
