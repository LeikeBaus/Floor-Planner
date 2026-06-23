"""Project serialization and save service."""

from __future__ import annotations

import json
from pathlib import Path

from models.project import Project


class ProjectSaver:
    """Writes project files to disk in .fplan JSON format."""

    def save(self, project: Project, path: str | Path) -> None:
        """Persist project to a target file path."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = project.to_dict()

        with target.open("w", encoding="utf-8") as file_handle:
            json.dump(payload, file_handle, ensure_ascii=False, indent=2)
