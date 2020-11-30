import functools
import logging

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.WARNING)


def loglevel(func):
    """Generate a decorator for setting the logger level on a function"""

    @functools.wraps(func)
    def loglevel_decorator(*args, **kwargs):
        verbosity = kwargs.pop("verbosity", None)
        if verbosity is not None:
            old_log_level = logger.level
            if verbosity >= 1:
                logger.setLevel(logging.INFO)
            if verbosity >= 2:
                logger.setLevel(logging.DEBUG)
        value = func(*args, **kwargs)
        if verbosity is not None:
            logger.setLevel(old_log_level)
        return value

    return loglevel_decorator
