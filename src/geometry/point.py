"""Immutable point value object."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Point:
    """Cartesian coordinate in millimeters."""

    x: float
    y: float

    def to_dict(self) -> dict[str, float]:
        """Serialize this point to JSON-compatible dictionary."""
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> Point:
        """Create point from JSON-compatible dictionary."""
        return cls(x=float(data["x"]), y=float(data["y"]))
