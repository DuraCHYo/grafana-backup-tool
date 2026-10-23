"""
Pydantic settings configuration for Grafana backup v2.
"""

from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GrafanaSettings(BaseModel):
    """Grafana connection settings."""
    url: str = Field(default="http://localhost:3000", description="Grafana server URL")
    token: str | None = Field(default=None, description="API token for authentication")
    admin_user: str | None = Field(default=None, description="Admin username")
    admin_password: str | None = Field(default=None, description="Admin password")
    verify_ssl: bool = Field(default=False, description="Verify SSL certificates")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")


class StorageSettings(BaseModel):
    """Storage configuration."""
    backup_dir: Path = Field(default=Path("_OUTPUT_"), description="Backup directory")
    timestamp_format: str = Field(default="%Y-%m-%d-%H-%M", description="Timestamp format")
    pretty_print: bool = Field(default=False, description="Pretty print JSON files")
    create_archive: bool = Field(default=True, description="Create archive backup")
    
    # S3 settings
    s3_bucket: str | None = Field(default=None, description="S3 bucket name")
    s3_key: str | None = Field(default=None, description="S3 key prefix")
    aws_region: str | None = Field(default=None, description="AWS region")
    s3_endpoint_url: str | None = Field(
        default=None, description="Custom S3 endpoint (MinIO/Garage/AIStor/R2)"
    )
    aws_access_key_id: str | None = Field(
        default=None, description="AWS access key (falls back to AWS_ACCESS_KEY_ID)"
    )
    aws_secret_access_key: str | None = Field(
        default=None, description="AWS secret key (falls back to AWS_SECRET_ACCESS_KEY)"
    )
    
    # Azure settings
    azure_container: str | None = Field(default=None, description="Azure container name")
    azure_connection_string: str | None = Field(default=None, description="Azure connection string")
    
    # GCS settings
    gcs_bucket: str | None = Field(default=None, description="GCS bucket name")
    gcs_path: str | None = Field(default=None, description="GCS path prefix")


class ComponentSettings(BaseModel):
    """Component-specific settings."""
    enabled_components: list[str] = Field(
        default_factory=list, 
        description="List of components to backup (empty = all)"
    )
    backup_workers: int = Field(default=3, description="Number of parallel workers")
    retry_attempts: int = Field(default=3, description="Retry attempts for failed operations")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")


class Settings(BaseSettings):
    """Main settings class using pydantic-settings."""
    
    grafana: GrafanaSettings = Field(default_factory=GrafanaSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    components: ComponentSettings = Field(default_factory=ComponentSettings)
    
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Log level")
    
    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
        case_sensitive = False,
        extra = "ignore",  # Ignore extra fields from legacy config
    )