"""Area comparison engine for measuring roof slope impact on living areas."""

from __future__ import annotations

from dataclasses import dataclass

from models.floor import Floor
from models.height_zone import HeightZoneType


@dataclass(slots=True)
class AreaComparison:
    """Metrics comparing original floor area vs. living area after roof slope application."""

    total_floor_area: float
    total_living_area: float
    total_under_1m_area: float
    total_between_1m_2m_area: float
    total_above_2m_area: float

    @property
    def area_loss_mm2(self) -> float:
        """Calculate total area lost due to roof slope sloping (under 1m zones)."""
        return self.total_under_1m_area

    @property
    def area_loss_percent(self) -> float:
        """Calculate percentage of floor area lost to roof slope."""
        if self.total_floor_area <= 0.0:
            return 0.0
        return (self.area_loss_mm2 / self.total_floor_area) * 100.0

    @property
    def partially_usable_mm2(self) -> float:
        """Calculate area with partial usability (1m-2m zones, 50% factor)."""
        return self.total_between_1m_2m_area

    @property
    def fully_usable_mm2(self) -> float:
        """Calculate fully usable area (above 2m zones)."""
        return self.total_above_2m_area


class AreaComparisonEngine:
    """Calculate area metrics for comparing floor areas before/after roof slope application."""

    def calculate_comparison(self, floor: Floor) -> AreaComparison:
        """Generate area comparison metrics from floor with height zones."""
        total_floor_area = floor.floor_area_total
        total_living_area = floor.living_area_total

        under_1m_area = 0.0
        between_1m_2m_area = 0.0
        above_2m_area = 0.0

        for zone in floor.height_zones:
            zone_area = zone.get_area()
            if zone.zone_type == HeightZoneType.UNDER_1M:
                under_1m_area += zone_area
            elif zone.zone_type == HeightZoneType.BETWEEN_1M_AND_2M:
                between_1m_2m_area += zone_area
            elif zone.zone_type == HeightZoneType.ABOVE_2M:
                above_2m_area += zone_area

        return AreaComparison(
            total_floor_area=total_floor_area,
            total_living_area=total_living_area,
            total_under_1m_area=under_1m_area,
            total_between_1m_2m_area=between_1m_2m_area,
            total_above_2m_area=above_2m_area,
        )
