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
    # If DATABASE_URL is set, it takes precedence over individual Postgres settings
    database_url_override: str | None = Field(default=None, alias="DATABASE_URL")
    postgres_user: str = Field(default="user", alias="POSTGRES_USER")
    postgres_password: str = Field(default="password", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="aive_db", alias="POSTGRES_DB")
    database_host: str = Field(default="localhost", alias="DATABASE_HOST")
    database_port: int = Field(default=5432, alias="DATABASE_PORT")
    
    @property
    def database_url(self) -> str:
        """Construct the database URL from individual components or use override."""
        if self.database_url_override:
            return self.database_url_override
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.database_host}:{self.database_port}/{self.postgres_db}"

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

    # AWS Configuration
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    aws_access_key_id: str = Field(default="", alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="", alias="AWS_SECRET_ACCESS_KEY")
    lambda_function_name: str = Field(default="aive-video-renderer-dev-renderVideo", alias="LAMBDA_FUNCTION_NAME")
    s3_bucket: str = Field(default="aive-rendered-videos", alias="S3_BUCKET")
    use_lambda_rendering: bool = Field(default=False, alias="USE_LAMBDA_RENDERING")

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
