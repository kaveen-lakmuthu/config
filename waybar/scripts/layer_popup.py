"""Shared click-outside behavior for GTK layer-shell panels."""

import json
import os

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gdk, Gtk, GtkLayerShell


SETTINGS_PATH = os.path.expanduser(
    "~/.config/river-control-center/generated/panel-settings.json"
)
THEME_PATH = os.path.expanduser(
    "~/.config/river-control-center/generated/panel-theme.css"
)


def install_generated_theme():
    """Apply the optional shared panel theme after each panel's base CSS."""

    if not os.path.isfile(THEME_PATH):
        return
    provider = Gtk.CssProvider()
    try:
        provider.load_from_path(THEME_PATH)
    except Exception as error:  # GTK reports CSS parser failures as GLib errors.
        print(f"Could not load generated panel theme: {error}")
        return
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1,
    )


def panel_settings():
    """Return generated panel settings, falling back safely if unavailable."""

    defaults = {
        "clipboardHistoryLimit": 40,
        "notificationHistoryLimit": 25,
        "width": 430,
        "height": 420,
        "padding": 16,
        "topMargin": 4,
        "rightMargin": 6,
    }
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as settings_file:
            loaded = json.load(settings_file)
    except (OSError, json.JSONDecodeError):
        return defaults
    if not isinstance(loaded, dict):
        return defaults
    return {**defaults, **loaded}


def panel_setting(name, default=None):
    return panel_settings().get(name, default)


def _is_inside(widget, content):
    while widget is not None:
        if widget is content:
            return True
        widget = widget.get_parent()
    return False


def configure_layer_popup(
    window,
    content,
    namespace,
    *,
    top=4,
    right=6,
    preserve_view_focus=False,
):
    """Place content at top-right over a transparent click-dismiss backdrop."""

    settings = panel_settings()
    top = settings.get("topMargin", top)
    right = settings.get("rightMargin", right)

    screen = window.get_screen()
    visual = screen.get_rgba_visual() if screen is not None else None
    if visual is not None:
        window.set_visual(visual)
    window.set_app_paintable(True)

    GtkLayerShell.init_for_window(window)
    GtkLayerShell.set_namespace(window, namespace)
    GtkLayerShell.set_layer(window, GtkLayerShell.Layer.OVERLAY)
    for edge in (
        GtkLayerShell.Edge.TOP,
        GtkLayerShell.Edge.RIGHT,
        GtkLayerShell.Edge.BOTTOM,
        GtkLayerShell.Edge.LEFT,
    ):
        GtkLayerShell.set_anchor(window, edge, True)
    keyboard_mode = (
        GtkLayerShell.KeyboardMode.NONE
        if preserve_view_focus
        else GtkLayerShell.KeyboardMode.ON_DEMAND
    )
    GtkLayerShell.set_keyboard_mode(window, keyboard_mode)

    content.set_name(f"{namespace}-card")

    alignment = Gtk.Alignment.new(1.0, 0.0, 0.0, 0.0)
    alignment.set_padding(top, 0, 0, right)
    alignment.add(content)

    backdrop = Gtk.EventBox()
    backdrop.set_visible_window(False)
    backdrop.set_events(Gdk.EventMask.BUTTON_PRESS_MASK)
    backdrop.add(alignment)

    def dismiss_outside(_backdrop, event):
        target = Gtk.get_event_widget(event)
        if not _is_inside(target, content):
            window.close()
            return True
        return False

    backdrop.connect("button-press-event", dismiss_outside)
    window.add(backdrop)
    install_generated_theme()
