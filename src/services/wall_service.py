"""Business operations for wall domain objects."""

from __future__ import annotations

from geometry.point import Point
from models.wall import Wall, WallType


class WallService:
    """Factory and mutation helpers for validated wall creation."""

    def create_wall(
        self,
        start: Point,
        end: Point,
        thickness: float,
        wall_type: WallType,
    ) -> Wall:
        """Create and validate a wall domain object."""
        wall = Wall(start=start, end=end, thickness=thickness, wall_type=wall_type)
        wall.validate()
        return wall
