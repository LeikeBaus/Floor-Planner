"""CSV exporter for floor summary, room details, and architectural elements."""

from __future__ import annotations

import csv
from pathlib import Path

from models.floor import Floor


class FloorCsvExporter:
    """Export floor and room data to CSV tabular format."""

    def export(self, floor: Floor, output_path: Path) -> None:
        """Generate CSV report with floor summary, rooms, and walls data."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        with target.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            # Summary section
            writer.writerow(["FLOOR SUMMARY"])
            writer.writerow(["Floor Name", floor.name])
            writer.writerow(["Elevation (mm)", str(floor.elevation)])
            floor_area_m2 = floor.floor_area_total / 1_000_000.0
            writer.writerow(["Floor Area Total (m²)", f"{floor_area_m2:.2f}"])
            living_area_m2 = floor.living_area_total / 1_000_000.0
            writer.writerow(["Living Area Total (m²)", f"{living_area_m2:.2f}"])
            writer.writerow(["Room Count", str(len(floor.rooms))])
            writer.writerow(["Wall Count", str(len(floor.walls))])
            writer.writerow(["Window Count", str(len(floor.windows))])
            writer.writerow(["Door Count", str(len(floor.doors))])
            writer.writerow([])

            # Rooms section
            writer.writerow(["ROOMS"])
            writer.writerow(
                [
                    "Room Name",
                    "Floor Area (m²)",
                    "Living Area (m²)",
                    "Color",
                    "Point Count",
                ]
            )
            for room in floor.rooms:
                room_floor_area_m2 = room.floor_area / 1_000_000.0
                room_living_area_m2 = room.living_area / 1_000_000.0
                point_count = len(room.polygon)
                writer.writerow(
                    [
                        room.name,
                        f"{room_floor_area_m2:.2f}",
                        f"{room_living_area_m2:.2f}",
                        room.color,
                        point_count,
                    ]
                )
            writer.writerow([])

            # Walls section
            writer.writerow(["WALLS"])
            wall_headers = [
                "Wall ID",
                "Start X (mm)",
                "Start Y (mm)",
                "End X (mm)",
                "End Y (mm)",
                "Length (m)",
                "Type",
            ]
            writer.writerow(wall_headers)
            for wall in floor.walls:
                start_x = wall.start.x
                start_y = wall.start.y
                end_x = wall.end.x
                end_y = wall.end.y
                length_m = wall.length / 1000.0
                wall_type = wall.wall_type
                writer.writerow(
                    [
                        wall.id[:8],
                        start_x,
                        start_y,
                        end_x,
                        end_y,
                        f"{length_m:.2f}",
                        wall_type,
                    ]
                )
            writer.writerow([])

            # Windows section
            if floor.windows:
                writer.writerow(["WINDOWS"])
                window_headers = [
                    "Window ID",
                    "Wall ID",
                    "Position (mm)",
                    "Width (mm)",
                    "Height (mm)",
                ]
                writer.writerow(window_headers)
                for window in floor.windows:
                    writer.writerow(
                        [
                            window.id[:8],
                            window.wall_id[:8],
                            f"{window.position:.0f}",
                            f"{window.width:.0f}",
                            f"{window.height:.0f}",
                        ]
                    )
                writer.writerow([])

            # Doors section
            if floor.doors:
                writer.writerow(["DOORS"])
                door_headers = [
                    "Door ID",
                    "Wall ID",
                    "Position (mm)",
                    "Width (mm)",
                    "Swing Direction",
                ]
                writer.writerow(door_headers)
                for door in floor.doors:
                    writer.writerow(
                        [
                            door.id[:8],
                            door.wall_id[:8],
                            f"{door.position:.0f}",
                            f"{door.width:.0f}",
                            door.swing_direction,
                        ]
                    )
                writer.writerow([])

            # Openings section
            if floor.openings:
                writer.writerow(["OPENINGS"])
                opening_headers = [
                    "Opening ID",
                    "Wall ID",
                    "Position (mm)",
                    "Width (mm)",
                ]
                writer.writerow(opening_headers)
                for opening in floor.openings:
                    writer.writerow(
                        [
                            opening.id[:8],
                            opening.wall_id[:8],
                            f"{opening.position:.0f}",
                            f"{opening.width:.0f}",
                        ]
                    )
                writer.writerow([])

            # Stairs section
            if floor.stairs:
                writer.writerow(["STAIRS"])
                stair_headers = [
                    "Stair ID",
                    "Position X (mm)",
                    "Position Y (mm)",
                    "Width (mm)",
                    "Depth (mm)",
                ]
                writer.writerow(stair_headers)
                for stair in floor.stairs:
                    writer.writerow(
                        [
                            stair.id[:8],
                            f"{stair.position_x:.0f}",
                            f"{stair.position_y:.0f}",
                            f"{stair.width:.0f}",
                            f"{stair.depth:.0f}",
                        ]
                    )
