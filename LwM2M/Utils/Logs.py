from typing import Literal
import logging
import sys
import io
import os


def stream_supports_colour(stream: io.IOBase) -> bool:
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
        *,
        defaults: logging.Mapping[str, logging.Any] | None = None,
    ) -> None:
        super().__init__(fmt, datefmt, style, validate, defaults=defaults)

        self._LEVEL_COLOURS = [
            (logging.DEBUG, "\x1b[39;1m"),
            (logging.INFO, "\x1b[34;1m"),
            (logging.WARNING, "\x1b[33;1m"),
            (logging.ERROR, "\x1b[31m"),
            (logging.CRITICAL, "\x1b[41m"),
        ]

        self._FORMATS = {
            level: logging.Formatter(
                fmt.replace("%(color)", colour),
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            for level, colour in self._LEVEL_COLOURS
        }

    def format(self, record) -> str:
        formatter = self._FORMATS.get(record.levelno)
        if formatter is None:
            formatter = self._FORMATS[logging.DEBUG]

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
    logger = logging.getLogger()

    stream_handler = logging.StreamHandler()
    file_handler = logging.FileHandler("lwm2m.log")
    formatter = logging.Formatter(fmt, datefmt)

    stream_formatter = (
        _ColourFormatter(colorfmt, datefmt)
        if stream_supports_colour(stream_handler.stream)
        else formatter
    )

    stream_handler.setFormatter(stream_formatter)
    stream_handler.setLevel(level)

    file_handler.setFormatter(formatter)
    stream_handler.setLevel(level)

    logger.setLevel(level)
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    logger.propagate = propagate
