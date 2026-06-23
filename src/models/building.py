"""Building model representing an independent structure."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from models.floor import Floor


@dataclass(slots=True)
class Building:
    """A project building containing one or more floors."""

    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "Main Building"
    floors: list[Floor] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Serialize building to JSON-compatible dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "floors": [floor.to_dict() for floor in self.floors],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Building:
        """Create building from JSON-compatible dictionary."""
        floor_payload = data.get("floors", [])
        floors: list[Floor] = []
        if isinstance(floor_payload, list):
            floors = [Floor.from_dict(item) for item in floor_payload if isinstance(item, dict)]
        return cls(
            id=str(data.get("id", str(uuid4()))),
            name=str(data.get("name", "Main Building")),
            floors=floors,
        )
