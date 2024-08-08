from typing import Literal
import logging
import sys
import io
import os

_log = logging.getLogger("LwM2M.Utils.Logs")
_log_file = "lwm2m.log"


def _stream_supports_colour(stream: io.IOBase) -> bool:
    """
    Check if the given stream supports color output.

    :param stream: The stream to check.
    :type stream: io.IOBase
    :return: True if the stream supports color output, False otherwise.
    :rtype: bool
    """

    is_a_tty = hasattr(stream, "isatty") and stream.isatty()

    if (
        "PYCHARM_HOSTED" in str(os.environ).upper()
        or os.environ.get("TERM_PROGRAM").lower() == "vscode"
    ):
        return is_a_tty

    if sys.platform != "win32":
        docker_path = "/proc/self/cgroup"
        return is_a_tty or (
            os.path.exists("/.dockerenv")
            or (
                os.path.isfile(docker_path)
                and any("docker" in line for line in open(docker_path))
            )
        )

    return is_a_tty and (
        "ANSICON" in str(os.environ).upper() or "WT_SESSION" in str(os.environ).upper()
    )


class _ColourFormatter(logging.Formatter):
    def __init__(
        self,
        fmt: str = "\x1b[30;1m%(asctime)s\x1b[0m %(color)%(levelname)-8s\x1b[0m \x1b[35m%(name)s\x1b[0m %(message)s",
        datefmt: str = "%Y-%m-%d %H:%M:%S",
        style: Literal["%"] | Literal["{"] | Literal["$"] = "%",
        validate: bool = True,
    ) -> None:
        """
        Initialize the Logs object.

        :param fmt: The format string for log messages.
        :type fmt: str
        :param datefmt: The format string for log message timestamps.
        :type datefmt: str
        :param style: The style of the format string.
        :type style: Literal["%"] | Literal["{"] | Literal["$"]
        :param validate: Whether to validate the format string.
        :type validate: bool
        """

        super().__init__(fmt, datefmt, style, validate)

        self._formats = {
            level: logging.Formatter(
                fmt.replace("%(color)", colour),
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            for level, colour in [
                (logging.DEBUG, "\x1b[39;1m"),
                (logging.INFO, "\x1b[34;1m"),
                (logging.WARNING, "\x1b[33;1m"),
                (logging.ERROR, "\x1b[31m"),
                (logging.CRITICAL, "\x1b[41m"),
            ]
        }

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record.

        :param record: The log record to be formatted.
        :type record: logging.LogRecord
        :return: The formatted log record.
        :rtype: str
        """

        formatter = self._formats.get(record.levelno)

        if formatter is None:
            formatter = self._formats[logging.DEBUG]

        if record.exc_info:
            text = formatter.formatException(record.exc_info)
            record.exc_text = f"\x1b[31m{text}\x1b[0m"

        output = formatter.format(record)

        record.exc_text = None
        return output


def setup_logging(
    level: int = logging.INFO,
    fmt: str = "%(asctime)s %(levelname)-8s %(name)s.%(funcName)s %(message)s",
    colorfmt: str = "\x1b[30;1m%(asctime)s\x1b[0m %(color)%(levelname)-8s\x1b[0m \x1b[35m%(name)s.%(funcName)s\x1b[0m %(message)s",
    datefmt: str = "%Y-%m-%d %H:%M:%S",
    propagate: bool = False,
) -> None:
    """
    Set up logging configuration.

    :param level: The logging level to be set. Defaults to logging.INFO.
    :type level: int
    :param fmt: The format string for log messages. Defaults to "%(asctime)s %(levelname)-8s %(name)s.%(funcName)s %(message)s".
    :type fmt: str
    :param colorfmt: The format string for colored log messages. Defaults to "\x1b[30;1m%(asctime)s\x1b[0m %(color)%(levelname)-8s\x1b[0m \x1b[35m%(name)s.%(funcName)s\x1b[0m %(message)s".
    :type colorfmt: str
    :param datefmt: The format string for the log message timestamp. Defaults to "%Y-%m-%d %H:%M:%S".
    :type datefmt: str
    :param propagate: Whether to propagate log messages to parent loggers. Defaults to False.
    :type propagate: bool
    """

    stream_handler = logging.StreamHandler()
    file_handler = logging.FileHandler("lwm2m.log")
    formatter = logging.Formatter(fmt, datefmt)

    use_color_format = _stream_supports_colour(stream_handler.stream)

    stream_formatter = (
        _ColourFormatter(colorfmt, datefmt) if use_color_format else formatter
    )

    stream_handler.setFormatter(stream_formatter)
    stream_handler.setLevel(level)

    file_handler.setFormatter(formatter)
    stream_handler.setLevel(level)

    logger = logging.getLogger()
    logger.propagate = propagate
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    logger.setLevel(level)

    _log.debug("Initialized logging")
    _log.debug(f"Log level set to {logging.getLevelName(level)}")
    _log.debug(f"Log format set to {fmt}")
    _log.debug(f"Date format set to {datefmt}")
    _log.debug(f"Color format set to {use_color_format}")
    _log.debug(f"Log propagation set to {propagate}")


def end_logging(separator: str = "\n\n") -> None:
    """
    End logging and perform necessary cleanup operations.

    :param separator: The separator to be written to the log file and standard output/error.
    :type separator: str
    """

    _log.debug("Ending logging")

    logging.shutdown()

    with open(_log_file, "a") as file:
        file.write(separator)
        os.fsync(file.fileno())

    sys.stdout.write(separator)
    sys.stdout.flush()
    os.fsync(sys.stdout.fileno())

    sys.stderr.write(separator)
    sys.stderr.flush()
    os.fsync(sys.stderr.fileno())
