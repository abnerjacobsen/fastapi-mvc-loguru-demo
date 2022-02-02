"""Application routes configuration.

In this file all application endpoints are being defined.
"""
from fastapi import APIRouter
from mvc_demo.app.controllers.api.v1 import ready

router = APIRouter(prefix="/api")

router.include_router(ready.router, tags=["ready"])
