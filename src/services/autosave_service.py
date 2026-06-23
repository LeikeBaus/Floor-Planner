"""Autosave service for periodic project persistence."""

from __future__ import annotations

import tempfile
from pathlib import Path

from PyQt6.QtCore import QTimer

from models.project import Project
from persistence.project_saver import ProjectSaver


class AutosaveService:
    """Persist project snapshots periodically to a recovery file."""

    def __init__(
        self,
        project_saver: ProjectSaver,
        autosave_directory: Path | None = None,
    ) -> None:
        self._project_saver = project_saver
        self._autosave_directory = (
            autosave_directory
            if autosave_directory is not None
            else Path(tempfile.gettempdir()) / "floorplanner" / "autosaves"
        )
        self._project: Project | None = None
        self._project_file_path: Path | None = None
        self._last_autosave_path: Path | None = None

        self._timer = QTimer()
        self._timer.setSingleShot(False)
        self._timer.timeout.connect(self._on_timeout)

    def set_project(self, project: Project, project_file_path: Path | None) -> None:
        """Update currently tracked project and source path."""
        self._project = project
        self._project_file_path = project_file_path

    def start(self, interval_seconds: int) -> None:
        """Start autosave timer; zero or negative disables autosave."""
        if interval_seconds <= 0:
            self.stop()
            return

        interval_ms = interval_seconds * 1000
        self._timer.start(interval_ms)

    def stop(self) -> None:
        """Stop autosave timer."""
        self._timer.stop()

    def is_running(self) -> bool:
        """Return whether autosave timer is active."""
        return self._timer.isActive()

    def current_interval_ms(self) -> int:
        """Return active timer interval in milliseconds."""
        return self._timer.interval()

    def perform_autosave(self) -> Path | None:
        """Run one autosave cycle and return written file path, if any."""
        if self._project is None:
            return None

        autosave_path = self._build_autosave_path()
        try:
            self._project_saver.save(self._project, autosave_path)
        except OSError:
            return None

        self._last_autosave_path = autosave_path
        return autosave_path

    def get_last_autosave_path(self) -> Path | None:
        """Return last successful autosave file path."""
        return self._last_autosave_path

    def clear_autosave_file(self) -> None:
        """Delete current autosave file if it exists."""
        autosave_path = self._last_autosave_path
        if autosave_path is None:
            return
        if autosave_path.exists():
            autosave_path.unlink()
        self._last_autosave_path = None

    def _on_timeout(self) -> None:
        """Timer callback for periodic autosave."""
        self.perform_autosave()

    def _build_autosave_path(self) -> Path:
        """Build deterministic autosave file path for current project."""
        self._autosave_directory.mkdir(parents=True, exist_ok=True)

        if self._project_file_path is not None:
            base_name = self._project_file_path.stem
            suffix = self._project_file_path.suffix or ".fplan"
            file_name = f"{base_name}.autosave{suffix}"
        else:
            project = self._project
            if project is None:
                file_name = "untitled.autosave.fplan"
            else:
                file_name = f"untitled_{project.id}.autosave.fplan"

        return self._autosave_directory / file_name
