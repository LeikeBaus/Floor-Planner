"""Controller for snap-related UI orchestration."""

from __future__ import annotations


class SnapController:
    """Coordinates snap state changes requested by the view layer."""

    def set_debug_mode(self, drawing_view: object | None, enabled: bool) -> None:
        """Toggle debug snap visualization on the drawing view."""
        if drawing_view is None:
            return
        set_debug = getattr(drawing_view, "set_debug_snap_enabled", None)
        if callable(set_debug):
            set_debug(enabled)

    def apply_snap_state(self, drawing_view: object | None, enabled: bool, distance_mm: float) -> None:
        """Apply snap enablement and distance to the drawing view."""
        if drawing_view is None:
            return
        set_snap_options = getattr(drawing_view, "set_snap_options", None)
        if callable(set_snap_options):
            set_snap_options(enabled=enabled, distance_mm=distance_mm)

    def handle_toggle_debug_snap_action(self, window: object, enabled: bool) -> None:
        """Handle QAction trigger for debug snap mode."""
        handler = getattr(window, "_toggle_debug_snap", None)
        if callable(handler):
            handler(enabled)
