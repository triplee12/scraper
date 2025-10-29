"""
Centralized logging layer for the application
"""

import logging

class LogHandler:
    logger = logging.getLogger("E-commerce-Product-Tracker")
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)s:     %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

logger = LogHandler.logger
