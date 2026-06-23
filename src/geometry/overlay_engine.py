"""Overlay engine for managing floor projections."""

from __future__ import annotations

from models.floor import Floor
from models.overlay import Overlay


class OverlayEngine:
    """Manages overlay creation and updates for floor projections."""

    @staticmethod
    def create_overlay(
        active_floor: Floor,
        source_floor: Floor,
        opacity: float = 0.3,
    ) -> Overlay:
        """Create an overlay projection from source floor onto active floor."""
        overlay = Overlay(
            active_floor_id=active_floor.id,
            source_floor_id=source_floor.id,
            visible=True,
            opacity=opacity,
        )
        return overlay

    @staticmethod
    def get_overlay_by_source(
        floor: Floor,
        source_floor_id: str,
    ) -> Overlay | None:
        """Find existing overlay by source floor ID."""
        return next(
            (o for o in floor.overlays if o.source_floor_id == source_floor_id),
            None,
        )

    @staticmethod
    def remove_overlay(floor: Floor, overlay_id: str) -> None:
        """Remove overlay from floor."""
        floor.overlays = [o for o in floor.overlays if o.id != overlay_id]

    @staticmethod
    def toggle_overlay_visibility(overlay: Overlay) -> None:
        """Toggle overlay visibility state."""
        overlay.visible = not overlay.visible

    @staticmethod
    def toggle_overlay_snapping(overlay: Overlay) -> None:
        """Toggle whether an overlay participates in snapping."""
        overlay.snap_enabled = not overlay.snap_enabled

    @staticmethod
    def set_overlay_opacity(overlay: Overlay, opacity: float) -> None:
        """Set overlay opacity (0.0-1.0)."""
        overlay.opacity = max(0.0, min(1.0, opacity))
