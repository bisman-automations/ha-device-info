"""Constants for Device Info. No Home Assistant imports."""

DOMAIN = "device_info"
TITLE = "Device Info"

# The one Device Info entry; each device's changes are a subentry under it.
SUBENTRY_OVERRIDE = "override"

CONF_DEVICE_ID = "device_id"
CONF_FIELDS = "fields"
# Keep the values even when the device's own integration sets its own.
CONF_KEEP = "keep"

# Device registry fields Device Info can set, in the order the form shows them.
FIELDS = (
    "manufacturer",
    "model",
    "model_id",
    "hw_version",
    "sw_version",
    "serial_number",
)
# Longest value accepted for a field.
MAX_LENGTH = 100

# What Device Info changed: per device, the value it set and the value it found.
STORAGE_KEY = "device_info.applied"
STORAGE_VERSION = 1
