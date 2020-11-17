# This file is part of IMASPy.
#
# IMASPy is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# IMASPy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with IMASPy.  If not, see <https://www.gnu.org/licenses/>.
import logging
import time

TRACE_LEVEL_NUM = 5
logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")


def trace(self, message, *args, **kws):
    if self.isEnabledFor(TRACE_LEVEL_NUM):
        # Yes, logger takes its '*args' as 'args'.
        self._log(TRACE_LEVEL_NUM, message, args, **kws)
        logging.Logger.trace = trace


logging.Logger.trace = trace
logging.TRACE = TRACE_LEVEL_NUM


class PrettyFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    light_grey = "\x1b[38;5;251m"
    yellow = "\x1b[33m"
    red = "\x1b[31m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    formatstr = "%(asctime)s [%(levelname)s] %(message)s @%(filename)s:%(lineno)d"
    default_time_format = "%H:%M:%S"

    FORMATS = {
        logging.TRACE: light_grey + formatstr + reset,
        logging.DEBUG: light_grey + formatstr + reset,
        logging.INFO: formatstr,
        logging.WARNING: yellow + formatstr + reset,
        logging.ERROR: red + formatstr + reset,
        logging.CRITICAL: bold_red + formatstr + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        formatter.formatTime = self.formatTime
        return formatter.format(record)

    def formatTime(self, record, datefmt=None, print_ms=False):
        # pylint: disable=arguments-differ # Adds print_ms kwarg
        ct = self.converter(record.created)
        if datefmt:
            ss = time.strftime(datefmt, ct)
        else:
            tt = time.strftime(self.default_time_format, ct)
            if print_ms:
                ss = self.default_msec_format % (tt, record.msecs)
            else:
                ss = tt
        return ss


def test_messages():
    """ Print out a message on each logging level """
    logger = logging.getLogger("imaspy.testlogger")
    logger.setLevel(logging.TRACE)
    logger.trace("Trace message")
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")


def connect_formatter(logger):
    """ Connect general formatter to given logger """
    ch = logging.StreamHandler()
    ch.setLevel(logging.TRACE)
    ch.setFormatter(PrettyFormatter())
    logger.addHandler(ch)


# Log to console by default, and output it all
root_logger = logging.getLogger("imaspy")
connect_formatter(root_logger)

if __name__ == "__main__":
    test_messages()
