"""SVG exporter for floor geometry and architectural elements."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Sequence
from math import hypot
from pathlib import Path

from models.floor import Floor
from models.wall import Wall


class FloorSvgExporter:
    """Export floor geometry to an SVG document."""

    _MM_TO_PX = 0.05
    _PADDING_MM = 1000.0

    def export(self, floor: Floor, output_path: Path) -> None:
        """Generate an SVG drawing of rooms, walls, and element markers."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        min_x, min_y, width_mm, height_mm = self._compute_viewport(floor)
        width_px = width_mm * self._MM_TO_PX
        height_px = height_mm * self._MM_TO_PX

        root = ET.Element(
            "svg",
            {
                "xmlns": "http://www.w3.org/2000/svg",
                "version": "1.1",
                "width": f"{width_px:.1f}",
                "height": f"{height_px:.1f}",
                "viewBox": f"0 0 {width_px:.1f} {height_px:.1f}",
            },
        )

        ET.SubElement(
            root,
            "rect",
            {
                "x": "0",
                "y": "0",
                "width": "100%",
                "height": "100%",
                "fill": "#ffffff",
            },
        )

        rooms_group = ET.SubElement(root, "g", {"id": "rooms"})
        walls_group = ET.SubElement(root, "g", {"id": "walls"})
        openings_group = ET.SubElement(root, "g", {"id": "openings"})
        stairs_group = ET.SubElement(root, "g", {"id": "stairs"})
        labels_group = ET.SubElement(root, "g", {"id": "labels"})

        self._render_rooms(rooms_group, floor, min_x, min_y)
        self._render_walls(walls_group, floor, min_x, min_y)
        self._render_openings(openings_group, floor, min_x, min_y)
        self._render_stairs(stairs_group, floor, min_x, min_y)

        ET.SubElement(
            labels_group,
            "text",
            {
                "x": "12",
                "y": "24",
                "font-size": "14",
                "font-family": "Arial, sans-serif",
                "fill": "#333333",
            },
        ).text = f"Floor: {floor.name}"

        tree = ET.ElementTree(root)
        tree.write(target, encoding="utf-8", xml_declaration=True)

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
            return -self._PADDING_MM, -self._PADDING_MM, 2 * self._PADDING_MM, 2 * self._PADDING_MM

        min_x = min(xs) - self._PADDING_MM
        max_x = max(xs) + self._PADDING_MM
        min_y = min(ys) - self._PADDING_MM
        max_y = max(ys) + self._PADDING_MM

        width_mm = max(100.0, max_x - min_x)
        height_mm = max(100.0, max_y - min_y)
        return min_x, min_y, width_mm, height_mm

    def _render_rooms(self, group: ET.Element, floor: Floor, min_x: float, min_y: float) -> None:
        for room in floor.rooms:
            if not room.polygon:
                continue
            points_attr = " ".join(
                f"{self._to_px(point.x - min_x):.2f},{self._to_px(point.y - min_y):.2f}"
                for point in room.polygon
            )
            ET.SubElement(
                group,
                "polygon",
                {
                    "points": points_attr,
                    "fill": room.color,
                    "fill-opacity": "0.25",
                    "stroke": "#6b7280",
                    "stroke-width": "1",
                },
            )

    def _render_walls(self, group: ET.Element, floor: Floor, min_x: float, min_y: float) -> None:
        for wall in floor.walls:
            stroke_color = "#1f2937" if str(wall.wall_type) == "EXTERIOR" else "#4b5563"
            stroke_width = max(1.0, self._to_px(wall.thickness))
            ET.SubElement(
                group,
                "line",
                {
                    "x1": f"{self._to_px(wall.start.x - min_x):.2f}",
                    "y1": f"{self._to_px(wall.start.y - min_y):.2f}",
                    "x2": f"{self._to_px(wall.end.x - min_x):.2f}",
                    "y2": f"{self._to_px(wall.end.y - min_y):.2f}",
                    "stroke": stroke_color,
                    "stroke-width": f"{stroke_width:.2f}",
                    "stroke-linecap": "round",
                },
            )

    def _render_openings(self, group: ET.Element, floor: Floor, min_x: float, min_y: float) -> None:
        wall_lookup = {wall.id: wall for wall in floor.walls}
        self._render_linear_elements(
            group,
            floor.windows,
            wall_lookup,
            min_x,
            min_y,
            color="#0ea5e9",
            css_class="window",
        )
        self._render_linear_elements(
            group,
            floor.doors,
            wall_lookup,
            min_x,
            min_y,
            color="#f59e0b",
            css_class="door",
        )
        self._render_linear_elements(
            group,
            floor.openings,
            wall_lookup,
            min_x,
            min_y,
            color="#10b981",
            css_class="opening",
        )

    def _render_linear_elements(
        self,
        group: ET.Element,
        elements: Sequence[object],
        wall_lookup: dict[str, Wall],
        min_x: float,
        min_y: float,
        color: str,
        css_class: str,
    ) -> None:
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

            ET.SubElement(
                group,
                "line",
                {
                    "class": css_class,
                    "x1": f"{self._to_px(start_x - min_x):.2f}",
                    "y1": f"{self._to_px(start_y - min_y):.2f}",
                    "x2": f"{self._to_px(end_x - min_x):.2f}",
                    "y2": f"{self._to_px(end_y - min_y):.2f}",
                    "stroke": color,
                    "stroke-width": "3",
                    "stroke-linecap": "round",
                },
            )

    def _render_stairs(self, group: ET.Element, floor: Floor, min_x: float, min_y: float) -> None:
        for stair in floor.stairs:
            ET.SubElement(
                group,
                "rect",
                {
                    "x": f"{self._to_px(stair.position_x - min_x):.2f}",
                    "y": f"{self._to_px(stair.position_y - min_y):.2f}",
                    "width": f"{self._to_px(stair.width):.2f}",
                    "height": f"{self._to_px(stair.depth):.2f}",
                    "fill": "#e5e7eb",
                    "stroke": "#374151",
                    "stroke-width": "1.5",
                },
            )

    def _to_px(self, value_mm: float) -> float:
        return value_mm * self._MM_TO_PX
