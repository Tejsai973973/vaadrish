import sys
from loguru import logger


def setup_logger(debug: bool = True) -> None:
    logger.remove()
    logger.add(
        sys.stdout,
        level="DEBUG" if debug else "INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>",
        colorize=True,
    )
    logger.add(
        "logs/vaadrish.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO",
        format="{time} | {level} | {name}:{line} — {message}",
    )


logger = logger