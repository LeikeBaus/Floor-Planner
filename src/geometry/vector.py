"""Immutable vector value object."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Vector:
    """Directional vector in millimeters."""

    dx: float
    dy: float
