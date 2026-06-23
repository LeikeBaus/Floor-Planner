"""Controller for drawing-focused application workflows."""

from __future__ import annotations

from models.floor import Floor
from models.project import Project
from services.drawing_service import DrawingService


class DrawingController:
    """Coordinates drawing domain updates requested by views."""

    def __init__(self, service: DrawingService) -> None:
        self._service = service

    def recalculate_floor(self, project: Project, floor: Floor) -> None:
        """Recalculate all derived floor data based on current project settings."""
        self._service.recalculate_floor(floor, project.settings)

    def handle_delete_selection_action(self, window: object) -> None:
        """Handle QAction trigger for deleting selection."""
        handler = getattr(window, "_delete_selected_walls", None)
        if callable(handler):
            handler()
