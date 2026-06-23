"""Settings-focused business operations."""

from __future__ import annotations

from models.project import Project


class SettingsService:
    """Applies and mutates project settings independent from UI widgets."""

    def set_snap_enabled(self, project: Project, enabled: bool) -> None:
        """Persist snap toggle in project settings."""
        project.settings.snap_enabled = enabled

    def set_grid_enabled(self, project: Project, enabled: bool) -> None:
        """Persist grid visibility in project settings."""
        project.settings.grid_enabled = enabled

    def set_dimensions_enabled(self, project: Project, enabled: bool) -> None:
        """Persist dimensions visibility in project settings."""
        project.settings.show_dimensions = enabled
