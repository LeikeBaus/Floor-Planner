"""Export business logic and exporter registration."""

from __future__ import annotations

from pathlib import Path

from export.exporter_registry import ExporterRegistry
from geometry.area_comparison_engine import AreaComparisonEngine
from models.floor import Floor
from services.comparison_pdf_exporter import ComparisonPdfExporter
from services.floor_csv_exporter import FloorCsvExporter
from services.floor_pdf_exporter import FloorPdfExporter
from services.floor_png_exporter import FloorPngExporter
from services.floor_svg_exporter import FloorSvgExporter
from services.floor_txt_exporter import FloorTxtExporter
from services.floor_xlsx_exporter import FloorXlsxExporter


class ExportService:
    """Provides export capabilities independent from UI concerns."""

    def __init__(
        self,
        registry: ExporterRegistry | None = None,
        area_comparison_engine: AreaComparisonEngine | None = None,
    ) -> None:
        self._registry = registry or ExporterRegistry()
        self._area_comparison_engine = area_comparison_engine or AreaComparisonEngine()
        self._register_defaults()

    def _register_defaults(self) -> None:
        self._registry.register_floor_exporter("pdf", FloorPdfExporter().export)
        self._registry.register_floor_exporter("csv", FloorCsvExporter().export)
        self._registry.register_floor_exporter("png", FloorPngExporter().export)
        self._registry.register_floor_exporter("svg", FloorSvgExporter().export)
        self._registry.register_floor_exporter("xlsx", FloorXlsxExporter().export)
        self._registry.register_floor_exporter("txt", FloorTxtExporter().export)
        self._registry.register_comparison_exporter("pdf", ComparisonPdfExporter().export)

    def export_floor(self, floor: Floor, export_format: str, target_path: str | Path) -> None:
        """Export floor in requested format."""
        exporter = self._registry.get_floor_exporter(export_format)
        if exporter is None:
            raise ValueError(f"No floor exporter is registered for '{export_format}'")
        exporter(floor, Path(target_path))

    def export_comparison_report(self, floor: Floor, target_path: str | Path) -> None:
        """Export area comparison report for a floor."""
        exporter = self._registry.get_comparison_exporter("pdf")
        if exporter is None:
            raise ValueError("No comparison PDF exporter is registered")
        comparison = self._area_comparison_engine.calculate_comparison(floor)
        exporter(floor.name, comparison, Path(target_path))
