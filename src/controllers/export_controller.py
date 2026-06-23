"""Controller coordinating export use cases."""

from __future__ import annotations

from pathlib import Path

from models.floor import Floor
from services.export_service import ExportService


class ExportController:
    """Entry point for export workflows from the view layer."""

    def __init__(self, service: ExportService) -> None:
        self._service = service

    def export_floor(self, floor: Floor, export_format: str, target_path: str | Path) -> None:
        """Export current floor in one of the registered formats."""
        self._service.export_floor(floor, export_format, target_path)

    def export_comparison_report(self, floor: Floor, target_path: str | Path) -> None:
        """Export current floor area-comparison report as PDF."""
        self._service.export_comparison_report(floor, target_path)
