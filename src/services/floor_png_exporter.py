"""PNG exporter for floor geometry and architectural elements."""

from __future__ import annotations

from collections.abc import Sequence
from math import hypot
from pathlib import Path

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QImage, QPainter, QPainterPath, QPen

from models.floor import Floor
from models.wall import Wall


class FloorPngExporter:
    """Export floor geometry to a PNG image."""

    _MM_TO_PX = 0.05
    _PADDING_MM = 1000.0

    def export(self, floor: Floor, output_path: Path) -> None:
        """Generate a PNG drawing of rooms, walls, and element markers."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        min_x, min_y, width_mm, height_mm = self._compute_viewport(floor)
        width_px = max(100, int(round(width_mm * self._MM_TO_PX)))
        height_px = max(100, int(round(height_mm * self._MM_TO_PX)))

        image = QImage(width_px, height_px, QImage.Format.Format_ARGB32)
        image.fill(QColor("#ffffff"))

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, on=True)

        self._render_rooms(painter, floor, min_x, min_y)
        self._render_walls(painter, floor, min_x, min_y)
        self._render_openings(painter, floor, min_x, min_y)
        self._render_stairs(painter, floor, min_x, min_y)

        painter.setPen(QPen(QColor("#333333")))
        painter.drawText(12, 24, f"Floor: {floor.name}")
        painter.end()

        image.save(str(target), "PNG")

    def _compute_viewport(self, floor: Floor) -> tuple[float, float, float, float]:
        """Return viewport origin and size in millimeters."""
        xs: list[float] = []
        ys: list[float] = []

        for wall in floor.walls:
            xs.extend([wall.start.x, wall.end.x])
            ys.extend([wall.start.y, wall.end.y])

        for room in floor.rooms:
            for point in room.polygon:
                xs.append(point.x)
                ys.append(point.y)

        for stair in floor.stairs:
            xs.extend([stair.position_x, stair.position_x + stair.width])
            ys.extend([stair.position_y, stair.position_y + stair.depth])

        if not xs or not ys:
            return (
                -self._PADDING_MM,
                -self._PADDING_MM,
                2 * self._PADDING_MM,
                2 * self._PADDING_MM,
            )

        min_x = min(xs) - self._PADDING_MM
        max_x = max(xs) + self._PADDING_MM
        min_y = min(ys) - self._PADDING_MM
        max_y = max(ys) + self._PADDING_MM

        width_mm = max(100.0, max_x - min_x)
        height_mm = max(100.0, max_y - min_y)
        return min_x, min_y, width_mm, height_mm

    def _render_rooms(self, painter: QPainter, floor: Floor, min_x: float, min_y: float) -> None:
        for room in floor.rooms:
            if not room.polygon:
                continue

            path = QPainterPath()
            first = room.polygon[0]
            path.moveTo(self._to_px(first.x - min_x), self._to_px(first.y - min_y))
            for point in room.polygon[1:]:
                path.lineTo(self._to_px(point.x - min_x), self._to_px(point.y - min_y))
            path.closeSubpath()

            fill_color = QColor(room.color)
            fill_color.setAlpha(64)
            painter.fillPath(path, QBrush(fill_color))

            painter.setPen(QPen(QColor("#6b7280"), 1.0))
            painter.drawPath(path)

    def _render_walls(self, painter: QPainter, floor: Floor, min_x: float, min_y: float) -> None:
        for wall in floor.walls:
            color = QColor("#1f2937") if str(wall.wall_type) == "EXTERIOR" else QColor("#4b5563")
            thickness_px = max(1.0, self._to_px(wall.thickness))
            pen = QPen(color, thickness_px)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(
                QPointF(self._to_px(wall.start.x - min_x), self._to_px(wall.start.y - min_y)),
                QPointF(self._to_px(wall.end.x - min_x), self._to_px(wall.end.y - min_y)),
            )

    def _render_openings(self, painter: QPainter, floor: Floor, min_x: float, min_y: float) -> None:
        wall_lookup = {wall.id: wall for wall in floor.walls}
        self._render_linear_elements(
            painter,
            floor.windows,
            wall_lookup,
            min_x,
            min_y,
            color=QColor("#0ea5e9"),
        )
        self._render_linear_elements(
            painter,
            floor.doors,
            wall_lookup,
            min_x,
            min_y,
            color=QColor("#f59e0b"),
        )
        self._render_linear_elements(
            painter,
            floor.openings,
            wall_lookup,
            min_x,
            min_y,
            color=QColor("#10b981"),
        )

    def _render_linear_elements(
        self,
        painter: QPainter,
        elements: Sequence[object],
        wall_lookup: dict[str, Wall],
        min_x: float,
        min_y: float,
        color: QColor,
    ) -> None:
        pen = QPen(color, 3.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        for element in elements:
            wall_id_raw = getattr(element, "wall_id", "")
            if not isinstance(wall_id_raw, str):
                continue

            wall = wall_lookup.get(wall_id_raw)
            if wall is None:
                continue

            wall_dx = wall.end.x - wall.start.x
            wall_dy = wall.end.y - wall.start.y
            wall_len = hypot(wall_dx, wall_dy)
            if wall_len <= 0.0:
                continue

            position_raw = getattr(element, "position", 0.0)
            width_raw = getattr(element, "width", 0.0)
            if not isinstance(position_raw, (int, float)) or not isinstance(
                width_raw, (int, float)
            ):
                continue

            t = max(0.0, min(1.0, float(position_raw) / wall_len))
            center_x = wall.start.x + wall_dx * t
            center_y = wall.start.y + wall_dy * t

            ux = wall_dx / wall_len
            uy = wall_dy / wall_len
            half_width = max(50.0, float(width_raw) / 2.0)

            start_x = center_x - ux * half_width
            start_y = center_y - uy * half_width
            end_x = center_x + ux * half_width
            end_y = center_y + uy * half_width

            painter.drawLine(
                QPointF(self._to_px(start_x - min_x), self._to_px(start_y - min_y)),
                QPointF(self._to_px(end_x - min_x), self._to_px(end_y - min_y)),
            )

    def _render_stairs(self, painter: QPainter, floor: Floor, min_x: float, min_y: float) -> None:
        for stair in floor.stairs:
            painter.setPen(QPen(QColor("#374151"), 1.5))
            painter.setBrush(QBrush(QColor("#e5e7eb")))
            x_px = self._to_px(stair.position_x - min_x)
            y_px = self._to_px(stair.position_y - min_y)
            width_px = self._to_px(stair.width)
            depth_px = self._to_px(stair.depth)
            painter.drawRect(QRectF(x_px, y_px, width_px, depth_px))

    def _to_px(self, value_mm: float) -> float:
        return value_mm * self._MM_TO_PX
