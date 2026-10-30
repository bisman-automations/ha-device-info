"""Device Info: fill in or correct manufacturer, model and other details of devices.

There is one Device Info entry. Each device it changes is a subentry under it
holding the values to show. ``DeviceInfoRuntime`` writes them to the device
registry, puts them back when the device's own integration overwrites a field
that should be kept, and restores the original values when a change is removed.
"""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_DEVICE_ID,
    CONF_FIELDS,
    CONF_KEEP,
    DOMAIN,
    FIELDS,
    STORAGE_KEY,
    STORAGE_VERSION,
    SUBENTRY_OVERRIDE,
)
from .overrides import clean_fields, plan_restore, plan_updates

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type DeviceInfoConfigEntry = ConfigEntry[DeviceInfoRuntime]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Nothing to set up before the entry."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: DeviceInfoConfigEntry) -> bool:
    """Apply every change and keep them in place."""
    runtime = DeviceInfoRuntime(hass, entry)
    entry.runtime_data = runtime
    await runtime.async_start()
    entry.async_on_unload(entry.add_update_listener(_async_entry_updated))
    entry.async_on_unload(runtime.stop)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: DeviceInfoConfigEntry) -> bool:
    """Stop watching. The values stay on the devices."""
    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Removing Device Info puts every device's original values back."""
    store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    stored = await store.async_load() or {}
    registry = dr.async_get(hass)
    for device_id, record in (stored.get("devices") or {}).items():
        _restore(registry, device_id, record, set(record.get("applied", {})))
    await store.async_remove()


async def _async_entry_updated(
    hass: HomeAssistant, entry: DeviceInfoConfigEntry
) -> None:
    """A device's change was added, edited or removed."""
    await entry.runtime_data.async_reconcile()


def overrides_of(entry: ConfigEntry) -> dict[str, dict[str, Any]]:
    """Device id -> ``{"fields": {...}, "keep": bool, "title": str}``."""
    result: dict[str, dict[str, Any]] = {}
    for subentry in entry.subentries.values():
        if subentry.subentry_type != SUBENTRY_OVERRIDE:
            continue
        device_id = subentry.data.get(CONF_DEVICE_ID)
        if not isinstance(device_id, str):
            continue
        result[device_id] = {
            "fields": clean_fields(subentry.data.get(CONF_FIELDS) or {}),
            "keep": bool(subentry.data.get(CONF_KEEP, False)),
            "title": subentry.title,
        }
    return result


def _current(device: dr.DeviceEntry) -> dict[str, Any]:
    return {field: getattr(device, field, None) for field in FIELDS}


def _restore(
    registry: dr.DeviceRegistry,
    device_id: str,
    record: dict[str, Any],
    removed: set[str],
) -> None:
    device = registry.async_get(device_id)
    if device is None or not removed:
        return
    restore = plan_restore(
        _current(device),
        record.get("applied", {}),
        record.get("original", {}),
        removed,
    )
    if restore:
        registry.async_update_device(device_id, **restore)


class DeviceInfoRuntime:
    """Writes each device's values and keeps a record of what it changed."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        # device id -> {"applied": {field: value}, "original": {field: value}}
        self.records: dict[str, dict[str, dict[str, Any]]] = {}
        self._unsub: Any = None

    async def async_start(self) -> None:
        stored = await self._store.async_load() or {}
        devices = stored.get("devices")
        if isinstance(devices, dict):
            self.records = {
                device_id: {
                    "applied": dict(record.get("applied") or {}),
                    "original": dict(record.get("original") or {}),
                }
                for device_id, record in devices.items()
                if isinstance(record, dict)
            }
        await self.async_reconcile()
        self._unsub = self.hass.bus.async_listen(
            dr.EVENT_DEVICE_REGISTRY_UPDATED, self._device_updated
        )

    @callback
    def stop(self) -> None:
        if self._unsub is not None:
            self._unsub()
            self._unsub = None

    async def async_reconcile(self) -> None:
        """Make every device match its change, and undo removed ones."""
        registry = dr.async_get(self.hass)
        overrides = overrides_of(self.entry)
        changed = False
        for device_id in list(self.records):
            wanted = overrides.get(device_id, {}).get("fields", {})
            record = self.records[device_id]
            removed = set(record["applied"]) - set(wanted)
            if removed:
                _restore(registry, device_id, record, removed)
                for field in removed:
                    record["applied"].pop(field, None)
                    record["original"].pop(field, None)
                changed = True
            if not record["applied"]:
                del self.records[device_id]
                changed = True
        for device_id in overrides:
            changed |= self._apply(registry, device_id, overrides)
        if changed:
            await self._save()

    @callback
    def _apply(
        self,
        registry: dr.DeviceRegistry,
        device_id: str,
        overrides: dict[str, dict[str, Any]],
    ) -> bool:
        """Write the device's values where they're missing. True when it wrote any."""
        override = overrides.get(device_id)
        device = registry.async_get(device_id)
        if override is None or device is None:
            return False
        record = self.records.setdefault(device_id, {"applied": {}, "original": {}})
        current = _current(device)
        updates = plan_updates(
            current, override["fields"], record["applied"], keep=override["keep"]
        )
        if not updates:
            return False
        for field, value in updates.items():
            if field not in record["applied"]:
                record["original"][field] = current.get(field)
            record["applied"][field] = value
        registry.async_update_device(device_id, **updates)
        return True

    @callback
    def _device_updated(self, event: Event) -> None:
        """The device's integration rewrote it: put kept values back."""
        if event.data.get("action") != "update":
            return
        device_id = event.data.get("device_id")
        changes = event.data.get("changes") or {}
        if not isinstance(device_id, str) or not set(changes) & set(FIELDS):
            return
        overrides = overrides_of(self.entry)
        if device_id not in overrides:
            return
        if self._apply(dr.async_get(self.hass), device_id, overrides):
            self.hass.async_create_task(self._save())

    async def _save(self) -> None:
        await self._store.async_save({"devices": self.records})
