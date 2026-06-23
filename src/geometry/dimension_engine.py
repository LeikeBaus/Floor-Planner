"""Auto-generation of wall length dimensions."""

from __future__ import annotations

from geometry.point import Point
from models.dimension import Dimension
from models.wall import Wall


class DimensionEngine:
    """Generates automatic dimensions from wall geometry."""

    def generate_wall_dimensions(
        self,
        walls: list[Wall],
        visible: bool,
        opacity: float,
        offset_mm: float = 350.0,
        offset_by_wall_id: dict[str, float] | None = None,
    ) -> list[Dimension]:
        """Create one parallel offset dimension per wall segment."""
        dimensions: list[Dimension] = []
        offsets = offset_by_wall_id or {}
        for wall in walls:
            if wall.length <= 0:
                continue

            dx = wall.end.x - wall.start.x
            dy = wall.end.y - wall.start.y
            inv_length = 1.0 / wall.length

            # Left normal of wall direction for offset dimension line.
            nx = -dy * inv_length
            ny = dx * inv_length

            offset = offsets.get(wall.id, offset_mm)
            display_start = Point(wall.start.x + nx * offset, wall.start.y + ny * offset)
            display_end = Point(wall.end.x + nx * offset, wall.end.y + ny * offset)

            dimensions.append(
                Dimension(
                    start=wall.start,
                    end=wall.end,
                    value=wall.length,
                    display_start=display_start,
                    display_end=display_end,
                    is_manual=False,
                    wall_id=wall.id,
                    visible=visible,
                    opacity=opacity,
                )
            )

        return dimensions
