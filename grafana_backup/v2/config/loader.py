"""
Configuration loader for Grafana backup v2.
Supports loading from legacy JSON format and converting to v2 settings.
"""

import json
import os
from pathlib import Path

from loguru import logger

from .settings import ComponentSettings, GrafanaSettings, Settings, StorageSettings


def load_legacy_config(config_path: Path) -> Settings:
    """
    Load legacy Grafana backup JSON configuration and convert to v2 settings.
    
    Args:
        config_path: Path to legacy JSON configuration file
        
    Returns:
        Settings instance for v2
    """
    try:
        with open(config_path, 'r') as f:
            legacy_config = json.load(f)
        
        logger.info(f"Loaded legacy configuration from {config_path}")
        
        # Extract grafana settings
        grafana_config = legacy_config.get("grafana", {})
        grafana_settings = GrafanaSettings(
            url=grafana_config.get("url", "http://localhost:3000"),
            token=grafana_config.get("token"),
            admin_user=grafana_config.get("admin_account"),
            admin_password=grafana_config.get("admin_password"),
            verify_ssl=legacy_config.get("general", {}).get("verify_ssl", False),
        )
        
        # Extract storage settings
        general_config = legacy_config.get("general", {})
        storage_settings = StorageSettings(
            backup_dir=Path(general_config.get("backup_dir", "_OUTPUT_")),
            timestamp_format=general_config.get("backup_file_format", "%Y-%m-%d-%H-%M"),
            pretty_print=general_config.get("pretty_print", False),
            create_archive=True,  # Always create archive in v2
        )
        
        # Add cloud storage settings if present
        aws_config = legacy_config.get("aws", {})
        if aws_config.get("s3_bucket_name"):
            storage_settings.s3_bucket = aws_config.get("s3_bucket_name")
            storage_settings.s3_key = aws_config.get("s3_bucket_key")
            storage_settings.aws_region = aws_config.get("region")
            storage_settings.s3_endpoint_url = aws_config.get("endpoint_url")
            storage_settings.aws_access_key_id = aws_config.get("access_key_id")
            storage_settings.aws_secret_access_key = aws_config.get("secret_access_key")
        
        azure_config = legacy_config.get("azure", {})
        if azure_config.get("container_name"):
            storage_settings.azure_container = azure_config.get("container_name")
            storage_settings.azure_connection_string = azure_config.get("connection_string")
        
        gcp_config = legacy_config.get("gcp", {})
        if gcp_config.get("gcs_bucket_name"):
            storage_settings.gcs_bucket = gcp_config.get("gcs_bucket_name")
            storage_settings.gcs_path = gcp_config.get("gcs_bucket_path")
        
        # Extract component settings
        component_settings = ComponentSettings(
            backup_workers=general_config.get("backup_workers", 3),
        )
        
        # General settings
        debug = general_config.get("debug", False)
        
        # Create v2 settings
        settings = Settings(
            grafana=grafana_settings,
            storage=storage_settings,
            components=component_settings,
            debug=debug,
            log_level="DEBUG" if debug else "INFO",
        )
        
        logger.info("Successfully converted legacy configuration to v2 format")
        return settings
        
    except FileNotFoundError:
        logger.warning(f"Configuration file not found: {config_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise


def _env_bool(name: str) -> bool | None:
    """Parse a boolean environment variable, returning ``None`` when unset."""
    raw = os.getenv(name)
    if raw is None or raw == "":
        return None
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _apply_env_overrides(settings: Settings) -> Settings:
    """Apply environment variables with v1-compatible names.

    Priority matches v1: environment > config file > defaults. This keeps
    Docker/Helm setups (``GRAFANA_URL``, ``GRAFANA_TOKEN``, ``AWS_*``) working
    without a mounted configuration file.
    """
    grafana = settings.grafana
    storage = settings.storage

    if value := os.getenv("GRAFANA_URL"):
        grafana.url = value
    if value := os.getenv("GRAFANA_TOKEN"):
        grafana.token = value
    if value := os.getenv("GRAFANA_ADMIN_ACCOUNT"):
        grafana.admin_user = value
    if value := os.getenv("GRAFANA_ADMIN_PASSWORD"):
        grafana.admin_password = value
    if (flag := _env_bool("VERIFY_SSL")) is not None:
        grafana.verify_ssl = flag

    if value := os.getenv("BACKUP_DIR"):
        storage.backup_dir = Path(value)
    if value := os.getenv("BACKUP_FILE_FORMAT"):
        storage.timestamp_format = value
    if (flag := _env_bool("PRETTY_PRINT")) is not None:
        storage.pretty_print = flag

    # S3 settings are read here as well so the storage provider can rely on a
    # single resolved Settings object.
    if value := os.getenv("AWS_S3_BUCKET_NAME"):
        storage.s3_bucket = value
    if value := os.getenv("AWS_S3_BUCKET_KEY"):
        storage.s3_key = value
    if value := os.getenv("AWS_DEFAULT_REGION"):
        storage.aws_region = value
    if value := os.getenv("AWS_ENDPOINT_URL"):
        storage.s3_endpoint_url = value
    if value := os.getenv("AWS_ACCESS_KEY_ID"):
        storage.aws_access_key_id = value
    if value := os.getenv("AWS_SECRET_ACCESS_KEY"):
        storage.aws_secret_access_key = value

    return settings


def load_config(config_path: str | None = None) -> Settings:
    """
    Load configuration from file or use defaults.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Settings instance for v2
    """
    if config_path:
        config_file = Path(config_path)
        if config_file.exists():
            return _apply_env_overrides(load_legacy_config(config_file))
        else:
            logger.warning(f"Configuration file not found: {config_file}, using defaults")
    
    # Try default locations (same order as v1)
    default_locations = [
        Path.home() / ".grafana-backup.json",
        Path("grafanaSettings.json"),
        # Also check built-in config file
        Path(__file__).parent.parent.parent / "conf" / "grafanaSettings.json",
    ]
    
    for location in default_locations:
        if location.exists():
            logger.info(f"Found configuration at {location}")
            return _apply_env_overrides(load_legacy_config(location))
    
    # Use defaults
    logger.info("No configuration file found, using default settings")
    return _apply_env_overrides(Settings())