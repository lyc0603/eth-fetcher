"""
logger
"""

import logging

from eth_tools import constants


def _create_logger():
    """creates a logger"""
    logger = logging.Logger("eth-tools")  # pylint: disable=redefined-outer-name

    # create a formatter
    formatter = logging.Formatter(constants.LOG_FORMAT)

    # create a handler
    handler = logging.StreamHandler()

    # set formatter
    handler.setFormatter(formatter)

    # set level to INFO
    handler.setLevel(logging.INFO)

    # add handler to logger
    logger.addHandler(handler)

    return logger


logger = _create_logger()
