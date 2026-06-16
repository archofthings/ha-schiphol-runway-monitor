"""Binary sensor platform for Schiphol Runway Monitor.

Registers the inbound and outbound peak binary sensors.
The actual entity classes live in sensor.py alongside the runway sensors
so all coordinator access is co-located.
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SchipholRunwayCoordinator
from .sensor import SchipholInboundPeakBinarySensor, SchipholOutboundPeakBinarySensor


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SchipholRunwayCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        SchipholInboundPeakBinarySensor(coordinator),
        SchipholOutboundPeakBinarySensor(coordinator),
    ])
