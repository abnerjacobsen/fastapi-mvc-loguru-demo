# -*- coding: utf-8 -*-
"""Application Asynchronous Server Gateway Interface."""
import logging

from fastapi import FastAPI
from asgi_correlation_id import CorrelationIdMiddleware
from loguru import logger
from mvc_demo.config import router, settings
from mvc_demo.app.utils import RedisClient, AiohttpClient
from mvc_demo.app.exceptions import (
    HTTPException,
    http_exception_handler,
)
from mvc_demo.core.loguru_logs import global_log_config

global_log_config(
    log_level=logging.getLevelName(settings.LOG_LEVEL),
    json=settings.JSON_LOGS,
)

log = logger

async def on_startup():
    """Fastapi startup event handler.

    Creates RedisClient and AiohttpClient session.

    """
    log.debug("Execute FastAPI startup event handler.")
    # Initialize utilities for whole FastAPI application without passing object
    # instances within the logic.
    if settings.USE_REDIS:
        await RedisClient.open_redis_client()

    AiohttpClient.get_aiohttp_client()


async def on_shutdown():
    """Fastapi shutdown event handler.

    Destroys RedisClient and AiohttpClient session.

    """
    log.debug("Execute FastAPI shutdown event handler.")
    # Gracefully close utilities.
    if settings.USE_REDIS:
        await RedisClient.close_redis_client()

    await AiohttpClient.close_aiohttp_client()


def get_app():
    """Initialize FastAPI application.

    Returns:
        app (FastAPI): Application object instance.

    """
    log.debug("Initialize FastAPI application node.")
    app = FastAPI(
        title=settings.PROJECT_NAME,
        debug=settings.DEBUG,
        version=settings.VERSION,
        docs_url=settings.DOCS_URL,
        on_startup=[on_startup],
        on_shutdown=[on_shutdown],
    )
    log.debug("Add application routes.")
    app.include_router(router)

    # Register global exception handler for custom HTTPException.
    app.add_exception_handler(HTTPException, http_exception_handler)

    # Register middlewares
    app.add_middleware(CorrelationIdMiddleware, header_name='X-Request-ID')

    return app


application = get_app()
