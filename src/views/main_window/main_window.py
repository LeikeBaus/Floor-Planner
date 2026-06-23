"""main_window.py"""
from __future__ import annotations

from PyQt6.QtGui import QUndoStack
from PyQt6.QtWidgets import QMainWindow

from app.actions.action_manager import ActionManager
from app.actions.action_registry import ActionID
from models.floor import Floor
from models.project import Project
from models.project_settings import ProjectSettings
from views.factory.main_view_factory import MainViewFactory
from views.factory.scene_factory import SceneFactory
from views.factory.dock_composer import DockComposer
from views.factory.dock_factory import DockFactory


class MainWindow(QMainWindow):
    """
    Main application window.

    Responsibility:
    - Assemble UI components via factories
    - Provide access points for wiring layer
    """

    def __init__(self, action_manager: ActionManager) -> None:
        super().__init__()

        self._action_manager = action_manager
        self._undo_stack = QUndoStack(self)

        # UI references
        self._drawing_scene = None
        self._drawing_view = None

        self._project_tree_panel = None
        self._snapshot_history_panel = None
        self._properties_panel = None
        self._floor_summary_panel = None
        self._project: Project | None = None
        self._docks: dict[str, object] = {}

        self._init_ui()

    # --- UI build  -------------------------------------------------------------

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
        self._drawing_view = MainViewFactory.create_drawing_view(self._drawing_scene)
        self._drawing_view.set_command_sink(self._undo_stack)
        self._drawing_view.set_wall_callbacks(self._drawing_scene)
        self.setCentralWidget(self._drawing_view)

        self._undo_stack.canUndoChanged.connect(
            lambda enabled: self._action_manager.get_action(ActionID.UNDO).setEnabled(enabled)
        )
        self._undo_stack.canRedoChanged.connect(
            lambda enabled: self._action_manager.get_action(ActionID.REDO).setEnabled(enabled)
        )
        self._drawing_scene.selectionChanged.connect(self._sync_delete_action_enabled)

    def _build_menus_and_bars(self) -> None:
        """
        Menu bar, tool bar, status bar.
        """
        self.setMenuBar(MainViewFactory.create_menu_bar(self._action_manager))
        self.addToolBar(MainViewFactory.create_tool_bar(self._action_manager))
        self.setStatusBar(MainViewFactory.create_status_bar())

    def _build_docks(self) -> None:
        """
        Dock widgets (project tree, properties, snapshots, summary).
        """
        widgets = DockFactory.create_widgets()
        composer = DockComposer(self)
        self._docks = composer.compose(widgets)

        self._project_tree_panel = widgets.project_tree
        self._snapshot_history_panel = widgets.snapshot_history
        self._properties_panel = widgets.properties
        self._floor_summary_panel = widgets.floor_summary

        for panel_name, dock in self._docks.items():
            dock.visibilityChanged.connect(
                lambda visible, name=panel_name: self._on_dock_visibility_changed(name, visible)
            )
            self._on_dock_visibility_changed(panel_name, dock.isVisible())

        self._set_project_actions_enabled(False)
        self._sync_delete_action_enabled()

    # --- Public accessors ---------------------------------------------------

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

    def get_undo_stack(self) -> QUndoStack:
        return self._undo_stack

    def set_grid_enabled(self, enabled: bool) -> None:
        if self._drawing_scene is None:
            return
        self._drawing_scene.grid_enabled = enabled
        self._drawing_scene.update(self._drawing_scene.sceneRect())

    def set_snap_enabled(self, enabled: bool, distance_mm: float) -> None:
        if self._drawing_view is None:
            return
        self._drawing_view.set_snap_options(enabled=enabled, distance_mm=distance_mm)

    def set_dimensions_visible(self, enabled: bool) -> None:
        if self._drawing_scene is None:
            return
        self._drawing_scene.set_dimensions_visibility(enabled)

    def set_height_zones_visible(self, enabled: bool) -> None:
        if self._drawing_scene is None:
            return
        self._drawing_scene.set_height_zones_visibility(enabled)

    def set_debug_snap_enabled(self, enabled: bool) -> None:
        if self._drawing_view is None:
            return
        self._drawing_view.set_debug_snap_enabled(enabled)

    def set_panel_visibility(self, panel: str, visible: bool) -> None:
        dock = self._docks.get(panel)
        if dock is None:
            return
        set_visible = getattr(dock, "setVisible", None)
        if callable(set_visible):
            set_visible(visible)

    def set_one_level_overlay_enabled(self, lower_enabled: bool, upper_enabled: bool) -> None:
        """Synchronize lower/upper overlay checkbox states in the summary panel."""
        if self._floor_summary_panel is not None:
            self._floor_summary_panel.set_one_level_overlay_enabled(lower_enabled, upper_enabled)

    def apply_project_settings(self, settings: ProjectSettings) -> None:
        """Apply editable project settings to scene/view/panels."""
        if self._drawing_scene is not None:
            self._drawing_scene.grid_opacity = settings.grid_opacity
            self._drawing_scene.grid_enabled = settings.grid_enabled
            self._drawing_scene.set_dimensions_visibility(settings.show_dimensions)
            self._drawing_scene.set_dimension_opacity(settings.dimension_opacity)
            self._drawing_scene.set_dimension_font_size(settings.dimension_font_size)

        if self._drawing_view is not None:
            self._drawing_view.set_snap_options(
                enabled=settings.snap_enabled,
                distance_mm=settings.snap_distance,
            )
            self._drawing_view.set_angle_snap_increment(settings.angle_snap_increment)
            self._drawing_view.set_wall_defaults(
                exterior_thickness_mm=settings.default_exterior_wall_thickness,
                interior_thickness_mm=settings.default_interior_wall_thickness,
            )
            self._drawing_view.set_dimension_options(
                visible=settings.show_dimensions,
                opacity=settings.dimension_opacity,
            )

        if self._properties_panel is not None:
            self._properties_panel.set_wall_defaults(
                settings.default_exterior_wall_thickness,
                settings.default_interior_wall_thickness,
            )

        self._set_check_state(ActionID.TOGGLE_GRID, settings.grid_enabled)
        self._set_check_state(ActionID.TOGGLE_SNAP, settings.snap_enabled)
        self._set_check_state(ActionID.SHOW_DIMENSIONS, settings.show_dimensions)

    def refresh_active_floor_view(self) -> None:
        """Repaint all active-floor dependent scene layers."""
        if self._drawing_scene is None:
            return
        self._drawing_scene.refresh_walls()
        self._drawing_scene.refresh_windows()
        self._drawing_scene.refresh_doors()
        self._drawing_scene.refresh_openings()
        self._drawing_scene.refresh_stairs()
        self._drawing_scene.refresh_roof_slopes()
        self._drawing_scene.refresh_rooms()
        self._drawing_scene.refresh_height_zones()
        self._drawing_scene.refresh_dimensions()
    
    # --- State update helpers ---------------------------------------------------

    def set_window_title(self, title: str) -> None:
        self.setWindowTitle(title)

    def set_active_project_view(self, project_name: str) -> None:
        self.setWindowTitle(f"FloorPlanner - {project_name}")

    def on_project_bound(self, project: Project, active_floor: Floor) -> None:
        """Apply project-level UI updates after project create/load."""
        self._project = project
        self._set_project_actions_enabled(True)
        self.apply_project_settings(project.settings)
        if self._project_tree_panel is not None:
            self._project_tree_panel.set_project(project, active_floor)
        if self._floor_summary_panel is not None:
            self._floor_summary_panel.update_floor_info(active_floor)

    def on_active_floor_changed(self, floor: Floor, _available_floors: list[Floor]) -> None:
        """Apply floor-level panel updates whenever active floor changes."""
        if self._project is not None and self._project_tree_panel is not None:
            self._project_tree_panel.set_project(self._project, floor)
        if self._floor_summary_panel is not None:
            self._floor_summary_panel.update_floor_info(floor)

        floor_action = {
            "Basement": ActionID.BASEMENT,
            "Ground floor": ActionID.GROUND_FLOOR,
            "First floor": ActionID.FIRST_FLOOR,
            "Second floor": ActionID.SECOND_FLOOR,
        }.get(floor.name)
        if floor_action is not None:
            self._set_check_state(floor_action, True)

    # TEMP: compatibility endpoint used by crash-recovery startup flow.
    def load_recovered_project(self, project: Project) -> None:
        """Bind recovered project into UI using first available floor."""
        active_floor: Floor | None = None
        if project.buildings and project.buildings[0].floors:
            active_floor = project.buildings[0].floors[0]
        if active_floor is not None:
            self.on_project_bound(project, active_floor)

    def perform_undo(self) -> None:
        self._undo_stack.undo()

    def perform_redo(self) -> None:
        self._undo_stack.redo()

    def perform_delete_selection(self) -> None:
        if self._drawing_view is not None:
            self._drawing_view.delete_selected_items()

    def clear_undo_history(self) -> None:
        self._undo_stack.clear()
        self._action_manager.get_action(ActionID.UNDO).setEnabled(False)
        self._action_manager.get_action(ActionID.REDO).setEnabled(False)

    def _set_project_actions_enabled(self, enabled: bool) -> None:
        self._action_manager.export_actions.setEnabled(enabled)
        self._action_manager.snapshot_actions.setEnabled(enabled)
        self._action_manager.placement_actions.setEnabled(enabled)
        self._action_manager.floor_actions.setEnabled(enabled)
        self._action_manager.undo_redo_actions.setEnabled(enabled)
        self._action_manager.get_action(ActionID.SAVE_PROJECT).setEnabled(enabled)

        if enabled:
            self._action_manager.get_action(ActionID.UNDO).setEnabled(self._undo_stack.canUndo())
            self._action_manager.get_action(ActionID.REDO).setEnabled(self._undo_stack.canRedo())
            self._sync_delete_action_enabled()
        else:
            self._action_manager.get_action(ActionID.UNDO).setEnabled(False)
            self._action_manager.get_action(ActionID.REDO).setEnabled(False)
            self._action_manager.get_action(ActionID.DELETE).setEnabled(False)

    def _sync_delete_action_enabled(self) -> None:
        if self._drawing_scene is None:
            self._action_manager.get_action(ActionID.DELETE).setEnabled(False)
            return
        has_selection = bool(self._drawing_scene.selectedItems())
        self._action_manager.get_action(ActionID.DELETE).setEnabled(has_selection)

    def _on_dock_visibility_changed(self, panel: str, visible: bool) -> None:
        action_id = {
            "project": ActionID.SHOW_PROJECT_PANEL,
            "snapshot": ActionID.SHOW_SNAPSHOT_PANEL,
            "properties": ActionID.SHOW_PROPERTIES_PANEL,
            "summary": ActionID.SHOW_SUMMARY_PANEL,
        }.get(panel)
        if action_id is None:
            return
        self._set_check_state(action_id, visible)

    def _set_check_state(self, action_id: ActionID, checked: bool) -> None:
        action = self._action_manager.get_action(action_id)
        if action.isChecked() == checked:
            return
        action.blockSignals(True)
        action.setChecked(checked)
        action.blockSignals(False)