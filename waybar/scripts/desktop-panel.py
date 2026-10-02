#!/usr/bin/python3

import fcntl
import html
import json
import os
import subprocess
import sys
import threading

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gdk, GLib, Gtk, GtkLayerShell, Pango


def run(command, *, input_data=None):
    try:
        return subprocess.run(
            command,
            input=input_data,
            capture_output=True,
            timeout=8,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None


def run_json(command):
    result = run(command)
    if result is None:
        return []
    try:
        return json.loads(result.stdout.decode("utf-8", errors="replace"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return []


def mako_modes():
    result = run(["makoctl", "mode"])
    if result is None:
        return set()
    return set(result.stdout.decode("utf-8", errors="replace").splitlines())


def notification_status():
    dnd = "do-not-disturb" in mako_modes()
    count = len(run_json(["makoctl", "list", "-j"]))
    count += len(run_json(["makoctl", "history", "-j"]))
    label = "DND" if dnd else "NOTIF"
    if count:
        label += f" {count}"
    print(
        json.dumps(
            {
                "text": label,
                "tooltip": (
                    "Notifications paused" if dnd else "Notification history"
                ),
                "class": "dnd" if dnd else "active",
            }
        ),
        flush=True,
    )


class Panel(Gtk.Window):
    def __init__(self, title, lock_name):
        runtime_dir = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
        self.lock = open(os.path.join(runtime_dir, lock_name), "w")
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit(0)

        super().__init__()
        self.set_name("desktop-panel")
        self.set_decorated(False)
        self.set_resizable(False)
        self.connect("key-press-event", self.on_key_press)

        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, "desktop-panel")
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)
        # Waybar's exclusive zone already accounts for its own height.
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 4)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, 6)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.ON_DEMAND)

        self.outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.outer.set_border_width(12)
        self.add(self.outer)

        self.header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title_label = Gtk.Label(label=title)
        title_label.set_xalign(0)
        title_label.get_style_context().add_class("title")
        self.header.pack_start(title_label, True, True, 0)

        close = Gtk.Button(label="×")
        close.set_relief(Gtk.ReliefStyle.NONE)
        close.connect("clicked", lambda _button: self.close())
        self.header.pack_end(close, False, False, 0)
        self.outer.pack_start(self.header, False, False, 0)

        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_size_request(430, 420)
        self.outer.pack_start(self.scroll, True, True, 0)

    def set_content(self, widget):
        old = self.scroll.get_child()
        if old is not None:
            self.scroll.remove(old)
        self.scroll.add(widget)
        self.show_all()

    def add_confirm_button(self, label, callback):
        button = Gtk.Button(label=label)
        button.get_style_context().add_class("destructive")
        state = {"armed": False, "reset": None}

        def reset():
            state["armed"] = False
            state["reset"] = None
            button.set_label(label)
            return GLib.SOURCE_REMOVE

        def clicked(_button):
            if not state["armed"]:
                state["armed"] = True
                button.set_label("Confirm clear")
                state["reset"] = GLib.timeout_add_seconds(4, reset)
                return
            if state["reset"] is not None:
                GLib.source_remove(state["reset"])
            reset()
            callback()

        button.connect("clicked", clicked)
        self.header.pack_end(button, False, False, 0)
        return button

    def empty_label(self, text):
        label = Gtk.Label(label=text)
        label.set_margin_top(24)
        label.set_margin_bottom(24)
        label.get_style_context().add_class("muted")
        return label

    def on_key_press(self, _window, event):
        if event.keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False


class ClipboardPanel(Panel):
    def __init__(self):
        super().__init__("Clipboard", "clipboard-panel.lock")
        self.add_confirm_button("Clear", self.clear_history)
        self.refresh()

    def history(self):
        result = run(["cliphist", "list"])
        if result is None:
            return []
        return result.stdout.decode("utf-8", errors="replace").splitlines()

    def refresh(self):
        entries = self.history()
        if not entries:
            self.set_content(self.empty_label("Clipboard history is empty"))
            return

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        for entry in entries[:40]:
            preview = entry.split("\t", 1)[-1].strip() or "Empty item"
            button = Gtk.Button()
            button.set_relief(Gtk.ReliefStyle.NONE)
            button.get_style_context().add_class("history-row")
            label = Gtk.Label(label=preview)
            label.set_xalign(0)
            label.set_ellipsize(Pango.EllipsizeMode.END)
            label.set_max_width_chars(58)
            button.add(label)
            button.connect("clicked", self.copy_entry, entry)
            content.pack_start(button, False, False, 0)
        self.set_content(content)

    def copy_entry(self, _button, entry):
        def worker():
            decoded = run(
                ["cliphist", "decode"], input_data=(entry + "\n").encode()
            )
            if decoded is not None:
                run(["wl-copy"], input_data=decoded.stdout)
            GLib.idle_add(self.close)

        threading.Thread(target=worker, daemon=True).start()

    def clear_history(self):
        if run(["cliphist", "wipe"]) is not None:
            self.refresh()


class NotificationPanel(Panel):
    def __init__(self):
        super().__init__("Notifications", "notification-panel.lock")

        self.dnd = Gtk.Switch()
        self.dnd.set_active("do-not-disturb" in mako_modes())
        self.dnd.connect("state-set", self.set_dnd)
        self.header.pack_end(self.dnd, False, False, 0)

        dnd_label = Gtk.Label(label="DND")
        dnd_label.get_style_context().add_class("muted")
        self.header.pack_end(dnd_label, False, False, 0)

        restore = Gtk.Button(label="Restore latest")
        restore.connect("clicked", self.restore_latest)
        self.header.pack_end(restore, False, False, 0)
        self.add_confirm_button("Clear", self.clear_all)
        self.refresh()

    def notifications(self):
        current = run_json(["makoctl", "list", "-j"])
        history = run_json(["makoctl", "history", "-j"])
        return [("Current", item) for item in current] + [
            ("History", item) for item in history
        ]

    def refresh(self):
        notifications = self.notifications()
        if not notifications:
            self.set_content(self.empty_label("No notifications"))
            return

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        for source, item in notifications[:40]:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            card.get_style_context().add_class("notification-card")
            card.set_border_width(8)

            app = item.get("app_name") or "Notification"
            summary = item.get("summary") or ""
            heading = Gtk.Label()
            heading.set_xalign(0)
            heading.set_ellipsize(Pango.EllipsizeMode.END)
            heading.set_markup(
                f"<small>{html.escape(source)} · {html.escape(app)}</small>"
                f"\n<b>{html.escape(summary)}</b>"
            )
            card.pack_start(heading, False, False, 0)

            body = item.get("body") or ""
            if body:
                body_label = Gtk.Label(label=body)
                body_label.set_xalign(0)
                body_label.set_line_wrap(True)
                body_label.set_max_width_chars(58)
                body_label.set_lines(3)
                body_label.set_ellipsize(Pango.EllipsizeMode.END)
                card.pack_start(body_label, False, False, 0)
            content.pack_start(card, False, False, 0)
        self.set_content(content)

    def set_dnd(self, _switch, enabled):
        action = "-a" if enabled else "-r"
        run(["makoctl", "mode", action, "do-not-disturb"])
        return False

    def restore_latest(self, _button):
        run(["makoctl", "restore"])
        self.refresh()

    def clear_all(self):
        def worker():
            run(["makoctl", "dismiss", "--all", "--no-history"])
            for _ in range(50):
                history = run_json(["makoctl", "history", "-j"])
                if not history:
                    break
                history_ids = {item.get("id") for item in history}
                if run(["makoctl", "restore"]) is None:
                    break
                visible = run_json(["makoctl", "list", "-j"])
                restored = [
                    item.get("id") for item in visible if item.get("id") in history_ids
                ]
                if not restored:
                    break
                for notification_id in restored:
                    run(
                        [
                            "makoctl",
                            "dismiss",
                            "-n",
                            str(notification_id),
                            "--no-history",
                        ]
                    )
            GLib.idle_add(self.refresh)

        threading.Thread(target=worker, daemon=True).start()


def install_style():
    css = b"""
    window#desktop-panel {
        background-color: #101C2C;
        color: #EEF2F6;
        border: 2px solid #D6AE4A;
        border-radius: 8px;
    }
    label.title {
        font-weight: bold;
        font-size: 12pt;
    }
    label.muted {
        color: #A8B4C3;
    }
    button {
        color: #EEF2F6;
        background-color: #17283D;
        border: none;
        border-radius: 5px;
        padding: 5px 8px;
    }
    button:hover {
        background-color: #27374A;
    }
    button.destructive {
        color: #B94747;
    }
    button.history-row {
        padding: 7px 9px;
    }
    .notification-card {
        background-color: #17283D;
        border-radius: 6px;
    }
    switch:checked {
        background-color: #D6AE4A;
    }
    scrollbar slider {
        min-width: 5px;
        border-radius: 3px;
        background-color: #7D8A9B;
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
    arguments = sys.argv[1:]
    if arguments == ["notifications", "--status"]:
        notification_status()
        return 0
    if len(arguments) != 1 or arguments[0] not in {"clipboard", "notifications"}:
        print(f"usage: {sys.argv[0]} clipboard|notifications [--status]", file=sys.stderr)
        return 2

    install_style()
    panel = ClipboardPanel() if arguments[0] == "clipboard" else NotificationPanel()
    panel.connect("destroy", Gtk.main_quit)
    panel.show_all()
    Gtk.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
