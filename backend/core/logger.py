from loguru import logger
import sys


def setup_logger():
    """
    Sets up professional logging for the entire application.
    Every action gets recorded with timestamp and level!
    """

    # Remove default logger
    logger.remove()

    # Console logging - what you see in terminal
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        level="INFO",
        colorize=True
    )

    # File logging - saved to a log file
    logger.add(
        "logs/app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
               "{name}:{line} | {message}",
        level="DEBUG",
        rotation="10 MB",    # New file when reaches 10MB
        retention="7 days",  # Keep logs for 7 days
        compression="zip"    # Compress old logs
    )

    return logger


# Global logger object - import this everywhere!
log = setup_logger()