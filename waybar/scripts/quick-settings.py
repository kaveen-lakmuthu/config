#!/usr/bin/python3

"""Compact system controls for the River Waybar."""

import fcntl
import glob
import json
import os
import re
import subprocess
import sys
import threading


ROOT = os.path.expanduser("~/.config")
SCRIPTS = os.path.join(ROOT, "waybar", "scripts")
LAPTOP_DEVICE = "amdgpu_bl1"
DDC_SELECTOR = ["--mfg", "GSM", "--model", "RDS-220L"]


def run(command, *, timeout=5):
    try:
        return subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return ""


def spawn(command):
    try:
        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        pass


def script(name, *arguments):
    return [os.path.join(SCRIPTS, name), *arguments]


def layout_mode():
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
    try:
        with open(
            os.path.join(runtime_dir, "river-global-layout-mode"),
            encoding="utf-8",
        ) as state:
            mode = state.readline().strip()
    except OSError:
        mode = "tiled"
    return mode if mode in {"tiled", "floating"} else "tiled"


def microphone():
    command = ["wpctl", "get-volume", "@DEFAULT_AUDIO_SOURCE@"]
    output = run(command)
    match = re.search(r"Volume:\s+([0-9.]+)", output)
    level = round(float(match.group(1)) * 100) if match else None
    return level, "MUTED" in output


def dnd_enabled():
    return "do-not-disturb" in run(["makoctl", "mode"]).splitlines()


def night_enabled():
    output = run(script("night-light", "status"))
    try:
        return json.loads(output).get("class") == "active"
    except json.JSONDecodeError:
        return False


def idle_inhibited():
    return run(script("idle-inhibitor", "status")) == "active"


def power_profile():
    profile = run(script("power-profile", "status"))
    return profile if profile in {"power-saver", "balanced", "performance"} else ""


def status():
    level, muted = microphone()
    dnd = dnd_enabled()
    idle = idle_inhibited()

    if level is not None and not muted:
        css_class = "alert"
    elif dnd or idle:
        css_class = "attention"
    else:
        css_class = "normal"

    details = []
    if level is not None and not muted:
        details.append(f"microphone active at {level}%")
    if dnd:
        details.append("notifications paused")
    if idle:
        details.append("idle actions inhibited")
    tooltip = "System controls"
    if details:
        tooltip += " · " + " · ".join(details)
    print(json.dumps({"text": "SYS", "class": css_class, "tooltip": tooltip}))


if len(sys.argv) > 1 and sys.argv[1] == "--status":
    status()
    raise SystemExit(0)


import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gdk, GLib, Gtk

from layer_popup import configure_layer_popup


def laptop_level():
    output = run(
        ["brightnessctl", "--device", LAPTOP_DEVICE, "--machine-readable", "info"]
    )
    match = re.search(r",(\d+)%,", output)
    return int(match.group(1)) if match else 50


def external_connected():
    for status_path in glob.glob("/sys/class/drm/card*-HDMI-A-1/status"):
        try:
            with open(status_path, encoding="utf-8") as status_file:
                if status_file.read().strip() == "connected":
                    return True
        except OSError:
            pass
    return False


def external_level():
    output = run(["ddcutil", "getvcp", "10", "--brief", *DDC_SELECTOR])
    match = re.search(r"VCP\s+10\s+C\s+(\d+)\s+(\d+)", output)
    if not match or int(match.group(2)) == 0:
        return None
    return round(int(match.group(1)) * 100 / int(match.group(2)))


class QuickSettings(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.set_name("quick-settings")
        self.set_decorated(False)
        self.set_resizable(False)
        self.connect("key-press-event", self.on_key_press)

        self.pending = {}
        self.confirm_timers = {}
        self.mic_scroll_remainder = 0.0

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        outer.set_border_width(16)
        card.pack_start(outer, True, True, 0)
        configure_layer_popup(self, card, "quick-settings", top=4, right=6)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title = Gtk.Label(label="System")
        title.set_xalign(0)
        title.get_style_context().add_class("title")
        header.pack_start(title, True, True, 0)
        close = self.button("×", self.close, "Close")
        close.get_style_context().add_class("dismiss")
        header.pack_end(close, False, False, 0)
        outer.pack_start(header, False, False, 0)

        desktop = self.add_section(outer, "Modes")
        desktop_controls = Gtk.Grid(column_spacing=7, row_spacing=7)
        desktop_controls.set_column_homogeneous(True)
        self.layout_button = self.button("Layout", self.toggle_layout)
        self.night_button = self.button("Night light", self.toggle_night)
        self.idle_button = self.button("Keep awake", self.toggle_idle)
        self.dnd_button = self.button("DND", self.toggle_dnd)
        desktop_controls.attach(self.layout_button, 0, 0, 1, 1)
        desktop_controls.attach(self.night_button, 1, 0, 1, 1)
        desktop_controls.attach(self.idle_button, 0, 1, 1, 1)
        desktop_controls.attach(self.dnd_button, 1, 1, 1, 1)
        desktop.pack_start(desktop_controls, False, False, 0)

        audio = self.add_section(outer, "Audio")
        audio_controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=7)
        audio_controls.set_homogeneous(True)
        self.mic_button = self.button("Microphone", self.toggle_microphone)
        self.mic_button.add_events(Gdk.EventMask.SCROLL_MASK)
        self.mic_button.connect("scroll-event", self.scroll_microphone)
        self.mic_button.set_tooltip_text("Click to mute · scroll to change input level")
        audio_controls.pack_start(self.mic_button, True, True, 0)
        audio_controls.pack_start(
            self.button("Audio settings", lambda: self.launch(["pavucontrol"])),
            True,
            True,
            0,
        )
        audio.pack_start(audio_controls, False, False, 0)

        self.displays = self.add_section(outer, "Displays")
        self.add_slider(
            self.displays, "Laptop", laptop_level(), "laptop", self.set_laptop
        )
        if external_connected():
            self.external_loading = Gtk.Label(label="Reading external monitor…")
            self.external_loading.set_xalign(0)
            self.external_loading.get_style_context().add_class("muted")
            self.displays.pack_start(self.external_loading, False, False, 0)
            threading.Thread(
                target=self.load_external,
                args=(self.displays,),
                daemon=True,
            ).start()

        screenshots = self.add_section(outer, "Screenshots")
        screenshot_controls = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=6,
        )
        screenshot_controls.set_homogeneous(True)
        full = self.button(
            "Full screen",
            lambda: self.launch(
                [os.path.join(ROOT, "river", "scripts", "screenshot"), "full"]
            ),
            "Capture all outputs · Print",
        )
        region = self.button(
            "Region",
            lambda: self.launch(
                [os.path.join(ROOT, "river", "scripts", "screenshot"), "region"]
            ),
            "Select and save a region · Super+Print",
        )
        annotate = self.button(
            "Annotate",
            lambda: self.launch(
                [
                    os.path.join(ROOT, "river", "scripts", "screenshot"),
                    "annotate",
                ]
            ),
            "Select a region and open Swappy · Super+Shift+Print",
        )
        screenshot_controls.pack_start(full, True, True, 0)
        screenshot_controls.pack_start(region, True, True, 0)
        screenshot_controls.pack_start(annotate, True, True, 0)
        screenshots.pack_start(screenshot_controls, False, False, 0)

        settings = self.add_section(outer, "Settings")
        shortcuts = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        shortcuts.set_homogeneous(True)
        shortcuts.pack_start(
            self.button(
                "Notifications",
                lambda: self.launch(script("desktop-panel.py", "notifications")),
            ),
            True,
            True,
            0,
        )
        shortcuts.pack_start(
            self.button("Network", lambda: self.launch(["nm-connection-editor"])),
            True,
            True,
            0,
        )
        shortcuts.pack_start(
            self.button("Bluetooth", lambda: self.launch(["blueman-manager"])),
            True,
            True,
            0,
        )
        settings.pack_start(shortcuts, False, False, 0)

        power_profiles = self.add_section(outer, "Power profile")
        profile_controls = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=6,
        )
        profile_controls.set_homogeneous(True)
        self.power_profile_buttons = {}
        for label, profile in (
            ("Power saver", "power-saver"),
            ("Balanced", "balanced"),
            ("Performance", "performance"),
        ):
            button = self.button(
                label,
                lambda selected=profile: self.set_power_profile(selected),
            )
            self.power_profile_buttons[profile] = button
            profile_controls.pack_start(button, True, True, 0)
        power_profiles.pack_start(profile_controls, False, False, 0)

        session = self.add_section(outer, "Session")
        power = Gtk.Grid(column_spacing=6, row_spacing=6)
        power.set_column_homogeneous(True)
        power.attach(
            self.button(
                "Lock",
                lambda: self.launch(
                    [os.path.join(ROOT, "river", "scripts", "lock-screen")]
                ),
            ),
            0,
            0,
            1,
            1,
        )
        power.attach(
            self.button("Suspend", lambda: self.execute(["systemctl", "suspend"])),
            1,
            0,
            1,
            1,
        )
        power.attach(self.confirm_button("Log out", ["riverctl", "exit"]), 2, 0, 1, 1)
        power.attach(
            self.confirm_button("Restart", ["systemctl", "reboot"]), 0, 1, 1, 1
        )
        power_off = self.confirm_button("Power off", ["systemctl", "poweroff"])
        power_off.get_style_context().add_class("destructive")
        power.attach(power_off, 1, 1, 2, 1)
        session.pack_start(power, False, False, 0)

        self.refresh_toggles()

    @staticmethod
    def heading(text):
        label = Gtk.Label(label=text)
        label.set_xalign(0)
        label.get_style_context().add_class("section")
        return label

    def add_section(self, parent, title):
        frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame.get_style_context().add_class("settings-section")

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        content.set_border_width(12)
        content.pack_start(self.heading(title), False, False, 0)
        frame.add(content)
        parent.pack_start(frame, False, False, 0)
        return content

    def button(self, text, callback, tooltip=None):
        button = Gtk.Button(label=text)
        button.set_relief(Gtk.ReliefStyle.NONE)
        if tooltip:
            button.set_tooltip_text(tooltip)
        button.connect("clicked", lambda _button: callback())
        return button

    def confirm_button(self, text, command):
        button = self.button(text, lambda: self.arm_action(button, text, command))
        return button

    def arm_action(self, button, text, command):
        timer = self.confirm_timers.pop(text, None)
        if timer is not None:
            GLib.source_remove(timer)
            self.execute(command)
            return

        button.set_label(f"Confirm {text.lower()}")

        def reset():
            self.confirm_timers.pop(text, None)
            button.set_label(text)
            return GLib.SOURCE_REMOVE

        self.confirm_timers[text] = GLib.timeout_add_seconds(4, reset)

    def set_toggle(self, button, label, active, *, alert=False):
        button.set_label(label)
        style = button.get_style_context()
        style.remove_class("active")
        style.remove_class("alert")
        if alert:
            style.add_class("alert")
        elif active:
            style.add_class("active")

    def refresh_toggles(self):
        mode = layout_mode()
        self.set_toggle(
            self.layout_button,
            "FLOAT" if mode == "floating" else "TILE",
            mode == "floating",
        )
        self.set_toggle(self.night_button, "Night light", night_enabled())
        idle = idle_inhibited()
        self.set_toggle(
            self.idle_button,
            "Keep awake · ON" if idle else "Keep awake · OFF",
            idle,
        )
        level, muted = microphone()
        if level is None:
            self.set_toggle(self.mic_button, "Mic unavailable", False)
        elif muted:
            self.set_toggle(self.mic_button, f"Mic muted · {level}%", False)
        else:
            self.set_toggle(self.mic_button, f"Mic {level}%", True, alert=True)
        self.set_toggle(self.dnd_button, "DND", dnd_enabled())

        current_profile = power_profile()
        for profile, button in self.power_profile_buttons.items():
            button.set_sensitive(bool(current_profile))
            style = button.get_style_context()
            style.remove_class("active")
            if profile == current_profile:
                style.add_class("active")

    def toggle_layout(self):
        run(script("layout-mode", "toggle"), timeout=8)
        self.refresh_toggles()

    def toggle_night(self):
        run(script("night-light", "toggle"))
        self.refresh_toggles()

    def toggle_idle(self):
        run(script("idle-inhibitor", "toggle"))
        self.refresh_toggles()

    def toggle_microphone(self):
        run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "toggle"])
        self.refresh_toggles()

    def scroll_microphone(self, _button, event):
        success, direction = event.get_scroll_direction()
        if success and direction == Gdk.ScrollDirection.UP:
            adjustment = "5%+"
        elif success and direction == Gdk.ScrollDirection.DOWN:
            adjustment = "5%-"
        else:
            success, _delta_x, delta_y = event.get_scroll_deltas()
            if not success:
                return False
            self.mic_scroll_remainder += delta_y
            if self.mic_scroll_remainder <= -0.5:
                adjustment = "5%+"
                self.mic_scroll_remainder += 0.5
            elif self.mic_scroll_remainder >= 0.5:
                adjustment = "5%-"
                self.mic_scroll_remainder -= 0.5
            else:
                return True

        run(
            [
                "wpctl",
                "set-volume",
                "-l",
                "1.0",
                "@DEFAULT_AUDIO_SOURCE@",
                adjustment,
            ]
        )
        self.refresh_toggles()
        return True

    def toggle_dnd(self):
        action = "-r" if dnd_enabled() else "-a"
        run(["makoctl", "mode", action, "do-not-disturb"])
        self.refresh_toggles()

    def set_power_profile(self, profile):
        run(script("power-profile", "set", profile), timeout=15)
        self.refresh_toggles()

    def add_slider(self, parent, name, level, key, setter):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        label = Gtk.Label(label=name)
        label.set_xalign(0)
        label.set_size_request(65, -1)
        row.pack_start(label, False, False, 0)

        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 100, 1)
        scale.set_draw_value(False)
        scale.set_size_request(250, -1)
        scale.set_value(level)
        row.pack_start(scale, True, True, 0)

        value = Gtk.Label(label=f"{level}%")
        value.set_xalign(1)
        value.set_size_request(40, -1)
        row.pack_end(value, False, False, 0)
        scale.connect("value-changed", self.slider_changed, key, setter, value)
        parent.pack_start(row, False, False, 0)

    def slider_changed(self, scale, key, setter, value):
        level = round(scale.get_value())
        value.set_text(f"{level}%")
        previous = self.pending.pop(key, None)
        if previous is not None:
            GLib.source_remove(previous)
        self.pending[key] = GLib.timeout_add(
            140, self.apply_slider, key, setter, level
        )

    def apply_slider(self, key, setter, level):
        self.pending.pop(key, None)
        setter(level)
        return GLib.SOURCE_REMOVE

    @staticmethod
    def set_laptop(level):
        spawn(
            [
                "brightnessctl",
                "--quiet",
                "--device",
                LAPTOP_DEVICE,
                "set",
                f"{level}%",
            ]
        )

    @staticmethod
    def set_external(level):
        spawn(["ddcutil", "setvcp", "10", str(level), *DDC_SELECTOR, "--noverify"])

    def load_external(self, parent):
        level = external_level()
        GLib.idle_add(self.finish_external, parent, level)

    def finish_external(self, parent, level):
        parent.remove(self.external_loading)
        if level is not None:
            self.add_slider(parent, "External", level, "external", self.set_external)
        parent.show_all()
        return GLib.SOURCE_REMOVE

    def launch(self, command):
        spawn(command)
        self.close()

    def execute(self, command):
        spawn(command)
        self.close()

    def on_key_press(self, _window, event):
        if event.keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False


def install_style():
    css = b"""
    window#quick-settings {
        background-color: transparent;
    }
    #quick-settings-card {
        background-color: #101C2C;
        color: #EEF2F6;
        border: 2px solid #D6AE4A;
        border-radius: 8px;
    }
    label.title {
        color: #D6AE4A;
        font-weight: bold;
        font-size: 12pt;
    }
    label.section {
        color: #D6AE4A;
        font-weight: bold;
    }
    .settings-section {
        background-color: #17283D;
        border: 1px solid #27374A;
        border-radius: 8px;
    }
    label.muted {
        color: #7D8A9B;
    }
    button {
        min-height: 28px;
        padding: 4px 8px;
        color: #EEF2F6;
        background-color: #101C2C;
        border: 1px solid #27374A;
        border-radius: 5px;
    }
    button:hover,
    button:active,
    button.active {
        color: #08111F;
        background-color: #D6AE4A;
        border-color: #D6AE4A;
    }
    button.alert,
    button.destructive {
        color: #EEF2F6;
        background-color: #B94747;
        border-color: #B94747;
    }
    button.dismiss {
        min-height: 20px;
        min-width: 20px;
        padding: 0 5px;
        background: transparent;
        border-color: transparent;
    }
    scale trough {
        min-height: 6px;
        border-radius: 4px;
        background-color: #101C2C;
    }
    scale highlight {
        min-height: 6px;
        border-radius: 4px;
        background-color: #D6AE4A;
    }
    scale slider {
        min-width: 14px;
        min-height: 14px;
        border-radius: 8px;
        background-color: #EEF2F6;
    }
    """
    provider = Gtk.CssProvider()
    provider.load_from_data(css)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )


def main():
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
    lock = open(os.path.join(runtime_dir, "quick-settings.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return 0

    install_style()
    panel = QuickSettings()
    panel.connect("destroy", Gtk.main_quit)
    panel.show_all()
    Gtk.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
