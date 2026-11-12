"""FastAPI dependencies for objects created once per application."""

from typing import Annotated

from fastapi import Depends, Request

from english_app.core.clock import Clock
from english_app.core.config import Settings
from english_app.core.events import EventBus


def get_app_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_event_bus(request: Request) -> EventBus:
    bus: EventBus = request.app.state.event_bus
    return bus


def get_clock(request: Request) -> Clock:
    clock: Clock = request.app.state.clock
    return clock


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
EventBusDep = Annotated[EventBus, Depends(get_event_bus)]
ClockDep = Annotated[Clock, Depends(get_clock)]
