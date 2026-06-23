"""Snapshot model for capturing design states with timestamps and notes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from models.floor import Floor


@dataclass(slots=True)
class FloorSnapshot:
    """Captures a floor state at a specific point in time with optional revision notes."""

    floor: Floor
    timestamp: float
    notes: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict[str, object]:
        """Serialize snapshot to JSON-compatible dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "notes": self.notes,
            "floor": self.floor.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> FloorSnapshot:
        """Deserialize snapshot from JSON-compatible dictionary."""
        from models.floor import Floor

        floor_raw = data.get("floor", {})
        floor = Floor.from_dict(floor_raw) if isinstance(floor_raw, dict) else Floor()

        timestamp_raw = data.get("timestamp", datetime.now().timestamp())
        timestamp = (
            float(timestamp_raw)
            if isinstance(timestamp_raw, (int, float, str))
            else datetime.now().timestamp()
        )

        return cls(
            id=str(data.get("id", str(uuid4()))),
            floor=floor,
            timestamp=timestamp,
            notes=str(data.get("notes", "")),
        )

    @property
    def display_timestamp(self) -> str:
        """Return human-readable timestamp."""
        dt = datetime.fromtimestamp(self.timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
