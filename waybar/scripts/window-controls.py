#!/usr/bin/python3

"""Touch-friendly controls for River's currently focused view."""

import fcntl
import json
import os
import subprocess
import sys


def current_layout_mode():
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
    try:
        with open(
            os.path.join(runtime_dir, "river-global-layout-mode"),
            encoding="utf-8",
        ) as state:
            return state.readline().strip()
    except OSError:
        return "tiled"


def print_status():
    if current_layout_mode() == "floating":
        status = {
            "text": "WIN",
            "class": "active",
            "tooltip": "Touch controls for the focused window",
        }
    else:
        status = {"text": "", "class": "hidden", "tooltip": ""}
    print(json.dumps(status))


if len(sys.argv) > 1 and sys.argv[1] == "--status":
    print_status()
    raise SystemExit(0)


import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gdk, Gtk

from layer_popup import configure_layer_popup


def river(*arguments):
    try:
        subprocess.Popen(
            ["riverctl", *arguments],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        pass


class WindowControls(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.set_name("window-controls")
        self.set_decorated(False)
        self.set_resizable(False)
        self.connect("key-press-event", self.on_key_press)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=9)
        outer.set_border_width(16)
        card.pack_start(outer, True, True, 0)
        configure_layer_popup(
            self,
            card,
            "window-controls",
            top=4,
            right=10,
            preserve_view_focus=True,
        )

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title = Gtk.Label(label="Focused window")
        title.set_xalign(0)
        title.get_style_context().add_class("title")
        header.pack_start(title, True, True, 0)
        dismiss = self.button("×", self.close, "Close this control panel")
        dismiss.get_style_context().add_class("dismiss")
        header.pack_end(dismiss, False, False, 0)
        outer.pack_start(header, False, False, 0)

        outer.pack_start(
            self.section(
                "Select",
                [
                    ("Previous", ("focus-view", "previous")),
                    ("Next", ("focus-view", "next")),
                ],
            ),
            False,
            False,
            0,
        )

        movement = Gtk.Grid(column_spacing=5, row_spacing=5)
        movement.set_column_homogeneous(True)
        movement.attach(self.command_button("↑", "move", "up", "50"), 1, 0, 1, 1)
        movement.attach(self.command_button("←", "move", "left", "50"), 0, 1, 1, 1)
        movement.attach(self.label("Move"), 1, 1, 1, 1)
        movement.attach(self.command_button("→", "move", "right", "50"), 2, 1, 1, 1)
        movement.attach(self.command_button("↓", "move", "down", "50"), 1, 2, 1, 1)
        outer.pack_start(movement, False, False, 0)

        size = Gtk.Grid(column_spacing=5, row_spacing=5)
        size.set_column_homogeneous(True)
        size.attach(self.label("Width"), 0, 0, 1, 1)
        size.attach(self.command_button("−", "resize", "horizontal", "-80"), 1, 0, 1, 1)
        size.attach(self.command_button("+", "resize", "horizontal", "80"), 2, 0, 1, 1)
        size.attach(self.label("Height"), 0, 1, 1, 1)
        size.attach(self.command_button("−", "resize", "vertical", "-60"), 1, 1, 1, 1)
        size.attach(self.command_button("+", "resize", "vertical", "60"), 2, 1, 1, 1)
        outer.pack_start(size, False, False, 0)

        outer.pack_start(
            self.section(
                "Snap",
                [
                    ("Left", ("snap", "left")),
                    ("Top", ("snap", "up")),
                    ("Bottom", ("snap", "down")),
                    ("Right", ("snap", "right")),
                ],
            ),
            False,
            False,
            0,
        )

        monitor = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        monitor_label = self.label("Monitor")
        monitor_label.set_size_request(62, -1)
        monitor_label.set_xalign(0)
        monitor.pack_start(monitor_label, False, False, 0)
        monitor.pack_start(
            self.button(
                "Previous + follow",
                lambda: self.send_and_follow("previous"),
            ),
            True,
            True,
            0,
        )
        monitor.pack_start(
            self.button(
                "Next + follow",
                lambda: self.send_and_follow("next"),
            ),
            True,
            True,
            0,
        )
        outer.pack_start(monitor, False, False, 0)

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        actions.set_homogeneous(True)
        actions.pack_start(
            self.command_button("Float / Tile", "toggle-float"), True, True, 0
        )
        actions.pack_start(
            self.command_button("Fullscreen", "toggle-fullscreen"), True, True, 0
        )
        close = self.button("Close", self.close_view, "Close the focused application")
        close.get_style_context().add_class("destructive")
        actions.pack_start(close, True, True, 0)
        outer.pack_start(actions, False, False, 0)

    @staticmethod
    def label(text):
        label = Gtk.Label(label=text)
        label.get_style_context().add_class("control-label")
        return label

    def button(self, text, callback, tooltip=None):
        button = Gtk.Button(label=text)
        button.set_relief(Gtk.ReliefStyle.NONE)
        if tooltip:
            button.set_tooltip_text(tooltip)
        button.connect("clicked", lambda _button: callback())
        return button

    def command_button(self, text, *command):
        return self.button(text, lambda: river(*command))

    def section(self, heading, actions):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        label = self.label(heading)
        label.set_size_request(62, -1)
        label.set_xalign(0)
        row.pack_start(label, False, False, 0)
        for text, command in actions:
            row.pack_start(self.command_button(text, *command), True, True, 0)
        return row

    def close_view(self):
        river("close")
        self.close()

    def send_and_follow(self, direction):
        try:
            subprocess.run(
                ["riverctl", "send-to-output", "-current-tags", direction],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                ["riverctl", "focus-output", direction],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.CalledProcessError):
            return
        self.close()

    def on_key_press(self, _window, event):
        if event.keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False


def install_style():
    css = b"""
    window#window-controls {
        background-color: transparent;
    }
    #window-controls-card {
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
    label.control-label {
        color: #A8B4C3;
    }
    button {
        min-height: 26px;
        min-width: 32px;
        padding: 3px 8px;
        color: #EEF2F6;
        background-color: #17283D;
        border: 1px solid #27374A;
        border-radius: 5px;
    }
    button:hover,
    button:active {
        color: #08111F;
        background-color: #D6AE4A;
        border-color: #D6AE4A;
    }
    button.dismiss {
        min-height: 20px;
        min-width: 20px;
        padding: 0 5px;
        background: transparent;
        border-color: transparent;
    }
    button.destructive {
        color: #EEF2F6;
        background-color: #B94747;
        border-color: #B94747;
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
    lock = open(os.path.join(runtime_dir, "window-controls.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return 0

    install_style()
    panel = WindowControls()
    panel.connect("destroy", Gtk.main_quit)
    panel.show_all()
    Gtk.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
