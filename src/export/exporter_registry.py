"""Exporter registry for floor and comparison report outputs."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from geometry.area_comparison_engine import AreaComparison
from models.floor import Floor

FloorExportFn = Callable[[Floor, Path], None]
ComparisonExportFn = Callable[[str, AreaComparison, Path], None]


class ExporterRegistry:
    """Registry for pluggable export handlers by format."""

    def __init__(self) -> None:
        self._floor_exporters: dict[str, FloorExportFn] = {}
        self._comparison_exporters: dict[str, ComparisonExportFn] = {}

    def register_floor_exporter(self, format_id: str, exporter: FloorExportFn) -> None:
        """Register floor exporter for a format (for example: pdf, csv)."""
        self._floor_exporters[format_id.lower()] = exporter

    def register_comparison_exporter(
        self,
        format_id: str,
        exporter: ComparisonExportFn,
    ) -> None:
        """Register area comparison exporter for a format."""
        self._comparison_exporters[format_id.lower()] = exporter

    def get_floor_exporter(self, format_id: str) -> FloorExportFn | None:
        """Return floor exporter for the given format, if any."""
        return self._floor_exporters.get(format_id.lower())

    def get_comparison_exporter(self, format_id: str) -> ComparisonExportFn | None:
        """Return comparison exporter for the given format, if any."""
        return self._comparison_exporters.get(format_id.lower())

    def list_floor_formats(self) -> list[str]:
        """Return sorted list of registered floor export formats."""
        return sorted(self._floor_exporters.keys())

    def list_comparison_formats(self) -> list[str]:
        """Return sorted list of registered comparison export formats."""
        return sorted(self._comparison_exporters.keys())
