import logging as stdlib_logging
import os
import sys
import traceback
from contextvars import ContextVar
from types import TracebackType
from typing import TextIO

import structlog
from rich.console import Console
from rich.traceback import Traceback
from structlog.types import EventDict
from structlog.types import ExcInfo
from structlog.types import Processor
from structlog.types import WrappedLogger


_ROOT_LOGGER = stdlib_logging.getLogger()

_REQUEST_ID_CONTEXT: ContextVar[str | None] = ContextVar("request_id")


def set_request_id(request_id: str | None) -> None:
    _REQUEST_ID_CONTEXT.set(request_id)


def get_request_id() -> str | None:
    return _REQUEST_ID_CONTEXT.get(None)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.wrap_logger(_ROOT_LOGGER, logger_name=name or "root")


def log_as_text(app_env: str) -> bool:
    return app_env == "local"


def add_process_id(_: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
    event_dict["process_id"] = os.getpid()
    return event_dict


def add_request_id(_: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
    if request_id := _REQUEST_ID_CONTEXT.get(None):
        event_dict["request_id"] = request_id

    return event_dict


# https://github.com/hynek/structlog/issues/35#issuecomment-591321744
def rename_event_key(_, __, event_dict: EventDict) -> EventDict:
    """
    Log entries keep the text message in the `event` field, but Datadog
    uses the `message` field. This processor moves the value from one field to
    the other.
    See https://github.com/hynek/structlog/issues/35#issuecomment-591321744
    """
    event_dict["message"] = event_dict.pop("event")
    return event_dict


def drop_color_message_key(_, __, event_dict: EventDict) -> EventDict:
    """
    Uvicorn logs the message a second time in the extra `color_message`, but we don't
    need it. This processor drops the key from the event dict if it exists.
    """
    event_dict.pop("color_message", None)
    return event_dict


def rich_traceback(sio: TextIO, exc_info: ExcInfo) -> None:
    """
    We overwrite the default version of this in structlog to set the `max_frames` to 10.

    Being an ASGI server, there are a lot of frames that are not relevant to us, and
    we don't want to clutter the logs with them; especially when pretty printing.
    """
    sio.write("\n")
    Console(file=sio, color_system="truecolor").print(
        Traceback.from_exception(*exc_info, show_locals=True, max_frames=10)
    )


def configure_logging(app_env: str, log_level: str | int) -> None:
    shared_processors: list[Processor] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        add_process_id,
        add_request_id,
        drop_color_message_key,
    ]

    if log_as_text(app_env):
        log_renderer = structlog.dev.ConsoleRenderer(exception_formatter=rich_traceback)
    else:
        log_renderer = structlog.processors.JSONRenderer()

        # we rename `event` to `message` for datadog
        shared_processors.append(rename_event_key)

        # format the exception only when using the json renderer
        # we want to pretty-print the exception when logging as text
        shared_processors.append(structlog.processors.format_exc_info)

    structlog.stdlib.ProcessorFormatter.wrap_for_formatter
    structlog.configure(
        processors=(
            shared_processors
            # prepare for `ProcessorFormatter`
            + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter]
        ),
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            log_renderer,
        ],
    )

    handler = stdlib_logging.StreamHandler()
    handler.setFormatter(formatter)

    _ROOT_LOGGER.addHandler(handler)
    _ROOT_LOGGER.setLevel(log_level)

    for _logger in ("uvicorn", "uvicorn.error"):
        stdlib_logging.getLogger(_logger).handlers.clear()
        stdlib_logging.getLogger(_logger).propagate = True

    # effectively disable uvicorn.access
    # TODO: recreate access logs using middleware
    stdlib_logging.getLogger("uvicorn.access").handlers.clear()
    stdlib_logging.getLogger("uvicorn.access").propagate = False


def debug(*args, **kwargs) -> None:
    return get_logger().debug(*args, **kwargs)


def info(*args, **kwargs) -> None:
    return get_logger().info(*args, **kwargs)


def warning(*args, **kwargs) -> None:
    return get_logger().warning(*args, **kwargs)


def error(*args, **kwargs) -> None:
    return get_logger().error(*args, **kwargs)


def critical(*args, **kwargs) -> None:
    return get_logger().critical(*args, **kwargs)


# control the exception traceback message format


def overwrite_exception_hook() -> None:
    def exception_hook(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType,
    ) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        get_logger().error(
            "Uncaught exception",
            traceback=traceback.format_exception(exc_value),
        )

    global _default_excepthook
    _default_excepthook = sys.excepthook

    sys.excepthook = exception_hook


def restore_exception_hook() -> None:
    global _default_excepthook
    sys.excepthook = _default_excepthook
    del _default_excepthook
