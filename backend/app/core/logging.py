import logging
import sys

from app.core.config import settings


def setup_logging() -> None:
    """Configuración básica de logging para toda la aplicación."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        stream=sys.stdout,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Devuelve un logger con nombre para módulos de la aplicación."""
    return logging.getLogger(name)
