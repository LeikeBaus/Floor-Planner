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
