"""Dependency providers for the routers."""

from typing import Annotated

from fastapi import Depends, Request

from app.services.pii_service import PiiService


def get_pii_service(request: Request) -> PiiService:
    # Built once at startup, in the lifespan handler of app.main.
    service: PiiService = request.app.state.pii_service
    return service


PiiServiceDep = Annotated[PiiService, Depends(get_pii_service)]
