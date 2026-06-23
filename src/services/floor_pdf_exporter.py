"""Export floor summary to PDF with zones and area breakdown."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from models.floor import Floor
from models.height_zone import HeightZoneType


class FloorPdfExporter:
    """Export floor summary and statistics to PDF document."""

    def __init__(self) -> None:
        """Initialize exporter with default styles."""
        self._stylesheet = getSampleStyleSheet()

    def export(self, floor: Floor, output_path: Path) -> None:
        """Generate PDF report for floor with zones and area breakdown."""
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        story: list[object] = []

        title_style = ParagraphStyle(
            "CustomTitle",
            parent=self._stylesheet["Heading1"],
            fontSize=20,
            textColor=colors.HexColor("#1F2937"),
            spaceAfter=6,
        )
        story.append(Paragraph(f"Floor Summary: {floor.name}", title_style))

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        story.append(Paragraph(f"<i>Generated: {timestamp}</i>", self._stylesheet["Normal"]))
        story.append(Spacer(1, 0.2 * inch))

        floor_area_m2 = floor.floor_area_total / 1_000_000.0
        living_area_m2 = floor.living_area_total / 1_000_000.0
        total_data = [
            ["Metric", "Value"],
            ["Floor Area", f"{floor_area_m2:.2f} m²"],
            ["Living Area", f"{living_area_m2:.2f} m²"],
            ["Rooms", str(len(floor.rooms))],
            ["Walls", str(len(floor.walls))],
            ["Height Zones", str(len(floor.height_zones))],
        ]

        total_table = Table(total_data, colWidths=[2 * inch, 2 * inch])
        total_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F9FAFB")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#D1D5DB")),
                ]
            )
        )
        story.append(total_table)
        story.append(Spacer(1, 0.3 * inch))

        story.append(Paragraph("Zone Breakdown", self._stylesheet["Heading2"]))
        under_1m_count = sum(
            1 for zone in floor.height_zones if zone.zone_type == HeightZoneType.UNDER_1M
        )
        between_1m_2m_count = sum(
            1 for zone in floor.height_zones
            if zone.zone_type == HeightZoneType.BETWEEN_1M_AND_2M
        )
        above_2m_count = sum(
            1 for zone in floor.height_zones if zone.zone_type == HeightZoneType.ABOVE_2M
        )

        zone_data = [
            ["Zone Type", "Weight", "Count"],
            ["Under 1m", "0.0x", str(under_1m_count)],
            ["1m–2m", "0.5x", str(between_1m_2m_count)],
            ["Above 2m", "1.0x", str(above_2m_count)],
        ]

        zone_table = Table(zone_data, colWidths=[1.5 * inch, 1 * inch, 1 * inch])
        zone_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F9FAFB")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#D1D5DB")),
                ]
            )
        )
        story.append(zone_table)
        story.append(Spacer(1, 0.3 * inch))

        if floor.rooms:
            story.append(Paragraph("Room Details", self._stylesheet["Heading2"]))
            room_data = [["Room Name", "Floor Area", "Living Area"]]
            for room in floor.rooms:
                floor_area_room = room.floor_area / 1_000_000.0
                living_area_room = room.living_area / 1_000_000.0
                room_data.append(
                    [room.name, f"{floor_area_room:.2f} m²", f"{living_area_room:.2f} m²"]
                )

            room_table = Table(room_data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch])
            room_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 11),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F9FAFB")),
                        ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#D1D5DB")),
                    ]
                )
            )
            story.append(room_table)

        doc.build(story)
