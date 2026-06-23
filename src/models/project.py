"""Root project model and serialization helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from models.building import Building
from models.floor_snapshot import FloorSnapshot
from models.project_settings import ProjectSettings


@dataclass(slots=True)
class Project:
    """Root object representing a complete planning project."""

    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "Untitled Project"
    client_name: str = ""
    project_address: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    modified_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    settings: ProjectSettings = field(default_factory=ProjectSettings)
    buildings: list[Building] = field(default_factory=list)
    snapshots: list[FloorSnapshot] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Serialize project to schema-aligned dictionary."""
        return {
            "file_version": 1,
            "project": {
                "id": self.id,
                "name": self.name,
                "client_name": self.client_name,
                "project_address": self.project_address,
                "description": self.description,
                "created_at": self.created_at.isoformat(),
                "modified_at": self.modified_at.isoformat(),
            },
            "settings": self.settings.to_dict(),
            "buildings": [building.to_dict() for building in self.buildings],
            "snapshots": [snapshot.to_dict() for snapshot in self.snapshots],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Project:
        """Create project from persisted dictionary payload."""
        project_data = data.get("project", {})
        settings_data = data.get("settings", {})
        building_data = data.get("buildings", [])
        snapshot_data = data.get("snapshots", [])

        project_payload = project_data if isinstance(project_data, dict) else {}
        settings_payload = settings_data if isinstance(settings_data, dict) else {}
        buildings: list[Building] = []
        if isinstance(building_data, list):
            buildings = [
                Building.from_dict(item)
                for item in building_data
                if isinstance(item, dict)
            ]

        snapshots: list[FloorSnapshot] = []
        if isinstance(snapshot_data, list):
            snapshots = [
                FloorSnapshot.from_dict(item)
                for item in snapshot_data
                if isinstance(item, dict)
            ]

        created_at = _parse_datetime(project_payload.get("created_at"))
        modified_at = _parse_datetime(project_payload.get("modified_at"))

        return cls(
            id=str(project_payload.get("id", str(uuid4()))),
            name=str(project_payload.get("name", "Untitled Project")),
            client_name=str(project_payload.get("client_name", "")),
            project_address=str(project_payload.get("project_address", "")),
            description=str(project_payload.get("description", "")),
            created_at=created_at,
            modified_at=modified_at,
            settings=ProjectSettings.from_dict(settings_payload),
            buildings=buildings,
            snapshots=snapshots,
        )


def _parse_datetime(value: object) -> datetime:
    """Parse persisted datetime values with UTC fallback."""
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return datetime.now(UTC)
    return datetime.now(UTC)
