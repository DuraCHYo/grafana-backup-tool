"""Logging configuration for Grafana backup v2."""

import sys
from pathlib import Path

from loguru import logger


def setup_logging(log_level: str = "INFO", debug: bool = False):
    """Configure loguru logging."""
    
    # Remove default handler
    logger.remove()
    
    # Console output with colors
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )
    
    # File output for debug mode
    if debug:
        log_file = Path("_OUTPUT_") / "grafana_backup_v2.log"
        log_file.parent.mkdir(exist_ok=True)
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="10 MB",
            retention="1 week",
        )
    
    logger.info("Logging configured successfully")