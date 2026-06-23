"""Crash recovery service for discovering and restoring autosaved projects."""

from __future__ import annotations

import tempfile
from pathlib import Path

from models.project import Project
from persistence.project_loader import ProjectLoader


class CrashRecoveryService:
    """Provide recovery file discovery, loading, and cleanup operations."""

    def __init__(
        self,
        project_loader: ProjectLoader,
        autosave_directory: Path | None = None,
    ) -> None:
        self._project_loader = project_loader
        self._autosave_directory = (
            autosave_directory
            if autosave_directory is not None
            else Path(tempfile.gettempdir()) / "floorplanner" / "autosaves"
        )

    def list_recovery_files(self) -> list[Path]:
        """Return autosave files sorted by most recently modified first."""
        autosave_dir = self._autosave_directory
        if not autosave_dir.exists():
            return []

        candidates = [
            item
            for item in autosave_dir.iterdir()
            if item.is_file() and ".autosave" in item.name and item.suffix in {".fplan", ".json"}
        ]

        return sorted(candidates, key=lambda path: path.stat().st_mtime, reverse=True)

    def load_recovery_project(self, recovery_path: Path) -> Project:
        """Load a recovery project file into a Project model."""
        return self._project_loader.load(recovery_path)

    def discard_recovery_file(self, recovery_path: Path) -> None:
        """Delete one recovery file if it exists."""
        if recovery_path.exists():
            recovery_path.unlink()

    def get_autosave_directory(self) -> Path:
        """Return filesystem location used for autosave recovery files."""
        return self._autosave_directory
