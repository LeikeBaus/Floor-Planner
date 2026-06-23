"""Command stack service abstraction."""

from __future__ import annotations

from PyQt6.QtGui import QUndoCommand


class CommandService:
    """Provides command-stack operations independent from concrete UI widgets."""

    def push(self, undo_stack: object, command: QUndoCommand) -> None:
        """Push a command to the provided stack-like object."""
        push = getattr(undo_stack, "push", None)
        if callable(push):
            push(command)

    def clear(self, undo_stack: object) -> None:
        """Clear a stack-like object if it supports clear()."""
        clear = getattr(undo_stack, "clear", None)
        if callable(clear):
            clear()
