"""Graphics item for displaying a door on a wall."""

from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsItemGroup,
    QGraphicsPathItem,
    QGraphicsRectItem,
)

from models.door import Door


class DoorGraphicsItem(QGraphicsItemGroup):
    """Visual representation of a door on a wall with swing arc."""

    def __init__(
        self,
        door: Door,
        start_point: QPointF,
        end_point: QPointF,
        wall_thickness: float,
    ) -> None:
        super().__init__()
        self.door_id = door.id
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

        self._path_item: QGraphicsPathItem | None = None
        self._rect_item: QGraphicsRectItem | None = None

        # Calculate door position and swing visualization
        wall_dx = end_point.x() - start_point.x()
        wall_dy = end_point.y() - start_point.y()
        wall_length = (wall_dx**2 + wall_dy**2) ** 0.5

        if wall_length > 1e-6:
            # Normalize wall direction
            wall_ux = wall_dx / wall_length
            wall_uy = wall_dy / wall_length
            perp_ux = -wall_uy
            perp_uy = wall_ux

            # Door center position along wall
            door_center_x = start_point.x() + wall_ux * door.position
            door_center_y = start_point.y() + wall_uy * door.position

            # Door rectangle aligned to wall and wall thickness.
            half_width = door.width / 2.0
            offset_dist = max(40.0, wall_thickness / 2.0)
            half_depth = offset_dist

            left_top = QPointF(
                door_center_x - wall_ux * half_width - perp_ux * offset_dist,
                door_center_y - wall_uy * half_width - perp_uy * offset_dist,
            )

            rect_item = QGraphicsRectItem(0.0, 0.0, door.width, half_depth * 2.0)
            rect_item.setPos(left_top)
            rect_item.setRotation(math.degrees(math.atan2(wall_uy, wall_ux)))

            rect_pen = QPen(QColor("#000000"))
            rect_pen.setWidthF(2.0)
            rect_pen.setCosmetic(True)
            rect_item.setPen(rect_pen)
            rect_item.setBrush(QColor("#BEADAD"))
            self.addToGroup(rect_item)
            self._rect_item = rect_item

            path = self._build_swing_path(
                swing_direction=door.swing_direction,
                width=door.width,
                depth=half_depth * 2.0,
                radius=door.width,
            )

            path_item = QGraphicsPathItem(path)
            path_item.setPos(left_top)
            path_item.setRotation(math.degrees(math.atan2(wall_uy, wall_ux)))
            pen = QPen(QColor("#000000"))
            pen.setWidthF(2.0)
            pen.setCosmetic(True)
            path_item.setPen(pen)
            #path_item.setBrush(QColor("#7A7C99"))
            self.addToGroup(path_item)
            self._path_item = path_item

        self.setZValue(11)

    def _build_swing_path(
        self,
        swing_direction: str,
        width: float,
        depth: float,
        radius: float,
    ) -> QPainterPath:
        """Build quarter-circle swing relative to the local door rectangle."""
        mapping: dict[str, tuple[float, float, float, float]] = {
            # (hinge_x, hinge_y, closed_angle_deg, open_angle_deg)
            "left_out": (0.0, depth, 0.0, -90.0),
            "right_out": (width, depth, 180.0, 270.0),
            "left_in": (0.0, 0, 0.0, 90.0),
            "right_in": (width, 0, 180.0, 90.0),
        }
        hinge_x, hinge_y, start_deg, end_deg = mapping.get(
            swing_direction,
            mapping["right_in"],
        )

        arc_rect = QRectF(
            hinge_x - radius,
            hinge_y - radius,
            radius * 2.0,
            radius * 2.0,
        )

        # Build a strictly local quarter-circle from closed to open position.
        span = end_deg - start_deg
        if span > 180.0:
            span -= 360.0
        elif span < -180.0:
            span += 360.0

        path = QPainterPath()

        # Arc
        path.arcMoveTo(arc_rect, start_deg)
        path.arcTo(arc_rect, start_deg, span)

        # Hinge line
        angle_rad = math.radians(end_deg)
        end_x = hinge_x + radius * math.cos(angle_rad)
        end_y = hinge_y - radius * math.sin(angle_rad)
        path.moveTo(hinge_x, hinge_y)
        path.lineTo(end_x, end_y)

        return path

    def itemChange(
        self,
        change: QGraphicsItem.GraphicsItemChange,
        value: object,
    ) -> object:
        """Update visual style when the door selection state changes."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            if self._path_item is not None:
                if value:
                    pen = QPen(QColor("#991B1B"))
                    pen.setWidthF(2.5)
                    rect_color = QColor("#991B1B")
                else:
                    pen = QPen(QColor("#DC2626"))
                    pen.setWidthF(2.0)
                    rect_color = QColor("#DC2626")
                pen.setCosmetic(True)
                self._path_item.setPen(pen)
                if self._rect_item is not None:
                    rect_pen = QPen(rect_color)
                    rect_pen.setWidthF(2.0)
                    rect_pen.setCosmetic(True)
                    self._rect_item.setPen(rect_pen)
        return super().itemChange(change, value)
