from os import environ
import logging

LOG_LEVEL = environ.get('SWEPUB_LOG_LEVEL', 'INFO')
levels = {
    "DEBUG": logging.DEBUG,
    "ERROR": logging.ERROR,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "CRITICAL": logging.CRITICAL
    }

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# create console handler with a higher log level
ch = logging.StreamHandler()
if LOG_LEVEL in levels:
    logger.setLevel(levels[LOG_LEVEL])
else:
    raise Exception("Invalid log level")
formatter = logging.Formatter(
    fmt="[%(asctime)s] [%(process)d] [%(module)s] [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)",
    datefmt="%Y-%m-%d %H:%M:%S %z"
)
ch.setFormatter(formatter)
logger.addHandler(ch)
