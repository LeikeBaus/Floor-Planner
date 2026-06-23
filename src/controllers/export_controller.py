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

    def handle_export_floor_action(self, window: object, export_format: str) -> None:
        """Handle QAction trigger for floor export."""
        export_handlers = {
            "pdf": "_export_floor_pdf",
            "csv": "_export_floor_csv",
            "png": "_export_floor_png",
            "svg": "_export_floor_svg",
            "xlsx": "_export_floor_xlsx",
            "txt": "_export_floor_txt",
        }
        handler_name = export_handlers.get(export_format)
        if handler_name is None:
            return
        handler = getattr(window, handler_name, None)
        if callable(handler):
            handler()

    def handle_export_comparison_action(self, window: object) -> None:
        """Handle QAction trigger for comparison report export."""
        handler = getattr(window, "_export_comparison_report", None)
        if callable(handler):
            handler()

    def handle_create_snapshot_action(self, window: object) -> None:
        """Handle QAction trigger for snapshot creation."""
        handler = getattr(window, "_create_snapshot", None)
        if callable(handler):
            handler()
