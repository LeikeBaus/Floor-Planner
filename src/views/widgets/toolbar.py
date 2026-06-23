"""Toolbar widget for the main window."""

from PyQt6.QtWidgets import QToolBar


class ToolBar(QToolBar):
    """Build the icon toolbar from shared application actions."""

    def __init__(self, action_manager) -> None:
        super().__init__()
        self._placement_actions = action_manager.placement_actions.actions()
        self._undo_redo_actions = action_manager.undo_redo_actions.actions()
        self._floor_actions = action_manager.floor_actions.actions()
        
        self.setMovable(False)

        self._create_actions()

    def _create_actions(self):
        self.addActions(self._placement_actions)
        self.addSeparator()
        self.addActions(self._undo_redo_actions)
        self.addSeparator()
        self.addActions(self._floor_actions)