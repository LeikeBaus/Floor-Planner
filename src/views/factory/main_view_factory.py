from PyQt6.QtWidgets import QToolBar, QStatusBar

from views.widgets.menubar import MenuBar
from views.widgets.toolbar import ToolBar
from views.widgets.statusbar import StatusBar
from views.scene.drawing_view import DrawingView


class MainViewFactory:
    """Creates top-level UI components for MainWindow."""

    @staticmethod
    def create_menu_bar(action_manager):
        return MenuBar(action_manager)

    @staticmethod
    def create_tool_bar(action_manager) -> QToolBar:
        return ToolBar(action_manager)

    @staticmethod
    def create_status_bar() -> QStatusBar:
        return StatusBar()

    @staticmethod
    def create_drawing_view(scene) -> DrawingView:
        return DrawingView(scene)