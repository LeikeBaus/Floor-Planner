"""PDF exporter for area comparison and impact analysis reports."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from geometry.area_comparison_engine import AreaComparison


class ComparisonPdfExporter:
    """Export area comparison analysis to PDF report."""

    def __init__(self) -> None:
        """Initialize exporter with default styles."""
        self._stylesheet = getSampleStyleSheet()

    def export(
        self, floor_name: str, comparison: AreaComparison, output_path: Path
    ) -> None:
        """Generate PDF report comparing floor area vs. living area impact."""
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
        story.append(Paragraph(f"Area Impact Analysis: {floor_name}", title_style))

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        story.append(Paragraph(f"<i>Generated: {timestamp}</i>", self._stylesheet["Normal"]))
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph("Executive Summary", self._stylesheet["Heading2"]))
        floor_area_m2 = comparison.total_floor_area / 1_000_000.0
        living_area_m2 = comparison.total_living_area / 1_000_000.0
        area_loss_m2 = comparison.area_loss_mm2 / 1_000_000.0
        area_loss_pct = comparison.area_loss_percent

        summary_text = (
            f"This floor has a total area of <b>{floor_area_m2:.2f} m²</b>. "
            f"After accounting for roof slope and height restrictions, "
            f"the usable living area is <b>{living_area_m2:.2f} m²</b> "
            f"(<b>{area_loss_pct:.1f}%</b> reduction, {area_loss_m2:.2f} m² lost)."
        )
        story.append(Paragraph(summary_text, self._stylesheet["Normal"]))
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph("Area Breakdown", self._stylesheet["Heading2"]))
        fully_usable_m2 = comparison.fully_usable_mm2 / 1_000_000.0
        partial_usable_m2 = comparison.partially_usable_mm2 / 1_000_000.0
        under_1m_m2 = comparison.total_under_1m_area / 1_000_000.0

        breakdown_data = [
            ["Zone Type", "Area (m²)", "Usability", "Percentage"],
            [
                "Above 2m",
                f"{fully_usable_m2:.2f}",
                "100% (fully usable)",
                f"{(fully_usable_m2 / floor_area_m2 * 100):.1f}%",
            ],
            [
                "1m–2m",
                f"{partial_usable_m2:.2f}",
                "50% (partial)",
                f"{(partial_usable_m2 / floor_area_m2 * 100):.1f}%",
            ],
            [
                "Under 1m",
                f"{under_1m_m2:.2f}",
                "0% (unusable)",
                f"{(under_1m_m2 / floor_area_m2 * 100):.1f}%",
            ],
        ]

        breakdown_table = Table(
            breakdown_data,
            colWidths=[1.5 * inch, 1.2 * inch, 1.5 * inch, 1 * inch],
        )
        breakdown_table.setStyle(
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
        story.append(breakdown_table)
        story.append(Spacer(1, 0.3 * inch))

        story.append(Paragraph("Area Comparison", self._stylesheet["Heading2"]))
        comparison_data = [
            ["Metric", "Value", "Impact"],
            ["Floor Area", f"{floor_area_m2:.2f} m²", "100% (design envelope)"],
            [
                "Living Area",
                f"{living_area_m2:.2f} m²",
                f"{(living_area_m2 / floor_area_m2 * 100):.1f}% effective",
            ],
            ["Area Reduction", f"{area_loss_m2:.2f} m²", f"{area_loss_pct:.1f}% lost to slope"],
        ]

        comparison_table = Table(
            comparison_data, colWidths=[1.5 * inch, 1.5 * inch, 1.5 * inch]
        )
        comparison_table.setStyle(
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
        story.append(comparison_table)

        doc.build(story)
