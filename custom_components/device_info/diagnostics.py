"""Diagnostics: each device's change and what Device Info wrote."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import overrides_of

# Serial numbers identify someone's hardware.
TO_REDACT = {"serial_number"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    runtime = getattr(entry, "runtime_data", None)
    records = getattr(runtime, "records", {})
    return {
        "devices": [
            {
                "device_id": device_id,
                "keep": override["keep"],
                "fields": async_redact_data(override["fields"], TO_REDACT),
                "applied": async_redact_data(
                    records.get(device_id, {}).get("applied", {}), TO_REDACT
                ),
                "original": async_redact_data(
                    records.get(device_id, {}).get("original", {}), TO_REDACT
                ),
            }
            for device_id, override in overrides_of(entry).items()
        ]
    }
