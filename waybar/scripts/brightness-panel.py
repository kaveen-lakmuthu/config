#!/usr/bin/python3

import fcntl
import glob
import os
import re
import subprocess
import sys
import threading

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gdk, GLib, Gtk, GtkLayerShell


LAPTOP_DEVICE = "amdgpu_bl1"
DDC_SELECTOR = ["--mfg", "GSM", "--model", "RDS-220L"]


def run(command, timeout=5):
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


def laptop_level():
    output = run(
        ["brightnessctl", "--device", LAPTOP_DEVICE, "--machine-readable", "info"]
    )
    match = re.search(r",(\d+)%,", output)
    return int(match.group(1)) if match else 50


def external_connected():
    for status_path in glob.glob("/sys/class/drm/card*-HDMI-A-1/status"):
        try:
            if open(status_path, encoding="utf-8").read().strip() == "connected":
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


class BrightnessPanel(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.set_name("brightness-panel")
        self.set_decorated(False)
        self.set_resizable(False)
        self.connect("key-press-event", self.on_key_press)

        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, "brightness-panel")
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)
        # Waybar's exclusive zone already accounts for its own height.
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 4)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, 10)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.ON_DEMAND)

        self.pending = {}
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        outer.set_border_width(14)
        self.add(outer)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title = Gtk.Label(label="Brightness")
        title.set_xalign(0)
        title.get_style_context().add_class("title")
        header.pack_start(title, True, True, 0)

        close = Gtk.Button(label="×")
        close.set_relief(Gtk.ReliefStyle.NONE)
        close.connect("clicked", lambda _button: self.close())
        header.pack_end(close, False, False, 0)
        outer.pack_start(header, False, False, 0)

        self.add_slider(
            outer,
            "Laptop",
            laptop_level(),
            "laptop",
            self.set_laptop,
        )

        if external_connected():
            loading = Gtk.Label(label="Reading external monitor…")
            loading.set_xalign(0)
            outer.pack_start(loading, False, False, 0)
            threading.Thread(
                target=self.load_external,
                args=(outer, loading),
                daemon=True,
            ).start()

    def load_external(self, parent, loading):
        level = external_level()
        GLib.idle_add(self.finish_external_load, parent, loading, level)

    def finish_external_load(self, parent, loading, level):
        parent.remove(loading)
        if level is not None:
            self.add_slider(
                parent,
                "External",
                level,
                "external",
                self.set_external,
            )
        parent.show_all()
        return GLib.SOURCE_REMOVE

    def add_slider(self, parent, name, level, key, setter):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        name_label = Gtk.Label(label=name)
        name_label.set_xalign(0)
        name_label.set_size_request(70, -1)
        row.pack_start(name_label, False, False, 0)

        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 100, 1)
        scale.set_draw_value(False)
        scale.set_size_request(240, -1)
        scale.set_value(level)
        row.pack_start(scale, True, True, 0)

        value_label = Gtk.Label(label=f"{level}%")
        value_label.set_xalign(1)
        value_label.set_size_request(42, -1)
        row.pack_end(value_label, False, False, 0)

        scale.connect(
            "value-changed", self.on_value_changed, key, setter, value_label
        )
        parent.pack_start(row, False, False, 0)

    def on_value_changed(self, scale, key, setter, value_label):
        level = round(scale.get_value())
        value_label.set_text(f"{level}%")

        previous = self.pending.pop(key, None)
        if previous is not None:
            GLib.source_remove(previous)

        self.pending[key] = GLib.timeout_add(
            140, self.apply_level, key, setter, level
        )

    def apply_level(self, key, setter, level):
        self.pending.pop(key, None)
        setter(level)
        return GLib.SOURCE_REMOVE

    @staticmethod
    def set_laptop(level):
        subprocess.Popen(
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
        subprocess.Popen(
            [
                "ddcutil",
                "setvcp",
                "10",
                str(level),
                *DDC_SELECTOR,
                "--noverify",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def on_key_press(self, _window, event):
        if event.keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False


def install_style():
    css = b"""
    window#brightness-panel {
        background-color: #101C2C;
        color: #EEF2F6;
        border: 2px solid #D6AE4A;
        border-radius: 8px;
    }
    label.title {
        font-weight: bold;
        font-size: 12pt;
    }
    button {
        color: #EEF2F6;
        background: transparent;
        border: none;
        padding: 0 4px;
    }
    scale trough {
        min-height: 6px;
        border-radius: 4px;
        background-color: #17283D;
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
    lock = open(os.path.join(runtime_dir, "brightness-panel.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return 0

    install_style()
    panel = BrightnessPanel()
    panel.connect("destroy", Gtk.main_quit)
    panel.show_all()
    Gtk.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
