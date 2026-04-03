"""Logging utility for the data generation agent."""

import logging


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger.

    Args:
        name: Name for the logger (typically __name__)

    Returns:
        Configured Logger instance at INFO level
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
