"""Set up Device Info once, then add or edit one device's details at a time."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, selector

from .const import (
    CONF_DEVICE_ID,
    CONF_FIELDS,
    CONF_KEEP,
    DOMAIN,
    FIELDS,
    SUBENTRY_OVERRIDE,
    TITLE,
)
from .overrides import clean_fields


def _device_name(device: dr.DeviceEntry) -> str:
    return device.name_by_user or device.name or device.id


def _shown(value: Any) -> str:
    """How a device's current value appears in the form's description."""
    return str(value) if value not in (None, "") else "not set"


def _original_values(
    hass: HomeAssistant, entry: ConfigEntry, device: dr.DeviceEntry
) -> dict[str, Any]:
    """What the device's own integration set, before any Device Info change."""
    current = {field: getattr(device, field, None) for field in FIELDS}
    runtime = getattr(entry, "runtime_data", None)
    record = getattr(runtime, "records", {}).get(device.id, {})
    return {**current, **record.get("original", {})}


def _fields_schema(values: dict[str, Any], keep: bool) -> vol.Schema:
    schema: dict[vol.Marker, Any] = {}
    for field in FIELDS:
        schema[
            vol.Optional(field, description={"suggested_value": values.get(field)})
        ] = selector.TextSelector()
    schema[vol.Required(CONF_KEEP, default=keep)] = selector.BooleanSelector()
    return vol.Schema(schema)


def _placeholders(original: dict[str, Any], name: str) -> dict[str, str]:
    return {"device_name": name} | {
        f"original_{field}": _shown(original.get(field)) for field in FIELDS
    }


class DeviceInfoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add Device Info. There is only one."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title=TITLE, data={})
        return self.async_show_form(step_id="user")

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        return {SUBENTRY_OVERRIDE: DeviceDetailsFlow}


class DeviceDetailsFlow(ConfigSubentryFlow):
    """Choose a device, then the details to show for it."""

    def __init__(self) -> None:
        self._device_id: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Choose the device."""
        errors: dict[str, str] = {}
        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            if dr.async_get(self.hass).async_get(device_id) is None:
                errors["base"] = "device_not_found"
            elif any(
                sub.unique_id == device_id
                for sub in self._get_entry().subentries.values()
            ):
                return self.async_abort(reason="already_configured")
            else:
                self._device_id = device_id
                return await self.async_step_details()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_DEVICE_ID): selector.DeviceSelector()}
            ),
            errors=errors,
        )

    async def async_step_details(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Choose what the device shows. Blank fields keep the integration's value."""
        assert self._device_id is not None
        device = dr.async_get(self.hass).async_get(self._device_id)
        if device is None:
            return self.async_abort(reason="device_not_found")
        entry = self._get_entry()
        original = _original_values(self.hass, entry, device)
        errors: dict[str, str] = {}
        if user_input is not None:
            fields = clean_fields(user_input)
            if not fields:
                errors["base"] = "nothing_set"
            else:
                return self.async_create_entry(
                    title=_device_name(device),
                    data={
                        CONF_DEVICE_ID: device.id,
                        CONF_FIELDS: fields,
                        CONF_KEEP: bool(user_input.get(CONF_KEEP)),
                    },
                    unique_id=device.id,
                )
        return self.async_show_form(
            step_id="details",
            data_schema=_fields_schema(user_input or {}, False),
            errors=errors,
            description_placeholders=_placeholders(original, _device_name(device)),
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Change the details. Clearing every field removes the change."""
        entry = self._get_entry()
        subentry = self._get_reconfigure_subentry()
        device = dr.async_get(self.hass).async_get(subentry.data[CONF_DEVICE_ID])
        if device is None:
            return self.async_abort(reason="device_not_found")
        original = _original_values(self.hass, entry, device)
        errors: dict[str, str] = {}
        if user_input is not None:
            fields = clean_fields(user_input)
            if not fields:
                errors["base"] = "nothing_set"
            else:
                return self.async_update_and_abort(
                    entry,
                    subentry,
                    title=_device_name(device),
                    data={
                        CONF_DEVICE_ID: device.id,
                        CONF_FIELDS: fields,
                        CONF_KEEP: bool(user_input.get(CONF_KEEP)),
                    },
                )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_fields_schema(
                user_input or dict(subentry.data.get(CONF_FIELDS) or {}),
                bool(subentry.data.get(CONF_KEEP, False)),
            ),
            errors=errors,
            description_placeholders=_placeholders(original, _device_name(device)),
        )
