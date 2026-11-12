"""Key-value settings changed from the UI and stored in the database."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession


def _utc_now() -> datetime:
    return datetime.now(UTC)


class AppSetting(SQLModel, table=True):
    __tablename__ = "app_setting"

    key: str = Field(primary_key=True, max_length=200)
    value: Any = Field(sa_column=Column(JSON, nullable=False))
    updated_at: datetime = Field(default_factory=_utc_now)


class AppSettingRepository:
    """Reads and writes settings. Never commits; the calling service owns the transaction."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, key: str) -> Any | None:
        setting = await self._session.get(AppSetting, key)
        return None if setting is None else setting.value

    async def set(self, key: str, value: Any) -> None:
        setting = await self._session.get(AppSetting, key)
        if setting is None:
            self._session.add(AppSetting(key=key, value=value))
            return
        setting.value = value
        setting.updated_at = _utc_now()
        self._session.add(setting)

    async def delete(self, key: str) -> None:
        setting = await self._session.get(AppSetting, key)
        if setting is not None:
            await self._session.delete(setting)
