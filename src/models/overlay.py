"""Overlay domain model for floor projections."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Overlay:
    """Represents a projected overlay of another floor for reference.

    Attributes:
        id: Unique identifier for this overlay.
        active_floor_id: ID of the floor where this overlay is displayed.
        source_floor_id: ID of the floor being projected as overlay.
        visible: Whether overlay is currently shown.
        snap_enabled: Whether overlay participates in snapping.
        opacity: Opacity level 0.0-1.0 for overlay rendering.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    active_floor_id: str = ""
    source_floor_id: str = ""
    visible: bool = True
    snap_enabled: bool = True
    opacity: float = 0.3

    def to_dict(self) -> dict[str, object]:
        """Serialize overlay to dictionary."""
        return {
            "id": self.id,
            "active_floor_id": self.active_floor_id,
            "source_floor_id": self.source_floor_id,
            "visible": self.visible,
            "snap_enabled": self.snap_enabled,
            "opacity": self.opacity,
        }

    @staticmethod
    def from_dict(data: dict[str, object]) -> Overlay:
        """Deserialize overlay from dictionary."""
        opacity_raw = data.get("opacity", 0.3)

        return Overlay(
            id=str(data.get("id", str(uuid4()))),
            active_floor_id=str(data.get("active_floor_id", "")),
            source_floor_id=str(data.get("source_floor_id", "")),
            visible=bool(data.get("visible", True)),
            snap_enabled=bool(data.get("snap_enabled", True)),
            opacity=(
                max(0.0, min(1.0, float(opacity_raw)))
                if isinstance(opacity_raw, (int, float, str))
                else 0.3
            ),
        )
