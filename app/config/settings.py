from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "InsightFlow"
    quality_alert_threshold: float = 70.0
    max_upload_size_mb: int = 5
    log_level: str = "INFO"
    enable_background_jobs: bool = True


settings = Settings()
