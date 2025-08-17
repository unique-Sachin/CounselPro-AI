import logging
from logging.handlers import RotatingFileHandler


def get_logger(name: str = "app", log_file: str = None) -> logging.Logger:
    """Get a logger instance with console and optional file output."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # Optional file handler
        if log_file:
            file_handler = RotatingFileHandler(
                log_file, maxBytes=5_000_000, backupCount=5
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

    logger.propagate = False
    return logger
