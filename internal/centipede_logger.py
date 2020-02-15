"""
Allows any module to create and grab an instance of the Elsagate logger.
"""

import logging

eg_logger = None


def create_logger(class_name, level):
    class_logger = logging.getLogger(class_name)
    class_logger.setLevel(level)

    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    class_logger.addHandler(ch)

    return class_logger

if __name__ == "__main__":
    logger = create_logger("logger_testing", logging.DEBUG)
    logger.debug("debug message")
    logger.info("info message")
    logger.critical("critical message")