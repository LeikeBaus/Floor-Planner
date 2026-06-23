"""Living area calculation utilities based on height zones."""

from __future__ import annotations

from geometry.point import Point
from models.height_zone import HeightZone, HeightZoneType


class LivingAreaEngine:
    """Computes weighted living area according to height-zone factors."""

    def factor_for_zone_type(self, zone_type: HeightZoneType) -> float:
        """Return weighting factor for one height zone type."""
        if zone_type == HeightZoneType.UNDER_1M:
            return 0.0
        if zone_type == HeightZoneType.BETWEEN_1M_AND_2M:
            return 0.5
        return 1.0

    def calculate_living_area(self, zones: list[HeightZone]) -> float:
        """Calculate weighted living area from height zones in mm^2."""
        total = 0.0
        for zone in zones:
            total += self.calculate_zone_living_area(zone)
        return total

    def calculate_zone_living_area(self, zone: HeightZone) -> float:
        """Calculate weighted living area for a single zone in mm^2."""
        area = self._polygon_area(zone.polygon)
        return area * self.factor_for_zone_type(zone.zone_type)

    def _polygon_area(self, polygon: list[Point]) -> float:
        """Compute polygon area with shoelace formula in mm^2."""
        if len(polygon) < 3:
            return 0.0

        area = 0.0
        for index, point in enumerate(polygon):
            next_point = polygon[(index + 1) % len(polygon)]
            area += point.x * next_point.y
            area -= next_point.x * point.y

        return abs(area) * 0.5
