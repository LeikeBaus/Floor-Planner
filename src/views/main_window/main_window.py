"""Main window shell for FloorPlanner."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCloseEvent, QUndoStack
from PyQt6.QtWidgets import (
    QDockWidget,
    QMainWindow,
    QWidget,
)

from views.scene.drawing_scene import DrawingScene
from views.scene.drawing_view import DrawingView
from views.panels.floor_summary_panel import FloorSummaryPanel
from views.panels.object_properties_panel import ObjectPropertiesPanel
from views.widgets.menubar import MenuBar
from views.widgets.statusbar import StatusBar
from views.widgets.toolbar import ToolBar
from views.panels.project_tree_panel import ProjectTreePanel
from views.dialogs.settings_dialog import SettingsDialog
from views.panels.snapshot_history_panel import SnapshotHistoryPanel


class MainWindow(QMainWindow):
    """Top-level application shell with primary layout regions."""

    def __init__(self, action_manager) -> None:
        super().__init__()
        
        self.action_manager = action_manager

        self._setup_window()
        self._init_ui()

    def _setup_window(self) -> None:
        """Initialize main window layout and widgets."""
        self.setWindowTitle("FloorPlanner")
        self.resize(1440, 900)

    def _init_ui(self) -> None:
        # Central drawing area
        self.setCentralWidget(self._create_drawing_area())
        # Bars
        self.setMenuBar(MenuBar(self.action_manager))
        self.addToolBar(ToolBar(self.action_manager))
        self._build_docks()
        self.setStatusBar(StatusBar(self))

    def _create_drawing_area(self) -> QWidget:
        scene = DrawingScene()
        available_floors = self._get_all_floors_from_project(self._project)
        scene.set_active_floor(self._active_floor, available_floors)
        drawing_view = DrawingView(scene)
        drawing_view.set_command_sink(self._undo_stack)
        drawing_view.set_wall_callbacks(self)
        drawing_view.cursor_world_changed.connect(self._update_cursor_status)
        drawing_view.snap_debug_changed.connect(self._update_debug_snap_status)
        drawing_view.wall_preview_length_changed.connect(self._update_wall_length_status)
        scene.selectionChanged.connect(self._on_scene_selection_changed)
        self._drawing_scene = scene
        self._drawing_view = drawing_view
        self._apply_project_settings()
        return drawing_view
    
    def _build_docks(self) -> None:
        project_dock = QDockWidget("Project", self)
        project_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self._project_tree_panel = ProjectTreePanel()
        project_dock.setWidget(self._project_tree_panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, project_dock)

        summary_dock = QDockWidget("Summary", self)

        properties_dock = QDockWidget("Properties", self)
        properties_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self._object_properties_panel = ObjectPropertiesPanel()
        properties_dock.setWidget(self._object_properties_panel)

        history_dock = QDockWidget("Snapshot History", self)
        history_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self._snapshot_history_panel = SnapshotHistoryPanel()
        self._snapshot_history_panel.snapshot_restore_requested.connect(self._restore_snapshot)
        self._snapshot_history_panel.snapshot_delete_requested.connect(self._delete_snapshot)
        history_dock.setWidget(self._snapshot_history_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, history_dock)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, properties_dock)
        summary_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self._floor_summary_panel = FloorSummaryPanel()
        self._floor_summary_panel.one_level_overlay_toggled.connect(
            self._on_one_level_overlay_toggled
        )
        summary_dock.setWidget(self._floor_summary_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, summary_dock)
        self.splitDockWidget(history_dock, properties_dock, Qt.Orientation.Vertical)
        self.splitDockWidget(properties_dock, summary_dock, Qt.Orientation.Vertical)