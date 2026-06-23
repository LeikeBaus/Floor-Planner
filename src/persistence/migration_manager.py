"""Project file migration utilities."""

from __future__ import annotations


class MigrationError(Exception):
    """Raised when file migration cannot be completed."""


class MigrationManager:
    """Migrates persisted project payloads to the current file version."""

    CURRENT_FILE_VERSION = 1

    def migrate(self, payload: dict[str, object]) -> dict[str, object]:
        """Migrate a payload to CURRENT_FILE_VERSION."""
        version = _to_int(payload.get("file_version"), default=1)

        if version > self.CURRENT_FILE_VERSION:
            raise MigrationError(
                f"Unsupported file version {version}. "
                f"Current version is {self.CURRENT_FILE_VERSION}."
            )

        # Placeholder for future migrations (v1 -> v2, etc.).
        payload["file_version"] = self.CURRENT_FILE_VERSION
        return payload


def _to_int(value: object, default: int) -> int:
    """Convert persisted value to int with a safe fallback."""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default
