# -*- coding: utf-8 -*-
"""Ready controller."""
from fastapi import APIRouter
from loguru import logger
from mvc_demo.config import settings
from mvc_demo.app.utils import RedisClient
from mvc_demo.app.models import ReadyResponse, ErrorResponse
from mvc_demo.app.exceptions import HTTPException

router = APIRouter()
log = logger


@router.get(
    "/ready",
    tags=["ready"],
    response_model=ReadyResponse,
    summary="Simple health check.",
    status_code=200,
    responses={502: {"model": ErrorResponse}},
)
async def readiness_check():
    """Run basic application health check.

    If the application is up and running then this endpoint will return simple
    response with status ok. Moreover, if it has Redis enabled then connection
    to it will be tested. If Redis ping fails, then this endpoint will return
    502 HTTP error.
    \f

    Returns:
        response (ReadyResponse): ReadyResponse model object instance.

    Raises:
        HTTPException: If applications has enabled Redis and can not connect
            to it. NOTE! This is the custom exception, not to be mistaken with
            FastAPI.HTTPException class.

    """
    log.info("Started GET /ready")

    if settings.USE_REDIS and not await RedisClient.ping():
        log.error("Could not connect to Redis")
        raise HTTPException(
            status_code=502,
            content=ErrorResponse(
                code=502, message="Could not connect to Redis"
            ).dict(exclude_none=True),
        )
    return ReadyResponse(status="ok")
