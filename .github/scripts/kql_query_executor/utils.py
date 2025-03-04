import logging


def setup_logging(level: int) -> None:
    """Configure logging with the specified level."""
    log_format = "%(message)s"
    if level == logging.DEBUG:
        log_format = "%(levelname)s: %(message)s"

    handlers = [logging.StreamHandler()]
    logging.basicConfig(level=level, format=log_format, handlers=handlers)
