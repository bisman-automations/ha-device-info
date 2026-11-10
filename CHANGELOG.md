# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-11-10

### Changed

- **Install from the Marketplace by searching for Device Info.** Home Assistant 2026.11 renames HACS to the Marketplace, so the install steps start by searching the Marketplace. Searching HACS stays for Home Assistant 2026.10 and older, and adding the repository as a custom repository remains the fallback.
- **Ruff 0.17.4.** Linting uses the current Ruff release.

## [1.0.0] - 2026-10-30

### Added

- **Fill in or correct a device's details.** Add a device under Device Info and type the manufacturer, model, model ID, hardware or firmware version, or serial number it should show, for example when the device list says unknown. Blank fields keep what the device's integration sets.
- **Keep your values, or let the integration win.** By default your values fill in what the integration leaves blank, and the integration's own value wins if it sets one later. Turn on **Keep these** to put your values back whenever the integration changes them.
- **Undo at any time.** Removing a device from Device Info, or clearing a field, puts back what the integration had set. Removing Device Info itself puts back every device.

[1.0.1]: https://github.com/bisman-automations/ha-device-info/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/bisman-automations/ha-device-info/releases/tag/v1.0.0
