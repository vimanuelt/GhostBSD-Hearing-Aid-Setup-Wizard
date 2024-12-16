#!/usr/bin/env python3
"""
setup.py for GhostBSD Hearing Aid Setup Wizard

Installs the wizard script system-wide on GhostBSD, acknowledging no separate 'pulseaudio-module-bluetooth' exists.
Instead, we install 'pulseaudio' and remind the user they may need to rebuild it from ports if Bluetooth is missing.
"""

import os
import sys
import shutil
import subprocess
from distutils.core import setup, Command
from distutils import log

APP_NAME = "ghostbsd_hearingaid_setup"
INSTALL_DIR = f"/usr/local/share/{APP_NAME}"
WRAPPER_PATH = f"/usr/local/bin/ghostbsd-hearingaid-setup"
DESKTOP_FILE_PATH = f"/usr/local/share/applications/{APP_NAME}.desktop"
LOCALE_DIR = os.path.join(INSTALL_DIR, "locale")

PY_SCRIPT = "ghostbsd_hearingaid_setup.py"
BRIDGING_DOC = "bridging_info.md"

class InstallGhostBSDWizard(Command):
    """
    Custom installation command for the GhostBSD Hearing Aid Setup Wizard.
    Usage: sudo python3 setup.py install
    """
    description = "Install the GhostBSD Hearing Aid Setup wizard system-wide."
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        if os.geteuid() != 0:
            log.error("ERROR: This installer must be run as root (sudo).")
            sys.exit(1)

        # 1. Install / ensure pulseaudio
        # There's no separate pulseaudio-module-bluetooth on GhostBSD:
        log.info("Installing/updating 'pulseaudio'. If BT audio fails, recompile from ports with Bluetooth enabled.")
        subprocess.run(["pkg", "install", "-y", "pulseaudio"], check=False)

        # 2. Create the installation directory
        log.info(f"Creating installation directory: {INSTALL_DIR}")
        os.makedirs(LOCALE_DIR, exist_ok=True)

        # 3. Copy main script and bridging doc
        if not os.path.isfile(PY_SCRIPT):
            log.error(f"Cannot find {PY_SCRIPT} in current directory.")
            sys.exit(1)
        shutil.copy2(PY_SCRIPT, INSTALL_DIR)
        os.chmod(os.path.join(INSTALL_DIR, PY_SCRIPT), 0o755)

        if os.path.isfile(BRIDGING_DOC):
            shutil.copy2(BRIDGING_DOC, INSTALL_DIR)

        # 4. Compile .po files if present
        if os.path.isdir("locale"):
            log.info("Found 'locale' directory. Compiling .po files...")
            for langdir in os.listdir("locale"):
                langpath = os.path.join("locale", langdir)
                if os.path.isdir(langpath):
                    lc_messages_path = os.path.join(langpath, "LC_MESSAGES")
                    if os.path.isdir(lc_messages_path):
                        po_file = os.path.join(lc_messages_path, f"{APP_NAME}.po")
                        if os.path.isfile(po_file):
                            dest_lang_dir = os.path.join(LOCALE_DIR, langdir, "LC_MESSAGES")
                            os.makedirs(dest_lang_dir, exist_ok=True)
                            mo_file = os.path.join(dest_lang_dir, f"{APP_NAME}.mo")
                            log.info(f"Compiling {po_file} to {mo_file}")
                            subprocess.run(["msgfmt", "-o", mo_file, po_file], check=False)
        else:
            log.info("No 'locale' directory found. Skipping .po compilation.")

        # 5. Create wrapper script
        log.info(f"Creating wrapper script at {WRAPPER_PATH}")
        with open(WRAPPER_PATH, "w", encoding="utf-8") as wf:
            wf.write("#!/bin/sh\n")
            wf.write(f'exec python3 "{INSTALL_DIR}/{PY_SCRIPT}" "$@"\n')
        os.chmod(WRAPPER_PATH, 0o755)

        # 6. Create .desktop file
        log.info(f"Creating .desktop file at {DESKTOP_FILE_PATH}")
        desktop_contents = f"""[Desktop Entry]
Type=Application
Name=GhostBSD Hearing Aid Setup
Comment=Wizard for pairing and configuring Bluetooth hearing aids on GhostBSD
Exec={WRAPPER_PATH}
Icon=bluetooth
Terminal=false
Categories=AudioVideo;GTK;Utility;
"""
        with open(DESKTOP_FILE_PATH, "w", encoding="utf-8") as df:
            df.write(desktop_contents)
        os.chmod(DESKTOP_FILE_PATH, 0o644)

        log.info("======================================================")
        log.info("Installation complete!")
        log.info("Launch the wizard via 'ghostbsd-hearingaid-setup' or find 'GhostBSD Hearing Aid Setup' in your menu.")
        log.info("If Bluetooth audio fails, recompile PulseAudio from ports with BT support.")
        log.info("======================================================")


setup(
    name="GhostBSDHearingAidSetup",
    version="1.1.0",
    description="GhostBSD Hearing Aid Setup Wizard (No separate BT module package)",
    author="YourName",
    author_email="you@example.com",
    license="MIT",
    cmdclass={
        'install': InstallGhostBSDWizard,
    },
)

