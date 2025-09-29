from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings configuration."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Application Configuration
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/aive_db",
        alias="DATABASE_URL",
    )

    # Authentication
    jwt_secret_key: str = Field(
        default="your-super-secret-key-change-this-in-production",
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=30, alias="JWT_EXPIRE_MINUTES")

    # External APIs
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    pexels_api_key: str = Field(default="", alias="PEXELS_API_KEY")
    pixabay_api_key: str = Field(default="", alias="PIXABAY_API_KEY")

    # File Storage
    max_upload_size: int = Field(default=104857600, alias="MAX_UPLOAD_SIZE")  # 100MB
    allowed_audio_types: list[str] = Field(
        default=["audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav"],
        alias="ALLOWED_AUDIO_TYPES",
    )

    # CORS
    allowed_origins: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8080",
        ],
        alias="ALLOWED_ORIGINS",
    )

    # Translation settings
    default_source_language: str = Field(
        default="auto", alias="DEFAULT_SOURCE_LANGUAGE"
    )
    target_language: str = Field(default="en", alias="TARGET_LANGUAGE")

    # API URLs
    groq_api_url: str = "https://api.groq.com/openai/v1"
    pexels_api_url: str = "https://api.pexels.com/videos"
    pixabay_api_url: str = "https://pixabay.com/api/"

    # Paths
    @property
    def base_dir(self) -> Path:
        """Get the base directory of the project."""
        return Path(__file__).resolve().parent.parent.parent

    @property
    def static_dir(self) -> Path:
        """Get the static files directory."""
        return self.base_dir / "static"

    @property
    def output_dir(self) -> Path:
        """Get the output directory for generated files."""
        return self.static_dir / "output"

    @property
    def temp_dir(self) -> Path:
        """Get the temporary files directory."""
        return self.static_dir / "temp"

    @property
    def audio_dir(self) -> Path:
        """Get the audio files directory."""
        return self.static_dir / "audio"

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [self.static_dir, self.output_dir, self.temp_dir, self.audio_dir]
        for directory in directories:
            directory.mkdir(exist_ok=True, parents=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    settings.ensure_directories()
    return settings
