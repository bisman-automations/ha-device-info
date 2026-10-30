"""Deciding what to write to a device. Pure: no Home Assistant imports.

Device Info keeps, per device and field, the value it last wrote (``applied``)
and the value the device had before (``original``). That is what lets it tell
its own value from one the device's integration set later, and put the
original back when a change is removed.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .const import FIELDS, MAX_LENGTH


def clean_fields(raw: Mapping[str, Any]) -> dict[str, str]:
    """The fields a form or stored override sets: non-empty, trimmed text."""
    fields: dict[str, str] = {}
    for field in FIELDS:
        value = raw.get(field)
        if isinstance(value, str) and (value := value.strip()):
            fields[field] = value[:MAX_LENGTH]
    return fields


def is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def plan_updates(
    current: Mapping[str, Any],
    wanted: Mapping[str, str],
    applied: Mapping[str, Any],
    *,
    keep: bool,
) -> dict[str, str]:
    """The fields to write now so the device shows ``wanted``.

    A field already showing the wanted value is left alone. Otherwise it is
    written when it is blank, when it still shows what Device Info wrote last
    (the change was edited), or always when ``keep`` is on. Without ``keep``,
    a value the device's own integration set later wins.
    """
    updates: dict[str, str] = {}
    for field, value in wanted.items():
        now = current.get(field)
        if now == value:
            continue
        if keep or is_blank(now) or (field in applied and now == applied[field]):
            updates[field] = value
    return updates


def plan_restore(
    current: Mapping[str, Any],
    applied: Mapping[str, Any],
    original: Mapping[str, Any],
    removed: set[str],
) -> dict[str, Any]:
    """Put back the original value of each removed field Device Info still holds.

    A field the device's integration has changed since is left as it is.
    """
    return {
        field: original.get(field)
        for field in removed
        if field in applied and current.get(field) == applied[field]
    }
