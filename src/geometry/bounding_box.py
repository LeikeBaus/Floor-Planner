"""Axis-aligned bounding box value object."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """A rectangular world-space envelope used for filtering and visibility."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def contains(self, x: float, y: float) -> bool:
        """Return True if a world coordinate lies within this bounding box."""
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y
