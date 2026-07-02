"""Configuration for the social match system."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    # Agnes AI API
    agnes_api_key: str = Field(default="sk-zizmPuVeRYNh4N8rI3fhulq2wXeuPf9SDDsUwCoMiw6dG4vs")
    agnes_base_url: str = "https://apihub.agnes-ai.com/v1"
    agnes_model: str = "agnes-2.0-flash"

    # Vector config
    vector_dim: int = 64

    # Temperatures
    collector_temp: float = 0.3
    matcher_temp: float = 0.2
    icebreaker_temp: float = 0.7

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Demo data path
    demo_data_path: str = "../data/demo_profiles.json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
