"""Controller wrapper around command stack operations."""

from __future__ import annotations

from PyQt6.QtGui import QUndoCommand

from services.command_service import CommandService


class CommandController:
    """Controller wrapper around command stack operations."""

    def __init__(self, service: CommandService | None = None) -> None:
        self._service = service or CommandService()

    def push(self, undo_stack: object, command: QUndoCommand) -> None:
        """Push an undoable command onto the configured stack."""
        self._service.push(undo_stack, command)

    def clear(self, undo_stack: object) -> None:
        """Clear all commands from the stack."""
        self._service.clear(undo_stack)
