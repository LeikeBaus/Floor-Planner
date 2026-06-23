"""Toolbar widget for the main window."""

from PyQt6.QtWidgets import QMenuBar


class MenuBar(QMenuBar):
    """Build the icon toolbar from shared application actions."""

    def __init__(self, action_manager) -> None:
        super().__init__()

        self.file_menu = self.addMenu("File")
        self.edit_menu = self.addMenu("Edit")
        self.grid_menu = self.addMenu("Grid")
        self.view_menu = self.addMenu("View")

        self._file_actions = action_manager.file_actions.actions()
        self._export_actions = action_manager.export_actions.actions()
        self._snapshot_actions = action_manager.snapshot_actions.actions()
        self._delete_actions = action_manager.delete_actions.actions()
        self._undo_redo_actions = action_manager.undo_redo_actions.actions()
        self._settings_actions = action_manager.settings_actions.actions()
        self._grid_actions = action_manager.grid_actions.actions()
        self._view_actions = action_manager.view_actions.actions()

        self._create_actions()

    def _create_actions(self):
        # File menu
        self.file_menu.addActions(self._file_actions)
        self.file_menu.addSeparator()
        self.file_menu.addActions(self._export_actions)
        self.file_menu.addSeparator()
        self.file_menu.addActions(self._snapshot_actions)
        self.file_menu.addSeparator()

        # Edit menu
        self.edit_menu.addActions(self._delete_actions)
        self.edit_menu.addSeparator()
        self.edit_menu.addActions(self._undo_redo_actions)
        self.edit_menu.addSeparator()
        self.edit_menu.addActions(self._settings_actions)

        # Grid Menu
        self.grid_menu.addActions(self._grid_actions)

        # View menu
        self.view_menu.addActions(self._view_actions)