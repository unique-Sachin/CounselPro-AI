import logging
import sys

# Define log format
LOG_FORMAT = "[%(levelname)s] %(asctime)s | %(name)s | %(message)s"

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,  # Global log level
    format=LOG_FORMAT,
    handlers=[logging.StreamHandler(sys.stdout)],  # Console output
)
