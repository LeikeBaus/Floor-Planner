"""Controller for drawing tool selection state."""

from __future__ import annotations

from PyQt6.QtGui import QAction

from models.wall import WallType
from views.scene.drawing_view import DrawingView, ToolMode
from views.widgets.statusbar import StatusBar


class ToolController:
    """Coordinates active drawing tool and related UI state."""

    _TOOL_MODES: dict[str, str] = {
        "select": ToolMode.SELECT,
        "wall_exterior": ToolMode.WALL,
        "wall_interior": ToolMode.WALL,
        "dimension": ToolMode.DIMENSION,
        "window": ToolMode.WINDOW,
        "door": ToolMode.DOOR,
        "opening": ToolMode.OPENING,
        "stair": ToolMode.STAIR,
        "roof_slope": ToolMode.ROOF_SLOPE,
    }

    _TOOL_LABELS: dict[str, str] = {
        "select": "Select",
        "wall_exterior": "Wall (Exterior)",
        "wall_interior": "Wall (Interior)",
        "dimension": "Dimension",
        "window": "Window",
        "door": "Door",
        "opening": "Opening",
        "stair": "Stair",
        "roof_slope": "Roof Slope",
    }

    def __init__(self) -> None:
        self._drawing_view: DrawingView | None = None
        self._status_bar: StatusBar | None = None
        self._tool_actions: dict[str, QAction] = {}

    def configure(
        self,
        drawing_view: DrawingView,
        tool_actions: dict[str, QAction],
        status_bar: StatusBar,
    ) -> None:
        """Attach dependencies needed to switch tools from actions."""
        self._drawing_view = drawing_view
        self._tool_actions = tool_actions
        self._status_bar = status_bar

    def handle_tool_action(self, tool: str) -> None:
        """Handle QAction trigger for drawing tool switching."""
        self.activate_tool(tool)

    def activate_tool(self, tool: str) -> None:
        """Set the active tool and synchronize checked action state."""
        drawing_view = self._drawing_view
        if drawing_view is None:
            return

        mode = self._TOOL_MODES.get(tool)
        if mode is None:
            return

        drawing_view.set_tool_mode(mode)
        if tool == "wall_exterior":
            drawing_view.set_wall_creation_type(WallType.EXTERIOR)
        elif tool == "wall_interior":
            drawing_view.set_wall_creation_type(WallType.INTERIOR)

        for name, action in self._tool_actions.items():
            action.setChecked(name == tool)

        if self._status_bar is not None:
            label = self._TOOL_LABELS.get(tool, "Select")
            self._status_bar.set_tool_text(label)
