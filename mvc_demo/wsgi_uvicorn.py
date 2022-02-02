# -*- coding: utf-8 -*-
"""Application Web Server Gateway Interface - uvicorn."""
import logging
import os
import sys

# import uvicorn
from uvicorn import Config, Server
import uvicorn
from loguru import logger

from mvc_demo.app.asgi import get_app
from mvc_demo.config.application import settings
from mvc_demo.core.loguru_logs import global_log_config


# https://stackoverflow.com/questions/68979130/gunicorn-uvicorn-run-programatically-or-via-command-line
def run_dev_wsgi(
    host=os.getenv("FASTAPI_HOST", "127.0.0.1"),
    port=os.getenv("FASTAPI_PORT", "8000"),
    workers=int(os.getenv("FASTAPI_WORKERS", 2)),
):
    """Run uvicorn WSGI with ASGI workers."""
    logger.info("Start uvicorn WSGI with ASGI workers.")
    sys.exit(
        uvicorn.run(
            "mvc_demo.app.asgi:application",
            host=host,
            port=int(port),
            reload=True,
            # Workers are not used when reload = True
            workers=int(workers),
            lifespan="off",
            log_config=None,
            access_log=True,
        )
    )


if __name__ == "__main__":
    run_dev_wsgi(
        host=os.getenv("FASTAPI_HOST", "127.0.0.1"),
        port=os.getenv("FASTAPI_PORT", "8000"),
        workers=int(os.getenv("FASTAPI_WORKERS", 2)),
    )
