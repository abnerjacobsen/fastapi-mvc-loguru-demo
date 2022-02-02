import logging
import os
import platform
from asgi_correlation_id.context import correlation_id
from datetime import datetime, timezone
from gunicorn.glogging import Logger
from loguru import logger
from pprint import pformat
from sys import stdout
from typing import Union

try:
    from orjson import dumps
except:
    from json import dumps

# App core modules
from mvc_demo.config.application import settings

# References
# Solution comes from:
#   https://pawamoy.github.io/posts/unify-logging-for-a-gunicorn-uvicorn-app/
#   https://github.com/pahntanapat/Unified-FastAPI-Gunicorn-Log
#   https://github.com/Delgan/loguru/issues/365
#   https://loguru.readthedocs.io/en/stable/api/logger.html#sink

def set_log_extras(record):
    record["extra"]["datetime"] = datetime.now(timezone.utc)   # Log datetime in UTC time zone, even if server is using another timezone
    record["extra"]["host"] = os.getenv('HOSTNAME', os.getenv('COMPUTERNAME', platform.node())).split('.')[0]
    record["extra"]["pid"] = os.getpid()
    record["extra"]["request_id"] = correlation_id.get()
    record["extra"]["app_name"] = settings.PROJECT_NAME

# 
# Set Gunicorn loggin handler to NullHandler, this allow
# Loguru to capture the logs emitted by Gunicorn
#
class StubbedGunicornLogger(Logger):
    def setup(self, cfg):
        self.loglevel = self.LOG_LEVELS.get(cfg.loglevel.lower(), logging.INFO)

        handler = logging.NullHandler()

        self.error_logger = logging.getLogger("gunicorn.error")
        self.error_logger.addHandler(handler)

        self.access_logger = logging.getLogger("gunicorn.access")
        self.access_logger.addHandler(handler)

        self.error_logger.setLevel(self.loglevel)
        self.access_logger.setLevel(self.loglevel)


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

def format_record(record: dict) -> str:
    """
    Custom format for loguru loggers.
    Uses pformat for log any data like request/response body 
    >>> [   {   'count': 2,
    >>>         'users': [   {'age': 87, 'is_active': True, 'name': 'Nick'},
    >>>                      {'age': 27, 'is_active': True, 'name': 'Alex'}]}]
    """
    # format_string = LOGURU_FORMAT
    # format_string = '<green>{extra[datetime]}</green> | <green>{extra[app_name]}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level> | <level>{extra}</level>'
    # format_string = "<green>{extra[datetime]}</green> | <green>{extra[pid]}</green> | <green>{extra[correlation_id]}</green> | <green>{extra[request_id]}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    format_string = "<green>{extra[datetime]}</green> | <green>{extra[app_name]}</green> | <green>{extra[host]}</green> | <green>{extra[pid]}</green> | <green>{extra[request_id]}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

    # This is to nice print data, like: logger.bind(payload=dataobject).info("Received data")
    if record["extra"].get("payload") is not None:
        record["extra"]["payload"] = pformat(
            record["extra"]["payload"], indent=4, compact=True, width=88
        )
        format_string += "\n<level>{extra[payload]}</level>"

    format_string += "{exception}\n"

    return format_string


def orjson_log_sink(msg):
    r = msg.record
    rec = {
        "elapsed": r["elapsed"].total_seconds(),
        "time": r["time"].isoformat(),
        "level": {
            "name": r["level"].name,
            "no": r["level"].no,
        },
        "process": {"id": r["process"].id, "name": r["process"].name},
        "thread": {"id": r["thread"].id, "name": r["thread"].name},
        "file": r["file"].path,
    }

    if r["exception"]:
        rec["exception"] = str(msg)

    for k, v in r.items():
        print(k, type(v), v)
        if k in rec:
            continue
        rec[k] = v

    print(dumps(rec), flush=True)


def global_log_config(log_level: Union[str, int] = logging.INFO, json: bool = True):
    if isinstance(log_level, str) and (log_level in logging._nameToLevel):
        log_level = logging.INFO

    intercept_handler = InterceptHandler()
    # logging.basicConfig(handlers=[intercept_handler], level=LOG_LEVEL)
    # logging.root.handlers = [intercept_handler]
    logging.root.setLevel(log_level)

    seen = set()
    for name in [
        *logging.root.manager.loggerDict.keys(),
        "gunicorn",
        "gunicorn.access",
        "gunicorn.error",
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "uvicorn.config",
    ]:
        if name not in seen:
            seen.add(name.split(".")[0])
            logging.getLogger(name).handlers = [intercept_handler]

    if json:
        logger.configure(
            handlers=[
                {
                    "sink": orjson_log_sink,
                    "serialize": json,
                    "diagnose": True,
                    "backtrace": True,
                }
            ]
        )
    else:
        logger.configure(
            handlers=[
                {
                    "sink": stdout,
                    # https://loguru.readthedocs.io/en/stable/api/logger.html#sink
                    # "sink": "./somefile.log",
                    # "rotation": "10 MB",
                    "serialize": False,
                    # "format": "<green>{extra[datetime]}</green> | <green>{extra[correlation_id]}</green> | <green>{extra[request_id]}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                    "format": format_record,
                    "diagnose": True,
                    "backtrace": True,
                    "enqueue": True,
                }
            ]
        )
    logger.configure(patcher=set_log_extras)

    return logger
