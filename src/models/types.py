"""Shared type aliases and enums for domain models."""

from __future__ import annotations

from enum import StrEnum


class UnitSystem(StrEnum):
    """Supported display unit systems."""

    METRIC = "METRIC"
