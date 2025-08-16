import logging
import sys

# Create a logger for your app
logger = logging.getLogger("counselpro")
logger.setLevel(logging.DEBUG)  # or INFO in production

# Check if handlers already exist
if not logger.handlers:
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

# Optional: integrate SQLAlchemy logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
logging.getLogger("sqlalchemy.engine").addHandler(console_handler)
