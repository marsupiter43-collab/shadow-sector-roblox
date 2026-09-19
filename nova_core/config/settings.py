from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # LLM Settings
    ollama_url: str = Field(default="http://localhost:11434")
    model_name: str = Field(default="llama3")

    # Engine Settings
    idle_tick_seconds: int = Field(default=15)
    proactive_trigger_seconds: int = Field(default=30)

    # Optional .env file loading
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
