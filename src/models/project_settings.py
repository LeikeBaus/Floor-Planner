"""Project-level default settings model."""

from __future__ import annotations

from dataclasses import dataclass

from models.types import UnitSystem


@dataclass(slots=True)
class ProjectSettings:
    """Global defaults and behavior settings for a FloorPlanner project."""

    default_exterior_wall_thickness: float = 300.0
    default_interior_wall_thickness: float = 110.0
    grid_size: float = 100.0
    grid_opacity: float = 0.55
    grid_enabled: bool = True
    snap_enabled: bool = True
    snap_distance: float = 400.0
    angle_snap_increment: float = 15.0
    autosave_interval: int = 300
    show_dimensions: bool = True
    dimension_opacity: float = 0.5
    dimension_font_size: float = 132.0
    lower_level_opacity: float = 0.7
    unit_system: UnitSystem = UnitSystem.METRIC

    def to_dict(self) -> dict[str, float | bool | int | str]:
        """Serialize settings to JSON-compatible dictionary."""
        return {
            "default_exterior_wall_thickness": self.default_exterior_wall_thickness,
            "default_interior_wall_thickness": self.default_interior_wall_thickness,
            "grid_size": self.grid_size,
            "grid_opacity": self.grid_opacity,
            "grid_enabled": self.grid_enabled,
            "snap_enabled": self.snap_enabled,
            "snap_distance": self.snap_distance,
            "angle_snap_increment": self.angle_snap_increment,
            "autosave_interval": self.autosave_interval,
            "show_dimensions": self.show_dimensions,
            "dimension_opacity": self.dimension_opacity,
            "dimension_font_size": self.dimension_font_size,
            "lower_level_opacity": self.lower_level_opacity,
            "unit_system": self.unit_system.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, float | bool | int | str]) -> ProjectSettings:
        """Create settings from JSON-compatible dictionary."""
        return cls(
            default_exterior_wall_thickness=float(
                data.get("default_exterior_wall_thickness", 300.0)
            ),
            default_interior_wall_thickness=float(
                data.get("default_interior_wall_thickness", 110.0)
            ),
            grid_size=float(data.get("grid_size", 100.0)),
            grid_opacity=float(data.get("grid_opacity", 0.55)),
            grid_enabled=bool(data.get("grid_enabled", True)),
            snap_enabled=bool(data.get("snap_enabled", True)),
            snap_distance=float(data.get("snap_distance", 200.0)),
            angle_snap_increment=float(data.get("angle_snap_increment", 15.0)),
            autosave_interval=int(data.get("autosave_interval", 300)),
            show_dimensions=bool(data.get("show_dimensions", True)),
            dimension_opacity=float(data.get("dimension_opacity", 0.3)),
            dimension_font_size=float(data.get("dimension_font_size", 72.0)),
            lower_level_opacity=float(data.get("lower_level_opacity", 0.7)),
            unit_system=UnitSystem(str(data.get("unit_system", UnitSystem.METRIC.value))),
        )
