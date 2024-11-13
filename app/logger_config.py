import logging
import os

# Get log level from environment variable
log_level = os.getenv('LOG_LEVEL', 'DEBUG')

# Map log level names to logging module constants
log_level_mapping = {
    'CRITICAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
}

# Get the actual log level from the mapping
log_level = log_level_mapping.get(log_level, logging.DEBUG)

# Create a custom logger
logger = logging.getLogger(__name__)

# Set the level of logger
logger.setLevel(log_level)

# Create handlers
file_handler = logging.FileHandler('logfile.log')
file_handler.setLevel(log_level)

# Create formatters and add it to handlers
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(log_format)

# Add handlers to the logger
logger.addHandler(file_handler)