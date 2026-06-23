"""main_window.py"""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QWidget, QDockWidget

from app.actions.action_manager import ActionManager

from views.factory.main_view_factory import MainViewFactory
from views.factory.scene_factory import SceneFactory
from views.factory.dock_factory import DockFactory


class MainWindow(QMainWindow):
    """
    Main application window.

    Responsibility:
    - Assemble UI components via factories
    - Provide access points for wiring layer
    - No business logic
    """

    def __init__(self, action_manager: ActionManager) -> None:
        super().__init__()

        self._action_manager = action_manager

        # UI references (needed for wiring)
        self._drawing_scene = None
        self._drawing_view = None

        self._project_tree_panel = None
        self._snapshot_history_panel = None
        self._properties_panel = None
        self._floor_summary_panel = None

        self._init_ui()

    # ------------------------------------------------------------
    # UI BUILD
    # ------------------------------------------------------------

    def _init_ui(self) -> None:
        self.setWindowTitle("FloorPlanner")

        self._build_central_view()
        self._build_menus_and_bars()
        self._build_docks()

    def _build_central_view(self) -> None:
        """
        Central drawing area (Scene + View).
        """
        self._drawing_scene = SceneFactory.create()
        self._drawing_view = MainViewFactory.create_drawing_view(
            self._drawing_scene
        )

        self.setCentralWidget(self._drawing_view)

    def _build_menus_and_bars(self) -> None:
        """
        MenuBar + ToolBar + StatusBar.
        """
        self.setMenuBar(
            MainViewFactory.create_menu_bar(self._action_manager)
        )

        self.addToolBar(
            MainViewFactory.create_tool_bar(self._action_manager)
        )

        self.setStatusBar(
            MainViewFactory.create_status_bar()
        )

    def _build_docks(self) -> None:
        """
        Dock widgets (project tree, properties, snapshots, summary).
        """
        dock_bundle = DockFactory.create_all(self)

        self._project_tree_panel = dock_bundle.project_tree
        self._snapshot_history_panel = dock_bundle.snapshot_history
        self._properties_panel = dock_bundle.properties
        self._floor_summary_panel = dock_bundle.floor_summary

    # ------------------------------------------------------------
    # PUBLIC ACCESSORS (for wiring layer)
    # ------------------------------------------------------------

    def get_scene(self):
        return self._drawing_scene

    def get_view(self):
        return self._drawing_view

    def get_project_tree_panel(self):
        return self._project_tree_panel

    def get_snapshot_history_panel(self):
        return self._snapshot_history_panel

    def get_properties_panel(self):
        return self._properties_panel

    def get_floor_summary_panel(self):
        return self._floor_summary_panel

    # ------------------------------------------------------------
    # STATE UPDATE HELPERS (called by wiring layer)
    # ------------------------------------------------------------

    def set_window_title(self, title: str) -> None:
        self.setWindowTitle(title)

    def set_active_project_view(self, project_name: str) -> None:
        self.setWindowTitle(f"FloorPlanner - {project_name}")