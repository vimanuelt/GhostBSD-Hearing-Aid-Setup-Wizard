#GhostBSD Hearing Aid Setup Wizard

A **Python/GTK3** wizard to help you **discover**, **pair**, and **configure** Bluetooth hearing aids on **GhostBSD**.  
Includes **experimental BLE scanning**, bridging accessory documentation, and i18n support.

---

## Features

1. **Wizard Flow**: Intro → Discover → Pair → Configure PulseAudio → Bridging Info → Finish  
2. **BLE + Classic**: Utilizes GhostBSD’s native Bluetooth stack, attempts BLE scanning via `hccontrol` + parsing `dmesg`.  
3. **Bridging**: If direct pairing fails (BLE or MFi hearing aids), a bridging accessory doc is included.  
4. **i18n**: `.po` files compiled into `.mo`.  
5. **No separate** `pulseaudio-module-bluetooth`: On GhostBSD, Bluetooth support must be compiled into PulseAudio.

---

## Prerequisites

- **GhostBSD** environment, root privileges recommended.  
- **GhostBSD-bluetooth** packages for the underlying BT stack. (e.g., `GhostBSD-bluetooth-24.10.1`)  
- **PulseAudio**: If you want A2DP/HFP streaming, ensure PulseAudio is built with Bluetooth. If the default package lacks BT, recompile from ports:
  ```bash
  cd /usr/ports/audio/pulseaudio
  make config  # enable Bluetooth / BLUEZ
  make install clean

    GTK4 + PyGObject for the GUI wizard:

    pkg install -y py311-pygobject gtk3

## Installation (setup.py)

- **Clone** this repository:
  ```bash
  git clone https://github.com/YourUser/ghostbsd-hearingaid-setup.git
  cd ghostbsd-hearingaid-setup
  ```

- **Install** the wizard using Python:
  ```bash
  sudo python3 setup.py install
  ```
  - Copies ghostbsd_hearingaid_setup.py to /usr/local/share/ghostbsd_hearingaid_setup.
  - Compiles .po translation files under locale/.
  - Creates /usr/local/bin/ghostbsd-hearingaid-setup wrapper script.
  - Installs a .desktop entry at /usr/local/share/applications/ghostbsd_hearingaid_setup.desktop.

Note: This does not install a separate pulseaudio-module-bluetooth (which doesn’t exist on GhostBSD). You must build or configure PulseAudio with Bluetooth support if needed.

## Usage

After installation, run:
  ```bash
  ghostbsd-hearingaid-setup
  ```

**Wizard Steps:**

  -  **Intro** – Explains no separate BT module, bridging notes.
  -  **Discover** – Installs needed packages, attempts classic + BLE scanning.
  -  **Pair** – Writes hcsecd.conf, tries create_connection.
  -  **Configure PulseAudio** – Attempts to load module-bluetooth-discover; if missing, rebuild PulseAudio.
  -  **Bridging** – If device is BLE-only or proprietary, references bridging doc.
  -  **Finish** – Summarizes next steps, logs in /var/log/ghostbsd-hearingaid-setup.log.

## Internationalization (i18n)

  - Place .po files under locale/<lang>/LC_MESSAGES/<appname>.po.
  - The setup.py install step compiles them into .mo.
  - Run with a locale:
    ```bash
    LANG=es_ES.UTF-8 ghostbsd-hearingaid-setup
    ```

## Troubleshooting

  - PulseAudio Not Finding BT Devices: Possibly no BT support compiled in. Rebuild from ports with the Bluetooth/BlueZ option.
  - Pairing Fails: The hearing aid may use specialized BLE or MFi protocols. Use a bridging dongle.
  - No separate pulseaudio-module-bluetooth: GhostBSD doesn’t split that out.
  - Check Logs: /var/log/ghostbsd-hearingaid-setup.log.

## Contributing

  - Fork this repo.
  - Branch off for your changes: git checkout -b feature/something.
  - Commit & push, open a Pull Request.

## License

MIT License. See ARCHITECTURE.md or the top of ghostbsd_hearingaid_setup.py for license info.

