"""Core endpoints that exist regardless of enabled modules."""

from fastapi import APIRouter, Request
from pydantic import BaseModel

from english_app.core.modules import AppModule

router = APIRouter(tags=["core"])


class HealthResponse(BaseModel):
    status: str


class ModuleResponse(BaseModel):
    key: str
    title: str
    icon: str
    nav_order: int


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/modules", response_model=list[ModuleResponse])
async def list_modules(request: Request) -> list[ModuleResponse]:
    modules: list[AppModule] = request.app.state.modules
    return [
        ModuleResponse(key=m.key, title=m.title, icon=m.icon, nav_order=m.nav_order)
        for m in sorted(modules, key=lambda m: m.nav_order)
    ]
