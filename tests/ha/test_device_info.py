"""Device Info: filling in, keeping and restoring a device's details."""

from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.device_info import overrides_of
from custom_components.device_info.const import (
    CONF_DEVICE_ID,
    CONF_KEEP,
    DOMAIN,
    SUBENTRY_OVERRIDE,
)
from custom_components.device_info.diagnostics import async_get_config_entry_diagnostics
from custom_components.device_info.overrides import (
    clean_fields,
    plan_restore,
    plan_updates,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.helpers import device_registry as dr


def test_clean_fields_keeps_only_filled_in_details() -> None:
    assert clean_fields(
        {"manufacturer": "  SwitchBot ", "model": "", "sw_version": None, "x": "y"}
    ) == {"manufacturer": "SwitchBot"}


def test_plan_fills_blanks_and_lets_the_integration_win() -> None:
    wanted = {"manufacturer": "SwitchBot", "model": "Curtain"}
    # Blank: filled in.
    assert plan_updates({"manufacturer": None}, wanted, {}, keep=False) == wanted
    # The integration set its own value: left alone without keep.
    assert plan_updates(
        {"manufacturer": "Acme", "model": None}, wanted, {}, keep=False
    ) == {"model": "Curtain"}
    # Still showing what Device Info wrote, and the change was edited: updated.
    assert plan_updates(
        {"manufacturer": "Old", "model": "Curtain"},
        wanted,
        {"manufacturer": "Old"},
        keep=False,
    ) == {"manufacturer": "SwitchBot"}
    # Keep: always written.
    assert plan_updates(
        {"manufacturer": "Acme", "model": "Curtain"}, wanted, {}, keep=True
    ) == {"manufacturer": "SwitchBot"}


def test_restore_only_puts_back_what_device_info_still_holds() -> None:
    assert plan_restore(
        {"manufacturer": "SwitchBot", "model": "Changed by integration"},
        {"manufacturer": "SwitchBot", "model": "Curtain"},
        {"manufacturer": None, "model": None},
        {"manufacturer", "model"},
    ) == {"manufacturer": None}


async def _setup(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] == "create_entry"
    await hass.async_block_till_done()
    (entry,) = hass.config_entries.async_entries(DOMAIN)
    return entry


def _routine(hass, **info) -> dr.DeviceEntry:
    config = MockConfigEntry(domain="other_integration")
    config.add_to_hass(hass)
    return dr.async_get(hass).async_get_or_create(
        config_entry_id=config.entry_id,
        identifiers={("other_integration", "thing")},
        name="Boy's Bedroom Curtains",
        **info,
    )


async def _add(hass, entry, device, **values):
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_OVERRIDE), context={"source": SOURCE_USER}
    )
    assert result["step_id"] == "user"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], user_input={CONF_DEVICE_ID: device.id}
    )
    assert result["step_id"] == "details"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], user_input=values
    )
    await hass.async_block_till_done()
    return result


async def test_set_up_once(hass) -> None:
    await _setup(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["reason"] == "single_instance_allowed"


async def test_fill_in_unknown_details_and_restore_them(hass) -> None:
    """The <unknown> case: fill in, then removing the device puts it back."""
    entry = await _setup(hass)
    device = _routine(hass)
    result = await _add(
        hass, entry, device, manufacturer="SwitchBot", model="Curtain", keep=False
    )
    assert result["type"] == "create_entry"
    assert result["title"] == "Boy's Bedroom Curtains"
    registry = dr.async_get(hass)
    updated = registry.async_get(device.id)
    assert (updated.manufacturer, updated.model) == ("SwitchBot", "Curtain")

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    assert diagnostics["devices"][0]["applied"] == {
        "manufacturer": "SwitchBot",
        "model": "Curtain",
    }

    (subentry,) = entry.subentries.values()
    hass.config_entries.async_remove_subentry(entry, subentry.subentry_id)
    await hass.async_block_till_done()
    restored = registry.async_get(device.id)
    assert (restored.manufacturer, restored.model) == (None, None)


async def test_the_same_device_cant_be_added_twice(hass) -> None:
    entry = await _setup(hass)
    device = _routine(hass)
    await _add(hass, entry, device, manufacturer="SwitchBot", keep=False)
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_OVERRIDE), context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], user_input={CONF_DEVICE_ID: device.id}
    )
    assert result["reason"] == "already_configured"


async def test_an_empty_form_is_refused(hass) -> None:
    entry = await _setup(hass)
    device = _routine(hass)
    result = await _add(hass, entry, device, keep=False)
    assert result["errors"] == {"base": "nothing_set"}


async def test_without_keep_the_integration_wins_later(hass) -> None:
    entry = await _setup(hass)
    device = _routine(hass)
    await _add(hass, entry, device, manufacturer="SwitchBot", keep=False)
    registry = dr.async_get(hass)
    registry.async_update_device(device.id, manufacturer="Wonderlabs")
    await hass.async_block_till_done()
    assert registry.async_get(device.id).manufacturer == "Wonderlabs"


async def test_keep_puts_the_value_back(hass) -> None:
    """With keep on, a value the integration writes later is replaced again."""
    entry = await _setup(hass)
    device = _routine(hass, manufacturer="Acme")
    await _add(hass, entry, device, manufacturer="SwitchBot", keep=True)
    registry = dr.async_get(hass)
    assert registry.async_get(device.id).manufacturer == "SwitchBot"
    registry.async_update_device(device.id, manufacturer="Acme")
    await hass.async_block_till_done()
    assert registry.async_get(device.id).manufacturer == "SwitchBot"

    # Removing the change puts the integration's own value back.
    (subentry,) = entry.subentries.values()
    hass.config_entries.async_remove_subentry(entry, subentry.subentry_id)
    await hass.async_block_till_done()
    assert registry.async_get(device.id).manufacturer == "Acme"


async def test_edit_details_and_clear_one_field(hass) -> None:
    entry = await _setup(hass)
    device = _routine(hass)
    await _add(hass, entry, device, manufacturer="SwitchBot", model="Curtain")
    (subentry,) = entry.subentries.values()
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_OVERRIDE),
        context={"source": "reconfigure", "subentry_id": subentry.subentry_id},
    )
    assert result["step_id"] == "reconfigure"
    assert result["description_placeholders"]["original_manufacturer"] == "not set"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], user_input={"model": "Curtain 3", CONF_KEEP: False}
    )
    assert result["reason"] == "reconfigure_successful"
    await hass.async_block_till_done()
    updated = dr.async_get(hass).async_get(device.id)
    assert (updated.manufacturer, updated.model) == (None, "Curtain 3")


async def test_settings_survive_a_restart(hass) -> None:
    entry = await _setup(hass)
    device = _routine(hass, manufacturer="Acme")
    await _add(hass, entry, device, manufacturer="SwitchBot", keep=False)
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    # Still knows it wrote this value, so removing it restores the original.
    (subentry,) = entry.subentries.values()
    hass.config_entries.async_remove_subentry(entry, subentry.subentry_id)
    await hass.async_block_till_done()
    assert dr.async_get(hass).async_get(device.id).manufacturer == "Acme"


async def test_removing_device_info_restores_everything(hass) -> None:
    entry = await _setup(hass)
    device = _routine(hass)
    await _add(hass, entry, device, manufacturer="SwitchBot", keep=False)
    assert await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert dr.async_get(hass).async_get(device.id).manufacturer is None


async def test_a_removed_device_added_back_gets_its_details_again(hass) -> None:
    """Home Assistant restores a removed device with the same id."""
    entry = await _setup(hass)
    device = _routine(hass)
    await _add(hass, entry, device, manufacturer="SwitchBot", keep=False)
    registry = dr.async_get(hass)
    (config_entry_id,) = (
        e.entry_id for e in hass.config_entries.async_entries("other_integration")
    )
    registry.async_remove_device(device.id)
    await hass.async_block_till_done()
    again = registry.async_get_or_create(
        config_entry_id=config_entry_id,
        identifiers={("other_integration", "thing")},
        name="Boy's Bedroom Curtains",
    )
    await hass.async_block_till_done()
    assert again.id == device.id
    assert registry.async_get(device.id).manufacturer == "SwitchBot"


async def test_other_devices_changing_are_not_looked_at(hass) -> None:
    """Registry updates of devices without a change skip the work."""
    entry = await _setup(hass)
    device = _routine(hass)
    await _add(hass, entry, device, manufacturer="SwitchBot", keep=True)
    other_config = MockConfigEntry(domain="another")
    other_config.add_to_hass(hass)
    registry = dr.async_get(hass)
    other = registry.async_get_or_create(
        config_entry_id=other_config.entry_id,
        identifiers={("another", "lamp")},
        name="Lamp",
    )
    with patch(
        "custom_components.device_info.overrides_of", wraps=overrides_of
    ) as walked:
        registry.async_update_device(other.id, manufacturer="Acme")
        await hass.async_block_till_done()
        assert not walked.called
        registry.async_update_device(device.id, manufacturer="Acme")
        await hass.async_block_till_done()
        assert walked.called
    assert registry.async_get(device.id).manufacturer == "SwitchBot"
