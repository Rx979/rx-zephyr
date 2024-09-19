import logging
from copy import copy
from typing import Final, Optional

import click


class ZephyrFormatter(logging.Formatter):

    TRACE_LOG_LEVEL: Final[int] = 5

    LEVEL_COLORS = {
        TRACE_LOG_LEVEL: lambda level_name: click.style(str(level_name), fg="magenta"),
        logging.DEBUG: lambda level_name: click.style(str(level_name), fg="white"),
        logging.INFO: lambda level_name: click.style(
            str(level_name), fg="bright_green"
        ),
        logging.WARNING: lambda level_name: click.style(
            str(level_name), fg="bright_yellow"
        ),
        logging.ERROR: lambda level_name: click.style(str(level_name), fg="bright_red"),
        logging.CRITICAL: lambda level_name: click.style(
            str(level_name), fg="bright_red", bg="bright_white", bold=True
        ),
    }

    def __init__(
        self, fmt: Optional[str] = None, datefmt: Optional[str] = None
    ) -> None:
        super().__init__(fmt=fmt, datefmt=datefmt, style="%")

    def color_level_name(self, level_name: str, level_no: int) -> str:
        def default(level_name: str) -> str:
            return str(level_name)  # pragma: no cover

        func = self.LEVEL_COLORS.get(level_no, default)
        return func(level_name)

    def formatMessage(self, record: logging.LogRecord) -> str:
        record_copy = copy(record)
        level_name = self.color_level_name(record_copy.levelname, record_copy.levelno)
        if "color_message" in record_copy.__dict__:
            record_copy.msg = record_copy.__dict__["color_message"]
            record_copy.__dict__["message"] = record_copy.getMessage()
        record_copy.__dict__["levelprefix"] = f"[{level_name}]"
        return super().formatMessage(record_copy)
