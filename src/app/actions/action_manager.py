from PyQt6.QtGui import QAction, QActionGroup
from app.actions.action_registry import ActionID

class ActionManager:

    def __init__(self) -> None:
        
        self.actions: dict[ActionID, QAction] = {}
        self._create_actions()

    def get_action(self, action_id: ActionID) -> QAction:
        """Return the QAction associated with the given ActionID."""
        return self.actions[action_id]

    def _create_actions(self):
        # File actions
        self.file_actions = QActionGroup(None)
        self.actions[ActionID.NEW_PROJECT] = QAction("New")
        self.actions[ActionID.NEW_PROJECT].setShortcut("Ctrl+N")
        self.actions[ActionID.OPEN_PROJECT] = QAction("Open")
        self.actions[ActionID.OPEN_PROJECT].setShortcut("Ctrl+O")
        self.actions[ActionID.SAVE_PROJECT] = QAction("Save")
        self.actions[ActionID.SAVE_PROJECT].setShortcut("Ctrl+S")
        self.actions[ActionID.SAVE_PROJECT].setEnabled(False)  # Initially disabled until a project is loaded
        self.file_actions.addAction(self.actions[ActionID.NEW_PROJECT])
        self.file_actions.addAction(self.actions[ActionID.OPEN_PROJECT])
        self.file_actions.addAction(self.actions[ActionID.SAVE_PROJECT])

        # Export actions
        self.export_actions = QActionGroup(None)
        self.actions[ActionID.EXPORT_PDF] = QAction("Export floor as PDF")
        self.actions[ActionID.EXPORT_CSV] = QAction("Export floor as CSV")
        self.actions[ActionID.EXPORT_PNG] = QAction("Export floor as PNG")
        self.actions[ActionID.EXPORT_SVG] = QAction("Export floor as SVG")
        self.actions[ActionID.EXPORT_XLSX] = QAction("Export floor as XLSX")
        self.actions[ActionID.EXPORT_TXT] = QAction("Export floor as TXT")
        self.actions[ActionID.EXPORT_AREA_COMPARISON] = QAction("Export area comparison")
        self.export_actions.addAction(self.actions[ActionID.EXPORT_PDF])
        self.export_actions.addAction(self.actions[ActionID.EXPORT_CSV])
        self.export_actions.addAction(self.actions[ActionID.EXPORT_PNG])
        self.export_actions.addAction(self.actions[ActionID.EXPORT_SVG])
        self.export_actions.addAction(self.actions[ActionID.EXPORT_XLSX])
        self.export_actions.addAction(self.actions[ActionID.EXPORT_TXT])
        self.export_actions.addAction(self.actions[ActionID.EXPORT_AREA_COMPARISON])
        self.export_actions.setEnabled(False)  # Initially disabled until a project is loaded

        # Delete action
        self.delete_actions = QActionGroup(None)
        self.actions[ActionID.DELETE] = QAction("Delete")
        self.actions[ActionID.DELETE].setShortcut("Del")
        self.delete_actions.addAction(self.actions[ActionID.DELETE])
        self.delete_actions.setEnabled(False)  # Initially disabled until an object is selected

        # Actions for undo/redo
        self.undo_redo_actions = QActionGroup(None)
        self.actions[ActionID.UNDO] = QAction("Undo")
        self.actions[ActionID.UNDO].setShortcut("Ctrl+Z")
        self.actions[ActionID.REDO] = QAction("Redo")
        self.actions[ActionID.REDO].setShortcut("Ctrl+U")
        self.undo_redo_actions.addAction(self.actions[ActionID.UNDO])
        self.undo_redo_actions.addAction(self.actions[ActionID.REDO])
        self.undo_redo_actions.setEnabled(False)  # Initially disabled until undo/redo states are available

        # Snapshot action
        self.snapshot_actions = QActionGroup(None)
        self.actions[ActionID.CREATE_SNAPSHOT] = QAction("Create snapshot")
        self.snapshot_actions.addAction(self.actions[ActionID.CREATE_SNAPSHOT])
        self.snapshot_actions.setEnabled(False)  # Initially disabled until a project is loaded

        # Settings action
        self.settings_actions = QActionGroup(None)
        self.actions[ActionID.SETTINGS] = QAction("Settings")
        self.settings_actions.addAction(self.actions[ActionID.SETTINGS])

        # Grid actions
        self.grid_actions = QActionGroup(None)
        self.actions[ActionID.TOGGLE_GRID] = QAction("Toggle grid")
        self.actions[ActionID.TOGGLE_SNAP] = QAction("Toggle snap")
        self.actions[ActionID.DEBUG_SNAP_MODE] = QAction("Debug snap mode")
        self.actions[ActionID.SHOW_DIMENSIONS] = QAction("Show dimensions")
        self.actions[ActionID.SHOW_HEIGHT_ZONES] = QAction("Show height zones")
        self.grid_actions.addAction(self.actions[ActionID.TOGGLE_GRID])
        self.grid_actions.addAction(self.actions[ActionID.TOGGLE_SNAP])
        self.grid_actions.addAction(self.actions[ActionID.DEBUG_SNAP_MODE])
        self.grid_actions.addAction(self.actions[ActionID.SHOW_DIMENSIONS])
        self.grid_actions.addAction(self.actions[ActionID.SHOW_HEIGHT_ZONES])
        self.grid_actions.setExclusive(False)
        for action in self.grid_actions.actions():
            action.setCheckable(True)
        self.actions[ActionID.TOGGLE_GRID].setChecked(True)
        self.actions[ActionID.TOGGLE_SNAP].setChecked(True)
        self.actions[ActionID.SHOW_DIMENSIONS].setChecked(True)

        # View actions
        self.view_actions = QActionGroup(None)
        self.actions[ActionID.SHOW_PROJECT_PANEL] = QAction("Show project panel")
        self.actions[ActionID.SHOW_SNAPSHOT_PANEL] = QAction("Show snapshot panel")
        self.actions[ActionID.SHOW_PROPERTIES_PANEL] = QAction("Show properties panel")
        self.actions[ActionID.SHOW_SUMMARY_PANEL] = QAction("Show summary panel")
        self.view_actions.addAction(self.actions[ActionID.SHOW_PROJECT_PANEL])
        self.view_actions.addAction(self.actions[ActionID.SHOW_SNAPSHOT_PANEL])
        self.view_actions.addAction(self.actions[ActionID.SHOW_PROPERTIES_PANEL])
        self.view_actions.addAction(self.actions[ActionID.SHOW_SUMMARY_PANEL])
        self.view_actions.setExclusive(False)
        for action in self.view_actions.actions():
            action.setCheckable(True)
            action.setChecked(True)

        # Actions for placing objects
        self.placement_actions = QActionGroup(None)
        self.actions[ActionID.SELECT] = QAction("Select")
        self.actions[ActionID.WALL] = QAction("Wall (Exterior)")
        self.actions[ActionID.INTERIOR_WALL] = QAction("Wall (Interior)")
        self.actions[ActionID.DIMENSION] = QAction("Dimension")
        self.actions[ActionID.WINDOW] = QAction("Window")
        self.actions[ActionID.DOOR] = QAction("Door")
        self.actions[ActionID.OPENING] = QAction("Opening")
        self.actions[ActionID.STAIR] = QAction("Stair")
        self.actions[ActionID.ROOF_SLOPE] = QAction("Roof slope")
        self.placement_actions.addAction(self.actions[ActionID.SELECT])
        self.placement_actions.addAction(self.actions[ActionID.WALL])
        self.placement_actions.addAction(self.actions[ActionID.INTERIOR_WALL])
        self.placement_actions.addAction(self.actions[ActionID.DIMENSION])
        self.placement_actions.addAction(self.actions[ActionID.WINDOW])
        self.placement_actions.addAction(self.actions[ActionID.DOOR])
        self.placement_actions.addAction(self.actions[ActionID.OPENING])
        self.placement_actions.addAction(self.actions[ActionID.STAIR])
        self.placement_actions.addAction(self.actions[ActionID.ROOF_SLOPE])
        self.placement_actions.setExclusive(True)
        self.placement_actions.setEnabled(False)  # Initially disabled until a project is loaded

        # Floor actions
        self.floor_actions = QActionGroup(None)
        self.actions[ActionID.BASEMENT] = QAction("Basement")
        self.actions[ActionID.GROUND_FLOOR] = QAction("Ground Floor")
        self.actions[ActionID.FIRST_FLOOR] = QAction("First Floor")
        self.actions[ActionID.SECOND_FLOOR] = QAction("Second Floor")
        self.floor_actions.addAction(self.actions[ActionID.BASEMENT])
        self.floor_actions.addAction(self.actions[ActionID.GROUND_FLOOR])
        self.floor_actions.addAction(self.actions[ActionID.FIRST_FLOOR])
        self.floor_actions.addAction(self.actions[ActionID.SECOND_FLOOR])
        self.floor_actions.setExclusive(True)
        self.floor_actions.setEnabled(False)  # Initially disabled until a project is loaded
