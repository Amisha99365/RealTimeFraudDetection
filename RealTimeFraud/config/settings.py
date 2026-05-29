import secrets

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "RealTimeFraud"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Security
    api_key: str = ""
    require_api_key: bool = True
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    public_rate_limit_requests: int = 20
    allowed_origins: str = "http://127.0.0.1:8000,http://localhost:8000"

    # Fraud thresholds
    high_amount_threshold: float = 10_000.0
    velocity_window_seconds: int = 300
    velocity_max_transactions: int = 5
    velocity_amount_threshold: float = 50_000.0
    risk_block_threshold: float = 0.75
    risk_review_threshold: float = 0.45

    @model_validator(mode="after")
    def ensure_api_key(self) -> "Settings":
        if not self.api_key:
            self.api_key = f"rtf_dev_{secrets.token_hex(16)}"
        return self

    @property
    def effective_api_key(self) -> str:
        return self.api_key

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
