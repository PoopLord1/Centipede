"""
Allows any module to create and grab an instance of the Elsagate logger.
"""

import logging

eg_logger = None


def init(level):
    """
    Sets the logging level (eg logging.DEBUG or logging.INFO) for the EG logger object
    """
    global eg_logger
    if eg_logger is None:
        logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=level)
        eg_logger = logging


def get_logger():
    """
    Returns our logging object.
    """
    return eg_logger


if __name__ == "__main__":
    init(logging.WARNING)
    eg_logger = get_logger()
    eg_logger.debug("debug message")
    eg_logger.info("info message")
    eg_logger.critical("critical message")