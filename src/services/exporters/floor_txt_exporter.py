"""TXT exporter for floor data in plain text tabular format."""

from __future__ import annotations

from pathlib import Path
from typing import TextIO

from models.floor import Floor


class FloorTxtExporter:
    """Export floor and room data to plain text tabular format."""

    def export(self, floor: Floor, output_path: Path) -> None:
        """Generate TXT report with floor summary, rooms, and walls data."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        with target.open("w", encoding="utf-8") as txtfile:
            self._write_summary_section(txtfile, floor)
            self._write_rooms_section(txtfile, floor)
            self._write_walls_section(txtfile, floor)
            self._write_windows_section(txtfile, floor)
            self._write_doors_section(txtfile, floor)
            self._write_openings_section(txtfile, floor)
            self._write_stairs_section(txtfile, floor)

    def _write_summary_section(self, txtfile: TextIO, floor: Floor) -> None:
        """Write floor summary section."""
        txtfile.write("=" * 80 + "\n")
        txtfile.write("FLOOR SUMMARY\n")
        txtfile.write("=" * 80 + "\n")

        summary_lines = [
            f"Floor Name:              {floor.name}",
            f"Elevation (mm):          {floor.elevation:.1f}",
            f"Floor Area Total (m²):   {floor.floor_area_total / 1_000_000.0:.2f}",
            f"Living Area Total (m²):  {floor.living_area_total / 1_000_000.0:.2f}",
            f"Room Count:              {len(floor.rooms)}",
            f"Wall Count:              {len(floor.walls)}",
            f"Window Count:            {len(floor.windows)}",
            f"Door Count:              {len(floor.doors)}",
            f"Opening Count:           {len(floor.openings)}",
            f"Stair Count:             {len(floor.stairs)}",
        ]

        for line in summary_lines:
            txtfile.write(line + "\n")

        txtfile.write("\n")

    def _write_rooms_section(self, txtfile: TextIO, floor: Floor) -> None:
        """Write rooms section."""
        if not floor.rooms:
            return

        txtfile.write("=" * 80 + "\n")
        txtfile.write("ROOMS\n")
        txtfile.write("=" * 80 + "\n")

        header = (
            "Room Name".ljust(25)
            + "Floor Area (m²)".ljust(20)
            + "Living Area (m²)".ljust(20)
            + "Color".ljust(10)
            + "Points\n"
        )
        txtfile.write(header)
        txtfile.write("-" * 80 + "\n")

        for room in floor.rooms:
            room_floor_area_m2 = room.floor_area / 1_000_000.0
            room_living_area_m2 = room.living_area / 1_000_000.0
            point_count = len(room.polygon)

            row = (
                room.name.ljust(25)
                + f"{room_floor_area_m2:.2f}".ljust(20)
                + f"{room_living_area_m2:.2f}".ljust(20)
                + room.color.ljust(10)
                + str(point_count) + "\n"
            )
            txtfile.write(row)

        txtfile.write("\n")

    def _write_walls_section(self, txtfile: TextIO, floor: Floor) -> None:
        """Write walls section."""
        if not floor.walls:
            return

        txtfile.write("=" * 80 + "\n")
        txtfile.write("WALLS\n")
        txtfile.write("=" * 80 + "\n")

        header = (
            "Wall ID".ljust(12)
            + "Start X (mm)".ljust(15)
            + "Start Y (mm)".ljust(15)
            + "End X (mm)".ljust(15)
            + "End Y (mm)".ljust(15)
            + "Length (m)".ljust(15)
            + "Type\n"
        )
        txtfile.write(header)
        txtfile.write("-" * 80 + "\n")

        for wall in floor.walls:
            length_m = wall.length / 1000.0

            row = (
                wall.id[:8].ljust(12)
                + f"{wall.start.x:.0f}".ljust(15)
                + f"{wall.start.y:.0f}".ljust(15)
                + f"{wall.end.x:.0f}".ljust(15)
                + f"{wall.end.y:.0f}".ljust(15)
                + f"{length_m:.2f}".ljust(15)
                + str(wall.wall_type) + "\n"
            )
            txtfile.write(row)

        txtfile.write("\n")

    def _write_windows_section(self, txtfile: TextIO, floor: Floor) -> None:
        """Write windows section."""
        if not floor.windows:
            return

        txtfile.write("=" * 80 + "\n")
        txtfile.write("WINDOWS\n")
        txtfile.write("=" * 80 + "\n")

        header = (
            "Window ID".ljust(12)
            + "Wall ID".ljust(12)
            + "Position (mm)".ljust(18)
            + "Width (mm)".ljust(15)
            + "Height (mm)\n"
        )
        txtfile.write(header)
        txtfile.write("-" * 80 + "\n")

        for window in floor.windows:
            row = (
                window.id[:8].ljust(12)
                + window.wall_id[:8].ljust(12)
                + f"{window.position:.0f}".ljust(18)
                + f"{window.width:.0f}".ljust(15)
                + f"{window.height:.0f}\n"
            )
            txtfile.write(row)

        txtfile.write("\n")

    def _write_doors_section(self, txtfile: TextIO, floor: Floor) -> None:
        """Write doors section."""
        if not floor.doors:
            return

        txtfile.write("=" * 80 + "\n")
        txtfile.write("DOORS\n")
        txtfile.write("=" * 80 + "\n")

        header = (
            "Door ID".ljust(12)
            + "Wall ID".ljust(12)
            + "Position (mm)".ljust(18)
            + "Width (mm)".ljust(15)
            + "Swing Direction\n"
        )
        txtfile.write(header)
        txtfile.write("-" * 80 + "\n")

        for door in floor.doors:
            row = (
                door.id[:8].ljust(12)
                + door.wall_id[:8].ljust(12)
                + f"{door.position:.0f}".ljust(18)
                + f"{door.width:.0f}".ljust(15)
                + door.swing_direction + "\n"
            )
            txtfile.write(row)

        txtfile.write("\n")

    def _write_openings_section(self, txtfile: TextIO, floor: Floor) -> None:
        """Write openings section."""
        if not floor.openings:
            return

        txtfile.write("=" * 80 + "\n")
        txtfile.write("OPENINGS\n")
        txtfile.write("=" * 80 + "\n")

        header = (
            "Opening ID".ljust(12)
            + "Wall ID".ljust(12)
            + "Position (mm)".ljust(18)
            + "Width (mm)\n"
        )
        txtfile.write(header)
        txtfile.write("-" * 80 + "\n")

        for opening in floor.openings:
            row = (
                opening.id[:8].ljust(12)
                + opening.wall_id[:8].ljust(12)
                + f"{opening.position:.0f}".ljust(18)
                + f"{opening.width:.0f}\n"
            )
            txtfile.write(row)

        txtfile.write("\n")

    def _write_stairs_section(self, txtfile: TextIO, floor: Floor) -> None:
        """Write stairs section."""
        if not floor.stairs:
            return

        txtfile.write("=" * 80 + "\n")
        txtfile.write("STAIRS\n")
        txtfile.write("=" * 80 + "\n")

        header = (
            "Stair ID".ljust(12)
            + "Position X (mm)".ljust(18)
            + "Position Y (mm)".ljust(18)
            + "Width (mm)".ljust(15)
            + "Depth (mm)".ljust(12)
            + "Type".ljust(12)
            + "Orientation (deg)\n"
        )
        txtfile.write(header)
        txtfile.write("-" * 80 + "\n")

        for stair in floor.stairs:
            row = (
                stair.id[:8].ljust(12)
                + f"{stair.position_x:.0f}".ljust(18)
                + f"{stair.position_y:.0f}".ljust(18)
                + f"{stair.width:.0f}".ljust(15)
                + f"{stair.depth:.0f}".ljust(12)
                + stair.stair_type.ljust(12)
                + f"{stair.orientation_degrees:.1f}\n"
            )
            txtfile.write(row)

        txtfile.write("\n")
