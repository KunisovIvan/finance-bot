import sys

from loguru import logger

from core.constants import LOG_FMT_LOGURU
from core.settings import settings


class CustomizeLogger:
    logger = None

    @classmethod
    def make_logger(cls):
        cls.logger = cls.customize_logging(
            level=settings.LOGGING_LEVEL,
            format=LOG_FMT_LOGURU
        )
        return cls.logger

    @classmethod
    def customize_logging(cls, level: str, format: str):
        logger.remove()
        logger.add(
            sys.stdout,
            level=level.upper(),
            format=format,
        )
        return logger


logger = CustomizeLogger.make_logger()
