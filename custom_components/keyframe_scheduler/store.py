"""Storage handler for schedules."""

from __future__ import annotations

from typing import Any, Dict, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORE_KEY, STORE_VERSION


class ScheduleStore:
    """Handle persistent storage of schedules."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize store."""
        self._store = Store(hass, STORE_VERSION, STORE_KEY)
        self._data: Dict[str, Any] = {}

    async def async_load(self) -> None:
        """Load data from storage."""
        data = await self._store.async_load()
        self._data = data or {}

    async def async_save(self) -> None:
        """Save data to storage."""
        await self._store.async_save(self._data)

    async def async_get(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Get schedule for entry."""
        return self._data.get(entry_id)

    async def async_set(self, entry_id: str, schedule: Dict[str, Any]) -> None:
        """Set schedule for entry."""
        self._data[entry_id] = schedule
        await self.async_save()

    async def async_delete(self, entry_id: str) -> None:
        """Delete schedule for entry."""
        if entry_id in self._data:
            del self._data[entry_id]
            await self.async_save()
