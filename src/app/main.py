"""Application entrypoint for FloorPlanner."""

from __future__ import annotations

from app.application import FloorPlannerApplication


def main() -> int:
    """Run the application and return the process exit code."""
    return FloorPlannerApplication().run()


if __name__ == "__main__":
    raise SystemExit(main())