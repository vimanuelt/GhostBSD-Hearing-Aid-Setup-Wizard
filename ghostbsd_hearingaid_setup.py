#!/usr/bin/env python3
#
# ghostbsd_hearingaid_setup_gtk3.py
#
# A GTK3-based wizard for configuring Bluetooth hearing aids on GhostBSD.
# Similar logic to the previous GTK4 code, but uses 'gi.require_version("Gtk", "3.0")'.
#
import gi
gi.require_version("Gtk", "3.0")  # Force GTK 3
from gi.repository import Gtk, GLib
import subprocess
import os
import re
import sys
import shutil
import gettext
from datetime import datetime
from time import sleep
import threading
import logging

APP_NAME = "ghostbsd_hearingaid_setup"
LOCALE_DIR = os.path.join(os.path.dirname(__file__), "locale")

gettext.bindtextdomain(APP_NAME, LOCALE_DIR)
gettext.textdomain(APP_NAME)
_ = gettext.gettext  # Ensure _ is set to gettext.gettext

RC_CONF = "/etc/rc.conf"
HCSECD_CONF = "/etc/bluetooth/hcsecd.conf"
PA_CONF_SYSTEM = "/usr/local/etc/pulse/default.pa"
LOGFILE_PATH = "/var/log/ghostbsd-hearingaid-setup.log"
UBT0_CONF = "/etc/bluetooth/ubt0.conf"

# Configure logging
logging.basicConfig(filename=LOGFILE_PATH, level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WizardWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title=_("GhostBSD Hearing Aid Setup Wizard (GTK3)"))
        self.set_default_size(900, 550)

        self.discovered_devices = {}  # { MAC: (DeviceName, "Classic"/"BLE"/"BLE/Classic") }
        self.ble_devices = set()

        # Wizard pages via Gtk.Stack
        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE, transition_duration=400)

        # New pages for additional setup steps
        self.config_services_page = self.build_config_services_page()
        self.install_packages_page = self.build_install_packages_page()
        self.setup_bluetooth_page = self.build_setup_bluetooth_page()
        self.create_virtual_sound_page = self.build_create_virtual_sound_page()

        self.intro_page = self.build_intro_page()
        self.discover_page = self.build_discover_page()
        self.pair_page = self.build_pair_page()
        self.config_pulseaudio_page = self.build_config_pulseaudio_page()
        self.bridging_page = self.build_bridging_page()
        self.finish_page = self.build_finish_page()

        self.stack.add_named(self.intro_page, "intro")
        self.stack.add_named(self.config_services_page, "config_services")
        self.stack.add_named(self.install_packages_page, "install_packages")
        self.stack.add_named(self.setup_bluetooth_page, "setup_bluetooth")
        self.stack.add_named(self.discover_page, "discover")
        self.stack.add_named(self.pair_page, "pair")
        self.stack.add_named(self.config_pulseaudio_page, "config_pulseaudio")
        self.stack.add_named(self.create_virtual_sound_page, "create_virtual_sound")
        self.stack.add_named(self.bridging_page, "bridge")
        self.stack.add_named(self.finish_page, "finish")

        self.pages = ["intro", "config_services", "install_packages", "setup_bluetooth", "discover", "pair", "config_pulseaudio", "create_virtual_sound", "bridge", "finish"]
        self.current_page = "intro"
        self.stack.set_visible_child_name("intro")

        # Navigation buttons
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.back_button = Gtk.Button(label=_("Back"))
        self.back_button.connect("clicked", self.on_back_clicked)
        nav_box.pack_start(self.back_button, False, False, 0)

        self.next_button = Gtk.Button(label=_("Next"))
        self.next_button.connect("clicked", self.on_next_clicked)
        nav_box.pack_end(self.next_button, False, False, 0)

        # Main layout
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        main_vbox.set_border_width(10)
        main_vbox.pack_start(self.stack, True, True, 0)
        main_vbox.pack_end(nav_box, False, False, 0)

        self.add(main_vbox)

        self.update_nav_buttons()
        self.log_file = None
        self.init_logfile()

        if os.geteuid() != 0:
            self.log(_("WARNING: Run as root for best results."), error=False)


    def init_logfile(self):
        try:
            with open(LOGFILE_PATH, "a", encoding="utf-8") as log_file:
                self.log_file = log_file
                logger.info(f"Log file opened at {LOGFILE_PATH}")
        except PermissionError:
            self.show_error_dialog(
                _("Failed to open log file at {}. Check permissions.").format(LOGFILE_PATH)
            )


    def build_config_services_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        page_title = Gtk.Label(label=_("<b>Step 1: Configure System Services</b>"))
        page_title.set_use_markup(True)
        page_title.set_line_wrap(True)

        config_button = Gtk.Button(label=_("Configure Services"))
        config_button.connect("clicked", self.on_configure_services)

        page.pack_start(page_title, False, False, 0)
        page.pack_start(config_button, False, False, 0)
        return page


    def build_install_packages_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        page_title = Gtk.Label(label=_("<b>Step 2: Install Required Packages</b>"))
        page_title.set_use_markup(True)
        page_title.set_line_wrap(True)

        install_button = Gtk.Button(label=_("Install Packages"))
        install_button.connect("clicked", self.on_install_packages)

        page.pack_start(page_title, False, False, 0)
        page.pack_start(install_button, False, False, 0)
        return page


    def build_setup_bluetooth_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        page_title = Gtk.Label(label=_("<b>Step 3: Setup Bluetooth Configuration</b>"))
        page_title.set_use_markup(True)
        page_title.set_line_wrap(True)

        setup_button = Gtk.Button(label=_("Setup Bluetooth"))
        setup_button.connect("clicked", self.on_setup_bluetooth)

        page.pack_start(page_title, False, False, 0)
        page.pack_start(setup_button, False, False, 0)
        return page


    def build_create_virtual_sound_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        page_title = Gtk.Label(label=_("<b>Step 7: Create Virtual Sound Device</b>"))
        page_title.set_use_markup(True)
        page_title.set_line_wrap(True)

        create_button = Gtk.Button(label=_("Create Virtual Sound"))
        create_button.connect("clicked", self.on_create_virtual_sound)

        self.virtual_sound_text = Gtk.Entry()
        self.virtual_sound_text.set_text("buds")

        page.pack_start(page_title, False, False, 0)
        page.pack_start(Gtk.Label(label=_("Enter device name (e.g., 'buds'):")), False, False, 0)  # Fixed positional arguments issue
        page.pack_start(self.virtual_sound_text, False, False, 0)
        page.pack_start(create_button, False, False, 0)
        return page


    def build_intro_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        page_label = Gtk.Label(label=_("<b>Welcome to GhostBSD Hearing Aid Setup Wizard!</b>"))
        page_label.set_use_markup(True)

        info_label = Gtk.Label(
            label=_("If your hearing aids rely on proprietary BLE/MFi, "
                    "use a bridging accessory.")
        )
        info_label.set_line_wrap(True)

        page.pack_start(page_label, False, False, 0)
        page.pack_start(info_label, True, True, 0)
        return page


    def build_discover_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        page_title = Gtk.Label(label=_("<b>Step 4: Discover Nearby Devices (Classic & BLE)</b>"))
        page_title.set_use_markup(True)
        page_title.set_line_wrap(True)

        discover_button = Gtk.Button(label=_("Discover Devices"))
        discover_button.connect("clicked", self.on_discover_clicked)

        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.buffer = self.textview.get_buffer()

        scroll_log = Gtk.ScrolledWindow()
        scroll_log.add(self.textview)

        page.pack_start(page_title, False, False, 0)
        page.pack_start(discover_button, False, False, 0)
        page.pack_start(scroll_log, True, True, 0)
        return page


    def build_pair_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        page_title = Gtk.Label(label=_("<b>Step 5: Pair Your Hearing Aids</b>"))
        page_title.set_use_markup(True)
        page_title.set_line_wrap(True)

        list_label = Gtk.Label(
            label=_("Select a device below and click 'Pair Selected Device'. If BLE-only or proprietary, bridging may be required.")
        )
        list_label.set_line_wrap(True)

        self.store = Gtk.ListStore(str, str, str)  # [MAC, DeviceName, Type]
        self.treeview = Gtk.TreeView(model=self.store)

        renderer_text = Gtk.CellRendererText()
        col_mac = Gtk.TreeViewColumn(_("MAC Address"), renderer_text, text=0)
        col_name = Gtk.TreeViewColumn(_("Device Name"), renderer_text, text=1)
        col_type = Gtk.TreeViewColumn(_("Type"), renderer_text, text=2)

        self.treeview.append_column(col_mac)
        self.treeview.append_column(col_name)
        self.treeview.append_column(col_type)

        self.treeview.connect("row-activated", self.on_treeview_row_activated)

        scroll_devices = Gtk.ScrolledWindow()
        scroll_devices.add(self.treeview)

        self.pair_button = Gtk.Button(label=_("Pair Selected Device"))
        self.pair_button.connect("clicked", self.on_pair_selected_device)

        page.pack_start(page_title, False, False, 0)
        page.pack_start(list_label, False, False, 0)
        page.pack_start(scroll_devices, True, True, 0)
        page.pack_start(self.pair_button, False, False, 0)
        return page


    def build_config_pulseaudio_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        page_title = Gtk.Label(label=_("<b>Step 6: Configure PulseAudio</b>"))
        page_title.set_use_markup(True)
        page_title.set_line_wrap(True)

        desc_label = Gtk.Label(
            label=_("We'll attempt to load 'module-bluetooth-discover'. If that fails, recompile PulseAudio from ports with BT support.")
        )
        desc_label.set_line_wrap(True)

        config_button = Gtk.Button(label=_("Try Configure PulseAudio"))
        config_button.connect("clicked", self.on_configure_system)

        page.pack_start(page_title, False, False, 0)
        page.pack_start(desc_label, False, False, 0)
        page.pack_start(config_button, False, False, 0)
        return page


    def build_bridging_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        page_title = Gtk.Label(label=_("<b>Step 8: Bridging Accessory Info</b>"))
        page_title.set_use_markup(True)
        page_title.set_line_wrap(True)

        bridging_label = Gtk.Label(
            label=_("If direct pairing fails, bridging dongles from the manufacturer may be needed. Click below to see bridging docs.")
        )
        bridging_label.set_line_wrap(True)

        bridging_button = Gtk.Button(label=_("View Bridging Documentation"))
        bridging_button.connect("clicked", self.on_show_bridging_doc)

        page.pack_start(page_title, False, False, 0)
        page.pack_start(bridging_label, True, True, 0)
        page.pack_start(bridging_button, False, False, 0)
        return page


    def build_finish_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        page_label = Gtk.Label(label=_("<b>Finished Setup</b>"))
        page_label.set_use_markup(True)
        page_label.set_line_wrap(True)

        finish_text = Gtk.Label(
            label=_("If your hearing aids appear as a standard Bluetooth device, set them as default in pavucontrol. "
                    "Otherwise, bridging or advanced debug is required. Logs are in /var/log/ghostbsd-hearingaid-setup.log.")
        )
        finish_text.set_line_wrap(True)

        page.pack_start(page_label, False, False, 0)
        page.pack_start(finish_text, True, True, 0)
        return page


    # New methods for additional steps
    def on_configure_services(self, button):
        self.log(_("Updating /etc/rc.conf for Bluetooth services..."), error=False)
        self.enable_rc_conf("sdpd_enable", "YES")
        self.enable_rc_conf("hcsecd_enable", "YES")
        self.log(_("Services configured in rc.conf."), error=False)


    def on_install_packages(self, button):
        self.log(_("Installing necessary packages..."), error=False)
        packages = ["iwmbt-firmware", "virtual_oss"]
        for package in packages:
            ret, _ = self.run_command(["pkg", "install", "-y", package], raise_on_error=False)
            if ret == 0:
                self.log(_("Successfully installed {}").format(package), error=False)
            else:
                self.log(_("Failed to install {}").format(package), error=True)


    def on_setup_bluetooth(self, button):
        self.log(_("Setting up Bluetooth configuration..."), error=False)
        if not os.path.exists(UBT0_CONF):
            self.log(_("Creating {}").format(UBT0_CONF), error=False)
            try:
                with open(UBT0_CONF, "w") as f:
                    f.write("""authentication_enable="YES"
connectable="YES"
discoverable="YES"
role_switch="YES"
""")
            except Exception as e:
                self.log(_("Failed to create {}: {}").format(UBT0_CONF, e), error=True)
        else:
            self.log(_("{} already exists.").format(UBT0_CONF), error=False)
        
        self.log(_("Restarting system to apply Bluetooth settings..."), error=False)
        self.run_command(["reboot"], raise_on_error=False)  # Note: This command will close the application


    def on_create_virtual_sound(self, button):
        _ = gettext.gettext  # Ensure _ is a function
        device_name = self.virtual_sound_text.get_text()
        if not device_name:
            self.log(_("Please enter a device name."), error=True)
            return

        command = f"virtual_oss -T /dev/sndstat -S -a o,-4 -C 2 -c 2 -r 44100 -b 16 -s 1024 -R /dev/dsp0 -P /dev/bluetooth/{device_name} -d dsp -t vdsp.ctl"
        ret, _ = self.run_command(command.split(), raise_on_error=False)
        if ret == 0:
            self.log(_("Virtual sound device created successfully."), error=False)
        else:
            self.log(_("Failed to create virtual sound device. Try changing sample rate to 48000 if sound is strange."), error=True)


    # Navigation
    def update_nav_buttons(self):
        idx = self.pages.index(self.current_page)
        self.back_button.set_sensitive(idx > 0)
        if self.current_page == "finish":
            self.next_button.set_label(_("Close"))
        else:
            self.next_button.set_label(_("Next"))

    def on_back_clicked(self, button):
        idx = self.pages.index(self.current_page)
        if idx > 0:
            self.current_page = self.pages[idx - 1]
            self.stack.set_visible_child_name(self.current_page)
            self.update_nav_buttons()

    def on_next_clicked(self, button):
        idx = self.pages.index(self.current_page)
        if idx < len(self.pages) - 1:
            self.current_page = self.pages[idx + 1]
            self.stack.set_visible_child_name(self.current_page)
            self.update_nav_buttons()
        else:
            # finish
            self.destroy()


    # Discovery logic
    def on_discover_clicked(self, button):
        self.store.clear()
        self.discovered_devices.clear()
        self.ble_devices.clear()

        self.log(_("=== Checking tools (hccontrol, usbconfig, pulseaudio)... ==="), error=False)
        for tool in ["hccontrol", "usbconfig", "pulseaudio"]:
            if shutil.which(tool) is None:
                self.log(_("ERROR: Required tool '{}' not found.").format(tool), error=True)
                return

        self.log(_("Enabling Bluetooth in /etc/rc.conf..."), error=False)
        self.enable_rc_conf("bluetooth_enable", "YES")
        self.enable_rc_conf("hcsecd_enable", "YES")
        self.enable_rc_conf("sdpd_enable", "YES")

        self.run_command(["kldload", "ng_ubt"], raise_on_error=False)
        self.run_command(["service", "hcsecd", "stop"], raise_on_error=False)
        self.run_command(["service", "sdpd", "stop"], raise_on_error=False)
        self.run_command(["service", "hcsecd", "start"], raise_on_error=False)
        self.run_command(["service", "sdpd", "start"], raise_on_error=False)

        self.log(_("Checking adapter via usbconfig..."), error=False)
        self.run_command(["usbconfig", "list"], raise_on_error=False)

        self.log(_("=== Discovering Classic Bluetooth devices ==="), error=False)
        ret, output = self.run_command(["hccontrol", "-n", "ubt0hci", "inquiry"], raise_on_error=False)
        if ret == 0 and output:
            lines = output.split("\n")
            current_mac = None
            device_name = None
            for line in lines:
                line = line.strip()
                if line.startswith("Inquiry result, bdaddr"):
                    match = re.search(r'bdaddr\s+([0-9A-Fa-f:]+)', line)
                    if match:
                        current_mac = match.group(1)
                        device_name = _("(unknown)")
                elif line.startswith("Name:"):
                    match = re.search(r'Name:\s+"(.*)"', line)
                    if match and current_mac:
                        device_name = match.group(1)
                if current_mac and device_name:
                    self.discovered_devices[current_mac] = (device_name, "Classic")
                    self.log(_("Found Classic BT device: {} - {}").format(current_mac, device_name), error=False)
                    current_mac = None
                    device_name = None
        else:
            self.log(_("No classic devices found or inquiry failed."), error=False)

        self.log(_("=== Attempting BLE scan (experimental) ==="), error=False)
        self.run_command(["hccontrol", "-n", "ubt0hci", "le_set_scan_params", "0", "0x10", "0x10", "0", "0"], raise_on_error=False)
        self.run_command(["hccontrol", "-n", "ubt0hci", "le_set_scan_enable", "1", "0"], raise_on_error=False)
        self.log(_("Waiting 5s for BLE advertisements..."), error=False)

        
        def delay_scan():
            sleep(5)
            self.run_command(["hccontrol", "-n", "ubt0hci", "le_set_scan_enable", "0", "0"], raise_on_error=False)
            GLib.idle_add(self.continue_after_scan)

        threading.Thread(target=delay_scan).start()


    def continue_after_scan(self):
        ret, dmesg_out = self.run_command(["dmesg"], raise_on_error=False)
        ble_macs = re.findall(r'LE Address: ([0-9A-Fa-f:]{17})', dmesg_out or "")
        ble_macs = list(set(ble_macs))

        for addr in ble_macs:
            if addr not in self.discovered_devices:
                self.discovered_devices[addr] = (_("(unknown BLE device)"), "BLE")
                self.log(_("Found BLE device: {}").format(addr), error=False)
                self.ble_devices.add(addr)
            else:
                dev_name, dev_type = self.discovered_devices[addr]
                dev_type = "BLE/Classic"
                self.discovered_devices[addr] = (dev_name, dev_type)

        # Check remote features
        for bdaddr, (name, devtype) in self.discovered_devices.items():
            self.log(_("Checking features for {}").format(bdaddr), error=False)
            ret_feat, feat_out = self.run_command(["hccontrol", "-n", "ubt0hci", "read_remote_supported_features", bdaddr], raise_on_error=False)
            if ret_feat != 0 or ("No error" not in feat_out):
                self.log(_("WARNING: {} might be BLE-only or proprietary.").format(bdaddr), error=False)

        for bdaddr, (dev_name, dev_type) in self.discovered_devices.items():
            self.store.append([bdaddr, dev_name, dev_type])

        self.log(_("Discovery complete. Proceed to 'Pair' page."), error=False)
        self.current_page = "pair"
        self.stack.set_visible_child_name("pair")
        self.update_nav_buttons()


    def on_treeview_row_activated(self, treeview, path, column):
        model = self.treeview.get_model()
        treeiter = model.get_iter(path)
        if treeiter:
            bdaddr = model.get_value(treeiter, 0)
            self.pair_device(bdaddr)


    def on_pair_selected_device(self, button):
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            bdaddr = model.get_value(treeiter, 0)
            self.pair_device(bdaddr)
        else:
            self.log(_("No device selected."), error=True)


    def pair_device(self, bdaddr):
        if not re.match(r'^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}$', bdaddr):
            self.log(_("Invalid MAC address format: {}").format(bdaddr), error=True)
            return
        self.log(_("Pairing with device: {}").format(bdaddr), error=False)
        self.setup_hcsecd_conf(bdaddr)
        ret, _ = self.run_command(["hccontrol", "-n", "ubt0hci", "create_connection", bdaddr], raise_on_error=False)
        if ret != 0:
            self.log(_("Connection attempt failed. Possibly BLE-only."), error=True)
        else:
            self.log(_("Connection attempt succeeded or in progress."), error=False)


    def on_configure_system(self, button):
        self.log(_("Trying to load 'module-bluetooth-discover' in PulseAudio..."), error=False)
        if not os.path.isfile(PA_CONF_SYSTEM):
            self.log(_("WARNING: No default.pa found at {}").format(PA_CONF_SYSTEM), error=True)
            return

        with open(PA_CONF_SYSTEM, "r") as f:
            content = f.read()

        updated = False
        if "module-bluetooth-discover" not in content:
            with open(PA_CONF_SYSTEM, "a") as f:
                f.write("\nload-module module-bluetooth-discover\n")
            updated = True

        if updated:
            self.log(_("Appended 'load-module module-bluetooth-discover' to {}").format(PA_CONF_SYSTEM), error=False)
        else:
            self.log(_("module-bluetooth-discover already present."), error=False)

        self.log(_("Restarting PulseAudio..."), error=False)
        self.run_command(["pulseaudio", "--kill"], raise_on_error=False)
        self.run_command(["pulseaudio", "--start"], raise_on_error=False)
        self.log(_("If it fails, recompile PulseAudio with Bluetooth."), error=False)


    def on_show_bridging_doc(self, button):
        bridging_doc = "bridging_info.md"
        if os.path.isfile(bridging_doc):
            self.log(_("Opening bridging doc: {}").format(bridging_doc), error=False)
            try:
                subprocess.run(["xdg-open", bridging_doc])
            except Exception as e:
                self.log(_("Failed to open bridging doc: {}").format(e), error=True)
        else:
            self.log(_("No bridging_info.md found."), error=False)


    # Utility
    def run_command(self, cmd_list, raise_on_error=True):
        cmd_str = " ".join(cmd_list)
        self.log(f"[CMD] {cmd_str}", error=False)
        try:
            result = subprocess.run(cmd_list, capture_output=True, text=True, check=False)
            if result.stdout:
                self.log(result.stdout.strip(), error=False)
            if result.stderr:
                self.log(f"STDERR: {result.stderr.strip()}", error=False)

            if raise_on_error and result.returncode != 0:
                err_msg = _("Command failed: {} (retcode {})").format(cmd_str, result.returncode)
                self.log(err_msg, error=True)
            return result.returncode, result.stdout
        except subprocess.CalledProcessError as e:
            self.log(f"Command '{cmd_str}' failed with return code {e.returncode}: {e.output}", error=True)
            if raise_on_error:
                raise
        except Exception as e:
            self.log(f"Unexpected error running '{cmd_str}': {e}", error=True)
            if raise_on_error:
                raise
        return 1, ""


    def log(self, text, error=False):
        if error:
            logger.error(text)
        else:
            logger.info(text)
        
        # GUI update
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"[{timestamp}] {text}\n"
        end_iter = self.buffer.get_end_iter()
        self.buffer.insert(end_iter, message)

        # Write to log file if open
        if self.log_file:
            try:
                self.log_file.write(message)
                self.log_file.flush()
            except Exception:
                pass

        if error:
            self.show_error_dialog(text)


    def show_error_dialog(self, error_message):
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=_("Error")
        )
        dialog.format_secondary_text(error_message)
        dialog.run()
        dialog.destroy()


    def enable_rc_conf(self, key, value):
        if not os.path.isfile(RC_CONF):
            self.log(_("ERROR: Cannot find {}.").format(RC_CONF), error=True)
            return
        try:
            with open(RC_CONF, "r") as f:
                lines = f.readlines()
            modified = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f'{key}='):
                    lines[i] = f'{key}="{value}"\n'
                    modified = True
            if not modified:
                lines.append(f'{key}="{value}"\n')
            with open(RC_CONF, "w") as f:
                f.writelines(lines)
        except Exception as e:
            self.log(_("Failed to modify {}: {}").format(RC_CONF, e), error=True)


    def setup_hcsecd_conf(self, bdaddr):
        self.log(_("Updating {} for pairing with {}").format(HCSECD_CONF, bdaddr), error=False)
        if os.path.isfile(HCSECD_CONF):
            backup_path = f"{HCSECD_CONF}.bak.{int(GLib.get_real_time()/1000)}"
            try:
                shutil.copyfile(HCSECD_CONF, backup_path)
                self.log(_("Backed up existing hcsecd.conf to {}").format(backup_path), error=False)
            except Exception as e:
                self.log(_("ERROR: Failed to backup hcsecd.conf - {}").format(e), error=True)

        conf_content = f"""##
# hcsecd.conf for pairing a hearing aid or standard BT device.
device {{
    bdaddr = "{bdaddr}";
    name = "MyHearingAids";
    key = nokey;
    pin = "0000";
}}
"""
        try:
            with open(HCSECD_CONF, "w") as f:
                f.write(conf_content)
        except Exception as e:
            self.log(_("ERROR: Failed to write to hcsecd.conf - {}").format(e), error=True)

        self.run_command(["service", "hcsecd", "restart"], raise_on_error=False)
        self.run_command(["service", "sdpd", "restart"], raise_on_error=False)
        self.log(_("Bluetooth services restarted with updated config."), error=False)


def main():
    win = WizardWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()

