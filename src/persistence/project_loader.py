"""Project deserialization and load service."""

from __future__ import annotations

import json
from pathlib import Path

from models.project import Project
from persistence.migration_manager import MigrationManager


class ProjectLoader:
    """Reads and validates .fplan files from disk."""

    def __init__(self, migration_manager: MigrationManager | None = None) -> None:
        self._migration_manager = migration_manager or MigrationManager()

    def load(self, path: str | Path) -> Project:
        """Load project from path and return a Project instance."""
        source = Path(path)
        with source.open("r", encoding="utf-8") as file_handle:
            raw_payload = json.load(file_handle)

        if not isinstance(raw_payload, dict):
            raise ValueError("Invalid project file: root payload must be an object")

        migrated = self._migration_manager.migrate(raw_payload)
        return Project.from_dict(migrated)
