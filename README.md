<p align="center">
  <img src="custom_components/device_info/brand/icon.png" alt="Device Info" width="128">
</p>

# Device Info

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.8%2B-blue.svg)](https://www.home-assistant.io/)
[![GitHub Release](https://img.shields.io/github/v/release/bisman-automations/ha-device-info)](https://github.com/bisman-automations/ha-device-info/releases)
[![Test](https://github.com/bisman-automations/ha-device-info/actions/workflows/test.yml/badge.svg)](https://github.com/bisman-automations/ha-device-info/actions/workflows/test.yml)
[![Validate](https://github.com/bisman-automations/ha-device-info/actions/workflows/validate.yml/badge.svg)](https://github.com/bisman-automations/ha-device-info/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/bisman-automations/ha-device-info)](LICENSE)

Fill in or correct a device's manufacturer, model, versions and serial number when its integration leaves them blank or gets them wrong, such as the devices that show **unknown** in the device list. Device Info only changes the details you choose, and puts the original values back when you remove a change.

## Requirements

- Home Assistant 2026.8 or newer.
- Nothing else. It works with devices from any integration.

## Installation

### Marketplace (Home Assistant 2026.11 and newer)

[![Open your Home Assistant instance and open this repository in the Marketplace.](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=bisman-automations&repository=ha-device-info&category=integration)

1. Select the button above, or go to **Settings > Marketplace**, choose **Add
   from link**, enter `bisman-automations/ha-device-info` under **GitHub link**, and
   select **Add**. Adding a repository from a link needs a GitHub connection;
   the Marketplace asks you to connect one if you haven't.
2. Install **Device Info**. If a repair asks you to restart Home Assistant, restart it.

New versions show up under **Settings > Updates**. Already installed Device Info with
HACS? There's nothing to do: Home Assistant moves it into the Marketplace the
first time it starts on 2026.11.

### HACS (Home Assistant 2026.10 and older)

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=bisman-automations&repository=ha-device-info&category=integration)

1. Select the button above, or in HACS open the menu, choose **Custom
   repositories** and add `https://github.com/bisman-automations/ha-device-info` as an
   **Integration**.
2. Download **Device Info** and restart Home Assistant.

### Manual

1. Download `device_info.zip` from the [latest release](https://github.com/bisman-automations/ha-device-info/releases/latest).
2. Unzip it into `config/custom_components/device_info/` and restart Home Assistant.

## Setup

[![Open your Home Assistant instance and start setting up Device Info.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=device_info)

Select the button above, or go to **Settings > Devices & services > Add
integration** and search for **Device Info**.

Device Info is added once. Each device you change is listed under it.

## Changing a device's details

1. Open **Device Info** under **Settings > Devices & services** and choose **Add device**.
2. Choose the device.
3. Type the details it should show: **Manufacturer**, **Model**, **Model ID**, **Hardware version**, **Firmware version** or **Serial number**. Each field shows what the device's integration currently sets. Leave a field blank to keep that.
4. Choose whether to **keep these even when the device's integration sets its own**:
   - **Off** (the default): your values fill in what the integration leaves blank. If the integration sets its own value later, for example after an update, its value wins.
   - **On**: your values always win. If the integration writes its own value, usually when Home Assistant starts or the integration reloads, Device Info puts yours back straight away.

The device's page and the device list show your values from then on.

## Editing and undoing

- **Edit details** (the gear next to the device under Device Info) changes the values. Clearing a field puts back what the integration set for it.
- **Delete** the device from Device Info to put back everything the integration set.
- Removing **Device Info** itself puts back every device it changed.

Device Info remembers each value it wrote and the value that was there before. It only puts a value back while the device still shows what Device Info wrote, so it never undoes a newer value the integration set itself.

## Things to know

- The device's name and area are already yours to change in Home Assistant (the pencil on the device page), so Device Info doesn't touch them.
- If you maintain the integration that makes the device, fix the details there instead; Device Info is for integrations you can't change.
- With **Keep these** on, the integration's own value can show for a moment after Home Assistant starts, until Device Info puts yours back.

## Troubleshooting

- **My value went back to the integration's.** With **Keep these** off, the integration wins when it sets its own value. Edit the device and turn **Keep these** on.
- **Diagnostics:** on the integration's page, open the menu and choose
  **Download diagnostics**. Attach the file to an issue (check it first for
  anything you'd rather not share).
- **Debug logs:** on the integration's page choose **Enable debug logging**,
  reproduce the problem, then **Disable debug logging** to download the log.
- Report problems at [Issues](https://github.com/bisman-automations/ha-device-info/issues).

## Development

```
python3.14 -m venv .venv && . .venv/bin/activate
pip install -r requirements_test.txt
ruff check . && ruff format --check .
pytest
```

CI also tests the oldest supported Home Assistant (`requirements_test_min.txt`)
and runs hassfest and the HACS checks. Releases are drafted automatically from
`CHANGELOG.md` on every push to `main` and published by hand. See
[CLAUDE.md](CLAUDE.md) and [CONTRIBUTING](https://github.com/bisman-automations/.github/blob/main/CONTRIBUTING.md).

## License

[MIT](LICENSE)
