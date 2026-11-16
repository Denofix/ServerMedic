import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[2] / ".env", extra="ignore")

    openai_api_key: str = ""
    llm_model: str = ""
    llm_timeout_seconds: float = Field(default=60, ge=1, le=180)
    llm_max_output_tokens: int = Field(default=6000, ge=256, le=16000)
    public_demo: bool = Field(default_factory=lambda: os.getenv("VERCEL") == "1")
    demo_access_code: str = ""
    demo_requests_per_minute: int = Field(default=5, ge=1, le=60)
    demo_max_concurrent: int = Field(default=1, ge=1, le=4)

    @property
    def configured(self) -> bool:
        return bool(self.openai_api_key.strip() and self.llm_model.strip())

    @property
    def demo_access_configured(self) -> bool:
        return 16 <= len(self.demo_access_code.strip()) <= 128
