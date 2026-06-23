"""File dialog coordination for open/save/export workflows."""

from __future__ import annotations

from PyQt6.QtWidgets import QFileDialog, QWidget


class FileDialogService:
    """Provides file selection dialogs for project and export workflows."""

    def __init__(self, parent: QWidget | None = None) -> None:
        self._parent = parent

    def pick_open_project_path(self) -> str | None:
        """Prompt user to select a project file to open."""
        selected, _filter = QFileDialog.getOpenFileName(
            self._parent,
            "Open Project",
            "",
            "FloorPlanner Project (*.fplan);;All Files (*)",
        )
        return selected or None

    def pick_save_project_path(self) -> str | None:
        """Prompt user to select a destination path for project save-as."""
        selected, _filter = QFileDialog.getSaveFileName(
            self._parent,
            "Save Project",
            "",
            "FloorPlanner Project (*.fplan);;All Files (*)",
        )
        return selected or None

    def pick_export_path(self, title: str, extension: str) -> str | None:
        """Prompt user to select a destination path for export."""
        selected, _filter = QFileDialog.getSaveFileName(
            self._parent,
            title,
            "",
            f"{extension.upper()} (*.{extension});;All Files (*)",
        )
        return selected or None
