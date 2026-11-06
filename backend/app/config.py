from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[2] / ".env", extra="ignore")

    openai_api_key: str = ""
    llm_model: str = ""
    llm_timeout_seconds: float = Field(default=60, ge=1, le=180)
    llm_max_output_tokens: int = Field(default=6000, ge=256, le=16000)

    @property
    def configured(self) -> bool:
        return bool(self.openai_api_key.strip() and self.llm_model.strip())
