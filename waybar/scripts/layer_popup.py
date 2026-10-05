"""Shared click-outside behavior for GTK layer-shell panels."""

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gdk, Gtk, GtkLayerShell


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
