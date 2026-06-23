"""Project-centric business service operations."""

from __future__ import annotations

from pathlib import Path

from models.building import Building
from models.floor import Floor
from models.overlay import Overlay
from models.project import Project
from persistence.project_loader import ProjectLoader
from persistence.project_saver import ProjectSaver


class ProjectService:
    """Owns non-UI project lifecycle logic."""

    def __init__(
        self,
        loader: ProjectLoader | None = None,
        saver: ProjectSaver | None = None,
    ) -> None:
        self._loader = loader or ProjectLoader()
        self._saver = saver or ProjectSaver()

    def create_default_project(self) -> tuple[Project, Floor]:
        basement = Floor(name="Basement", elevation=-3000.0)
        ground = Floor(name="Ground floor", elevation=0.0)
        first = Floor(name="First floor", elevation=3000.0)
        second = Floor(name="Second floor", elevation=6000.0)

        building = Building(
            name="Main Building",
            floors=[basement, ground, first, second],
        )

        project = Project(
            name="Untitled Project",
            buildings=[building],
        )

        return project, ground
    
    def load_project(self, file_path: str | Path) -> Project:
        return self._loader.load(file_path)
    
    def save_project(
        self,
        project: Project,
        file_path: str | Path,
    ) -> None:
        self._saver.save(project, file_path)

    def all_floors(self, project: Project) -> list[Floor]:
        """Return all floors from project hierarchy."""
        floors: list[Floor] = []

        for building in project.buildings:
            floors.extend(building.floors)

        return floors

    def find_floor(
        self,
        project: Project,
        floor_name: str,
    ) -> Floor | None:
        """Return floor from project hierarchy."""
        for floor in self.all_floors(project):
            if floor.name == floor_name:
                return floor
        return None
    
    def find_first_floor(
        self,
        project: Project,
    ) -> Floor | None:
        """Return first available floor from project hierarchy."""
        floors = self.all_floors(project)
        return floors[0] if floors else None

    def configure_overlay(
        self,
        active_floor: Floor,
        all_floors: list[Floor],
        show_lower: bool,
        show_upper: bool,
    ) -> None:
        """Configure one-level lower/upper floor overlays for the active floor."""
        active_floor.overlays.clear()

        if not show_lower and not show_upper:
            return

        try:
            index = all_floors.index(active_floor)
        except ValueError:
            return

        if show_lower and index > 0:
            lower_floor = all_floors[index - 1]
            active_floor.overlays.append(
                Overlay(
                    active_floor_id=active_floor.id,
                    source_floor_id=lower_floor.id,
                    visible=True,
                    snap_enabled=True,
                    opacity=0.5,
                )
            )

        if show_upper and index < len(all_floors) - 1:
            upper_floor = all_floors[index + 1]
            active_floor.overlays.append(
                Overlay(
                    active_floor_id=active_floor.id,
                    source_floor_id=upper_floor.id,
                    visible=True,
                    snap_enabled=True,
                    opacity=0.5,
                )
            )
    
