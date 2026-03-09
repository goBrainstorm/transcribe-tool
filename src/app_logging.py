"""Shared logging setup for CLI modules."""

import logging


def configure_logging(debug: bool = False) -> None:
    """Configure root logging once for the CLI process."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(message)s")


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger."""
    return logging.getLogger(name)
