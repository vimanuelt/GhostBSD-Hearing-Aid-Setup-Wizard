# GhostBSD Hearing Aid Setup Wizard

This is a GTK3-based wizard designed to simplify the process of setting up Bluetooth hearing aids on GhostBSD. The application guides users through:

- **Configuring system services** for Bluetooth support
- **Installing necessary packages**
- **Setting up Bluetooth configuration**
- **Discovering and pairing Bluetooth devices**
- **Configuring PulseAudio for Bluetooth audio**
- **Creating a virtual sound device**
- **Providing information on bridging accessories if needed**

## Features

- **User-friendly Interface**: Step-by-step guidance through the setup process with a graphical interface.
- **Bluetooth Management**: Automates the discovery and pairing of hearing aids, both for Classic Bluetooth and BLE (Bluetooth Low Energy) devices.
- **System Configuration**: Modifies system files like `/etc/rc.conf` and `/etc/bluetooth/ubt0.conf` to ensure proper Bluetooth functionality.
- **Package Management**: Installs required software packages like `iwmbt-firmware` and `virtual_oss`.
- **PulseAudio Setup**: Ensures `module-bluetooth-discover` is loaded in PulseAudio configurations.
- **Virtual Sound Creation**: Sets up virtual sound devices to route audio through Bluetooth hearing aids.

## Prerequisites

- **GhostBSD** operating system
- **Root privileges** for modifying system configurations
- **Bluetooth hardware** supported by GhostBSD

## Installation

To use this setup wizard, you can clone this repository:
  ```bash
  git clone https://github.com/vimanuelt/GhostBSD-Hearing-Aid-Setup-Wizard.git
  cd GhostBSD-Hearing-Aid-Setup-Wizard
  ```

Then, make the script executable:
  ```bash
  chmod +x ghostbsd_hearingaid_setup.py
  ```

## Usage
Run the wizard with root privileges:
  ```bash
  sudo ./ghostbsd_hearingaid_setup.py
  ```

Note: You'll be guided through each step of the setup process. If you encounter any issues, check the log file at /var/log/ghostbsd-hearingaid-setup.log.

## Troubleshooting

  - Permissions: Ensure you're running the setup with root privileges.
  - Bluetooth Not Detecting Devices: Make sure your hearing aids are in pairing mode and not connected to another device. If they still aren't detected, they might not be compatible.
  - Audio Issues: If sound is not working correctly, try adjusting the sample rate in the virtual_oss command from 44100 to 48000.


## Known Issues

    This tool assumes your hearing aids support standard Bluetooth profiles. Proprietary or MFi Bluetooth might require additional bridging hardware.


## Contributing
Contributions are welcome! Please fork this repository and submit pull requests for changes or enhancements. Here's how you can contribute:

  - Bug Fixes: If you find bugs, open an issue with steps to reproduce.
  - Feature Requests: Suggest new features or improvements via issues.
  - Code: Fork the repo, make your changes, and send a pull request.

## Acknowledgements

    - GhostBSD Community: For providing a fantastic BSD-based operating system.
    - Python and GTK Community: For the tools that made this setup wizard possible.
