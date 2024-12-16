# GhostBSD Hearing Aid Setup Wizard

**A user-friendly GTK4/Python wizard** that helps you **install** and **configure** Bluetooth hearing aids on GhostBSD. It includes:

- **Robust BLE Scanning (Experimental)**  
  Performs classic Bluetooth inquiry plus a basic BLE advertisement scan.
- **First Principles Approach**  
  If direct pairing fails (proprietary BLE/MFi hearing aids), the wizard guides you to bridging accessories.
- **Internationalization (i18n)**  
  Uses `.po` translation files to support multiple languages.
- **Wizard-Style Flow**  
  Multi-page setup process: intro → discover → pair → configure PulseAudio → bridging info → finish.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Internationalization (i18n)](#internationalization-i18n)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **BLE + Classic Discovery**: Uses `hccontrol` to do standard inquiry and partial BLE scanning (via `le_set_scan_enable`).  
- **User-Friendly Wizard**: Guides you step by step: discovering devices, pairing, configuring PulseAudio, bridging info.  
- **Logging**: All steps and errors are logged to both the GUI text pane and `/var/log/ghostbsd-hearingaid-setup.log`.  
- **Bridging Accessory Documentation**: If you have a bridging dongle from the manufacturer, the wizard can open a `bridging_info.md` doc or PDF for instructions.

---

## Prerequisites

1. **GhostBSD / FreeBSD** environment.  
2. **Root privileges** (recommended) to edit system configs, install packages, and restart services.  
3. **Python 3.9+**  
4. **GTK4 & PyGObject**  
   ```bash
   pkg install -y py39-gobject3 gtk4
   ```
5. **Bluetooth Tools**  
   - `hccontrol`, `usbconfig` (usually in base system)  
   - `pulseaudio`, `pulseaudio-module-bluetooth`  

---

## Installation

1. **Clone or Download** this repository.  
2. **Ensure** the `install-ghostbsd-hearingaid-setup.sh` script and `ghostbsd_hearingaid_setup.py` are in the same directory.  
3. **Make the install script executable** and run it as root:
   ```bash
   chmod +x install-ghostbsd-hearingaid-setup.sh
   sudo ./install-ghostbsd-hearingaid-setup.sh
   ```
   This creates an installation directory (e.g. `/usr/local/share/ghostbsd_hearingaid_setup`), copies files, and installs a `.desktop` entry.

---

## Usage

After installation:

- **Launch** from the system menu (search for “GhostBSD Hearing Aid Setup”)  
  **OR** type:
  ```bash
  ghostbsd-hearingaid-setup
  ```
- Follow the wizard pages:
  1. **Intro** – Explains direct vs bridging approach.  
  2. **Discover** – Installs needed packages, restarts daemons, runs classic and BLE scans.  
  3. **Pair** – Lists discovered devices. Click “Pair Selected Device.”  
  4. **Configure PulseAudio** – Adds `module-bluetooth-discover` and restarts PulseAudio.  
  5. **Bridging Info** – If direct pairing fails for proprietary BLE or MFi devices, read bridging instructions.  
  6. **Finish** – Closes the wizard.

The script logs output to **`/var/log/ghostbsd-hearingaid-setup.log`**.

---

## Internationalization (i18n)

1. **Compile `.po` files** to `.mo`:
   ```bash
   msgfmt -o locale/es/LC_MESSAGES/ghostbsd_hearingaid_setup.mo locale/es/LC_MESSAGES/ghostbsd_hearingaid_setup.po
   ```
2. **Set Locale**:
   ```bash
   LANG=es_ES.UTF-8 ghostbsd-hearingaid-setup
   ```
   The wizard interface will display translated strings if `.mo` files are installed.

---

## Troubleshooting

1. **No Bluetooth Adapter Detected**  
   - Run `usbconfig list` to confirm your dongle or built-in adapter is recognized.  
   - Some adapters may lack FreeBSD driver support.

2. **Pairing Fails Consistently**  
   - Your hearing aids may use proprietary BLE or MFi protocols. Use a bridging accessory.  
   - Check logs in `/var/log/ghostbsd-hearingaid-setup.log`.

3. **PulseAudio Not Restarting**  
   - Manually run `pulseaudio --kill && pulseaudio --start`.  
   - If you’re using PipeWire, the wizard’s PulseAudio logic might not fully apply.

---

## Contributing

1. **Fork** this repository.  
2. **Create** a new branch for your feature or fix:  
   ```bash
   git checkout -b feature/my-feature
   ```  
3. **Commit & push** your changes, then **open a pull request**.

Areas for improvement include:

- More advanced BLE/GATT scanning logic.  
- Additional wizard pages for advanced debugging.  
- Better bridging device support.

---

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

