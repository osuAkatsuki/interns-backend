import logging as stdlib_logging
import os
import sys
import traceback
from contextvars import ContextVar
from types import TracebackType

import structlog
from structlog.types import EventDict
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
    # TODO: fix error with json logger where it does this with stacktraces
    # https://app.datadoghq.com/logs?query=status%3Aerror%20service%3Ainterns-backend&cols=host%2Cservice&event=AgAAAYg71Zcly_8c2AAAAAAAAAAYAAAAAEFZZzcxYUdLQUFCcHg4RVNkQmlHaGdBTgAAACQAAAAAMDE4ODNiZDUtYzNjMC00OTY1LWFjNWMtZTBiM2Q5YTE5ZTE4&index=%2A&messageDisplay=inline&stream_sort=desc&viz=stream&from_ts=1680750604418&to_ts=1680751504418&live=true
    # return app_env == "local"
    return True


def log_with_colors(app_env: str) -> bool:
    return app_env == "local"


def add_process_id(_: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
    event_dict["process_id"] = os.getpid()
    return event_dict


def add_request_id(_: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
    if request_id := _REQUEST_ID_CONTEXT.get(None):
        event_dict["request_id"] = request_id

    return event_dict


def configure_logging(app_env: str, log_level: str | int) -> None:
    if log_as_text(app_env):
        renderer = structlog.dev.ConsoleRenderer(colors=log_with_colors(app_env))
    else:
        renderer = structlog.processors.JSONRenderer()

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=[
            structlog.processors.TimeStamper(fmt="iso", key="timestamp"),
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            add_process_id,
            add_request_id,
        ],
    )

    handler = stdlib_logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(log_level)

    _ROOT_LOGGER.addHandler(handler)
    _ROOT_LOGGER.setLevel(log_level)

    for name in stdlib_logging.root.manager.loggerDict:
        logger = stdlib_logging.getLogger(name)

        # defer logging control to the root logger
        logger.propagate = True
        logger.setLevel(log_level)
        for logger_handler in logger.handlers:
            logger.removeHandler(logger_handler)


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
