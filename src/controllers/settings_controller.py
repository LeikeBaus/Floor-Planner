"""Controller for settings mutation and orchestration."""

from __future__ import annotations

from models.project import Project
from services.settings_service import SettingsService


class SettingsController:
    """Coordinates settings changes from the view layer."""

    def __init__(self, service: SettingsService) -> None:
        self._service = service

    def toggle_snap(self, project: Project, enabled: bool) -> None:
        """Update snap setting."""
        self._service.set_snap_enabled(project, enabled)

    def toggle_grid(self, project: Project, enabled: bool) -> None:
        """Update grid setting."""
        self._service.set_grid_enabled(project, enabled)

    def toggle_dimensions(self, project: Project, enabled: bool) -> None:
        """Update dimensions visibility setting."""
        self._service.set_dimensions_enabled(project, enabled)

    # --- View action handlers -------------------------------------------------------------

    def handle_toggle_grid_action(self, window: object, enabled: bool) -> None:
        """Handle QAction trigger for grid visibility."""
        handler = getattr(window, "_toggle_grid", None)
        if callable(handler):
            handler(enabled)

    def handle_toggle_snap_action(self, window: object, enabled: bool) -> None:
        """Handle QAction trigger for snap toggle."""
        handler = getattr(window, "_toggle_snap", None)
        if callable(handler):
            handler(enabled)

    def handle_toggle_dimensions_action(self, window: object, enabled: bool) -> None:
        """Handle QAction trigger for dimensions visibility."""
        handler = getattr(window, "_toggle_dimensions", None)
        if callable(handler):
            handler(enabled)

    def handle_toggle_height_zones_action(self, window: object, enabled: bool) -> None:
        """Handle QAction trigger for height-zone visibility."""
        handler = getattr(window, "_toggle_height_zones", None)
        if callable(handler):
            handler(enabled)

    def handle_open_settings_action(self, window: object) -> None:
        """Handle QAction trigger for settings dialog."""
        handler = getattr(window, "_open_settings_dialog", None)
        if callable(handler):
            handler()
