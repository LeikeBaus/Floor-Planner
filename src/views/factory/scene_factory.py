from views.scene.drawing_scene import DrawingScene


class SceneFactory:
    """Creates drawing scene + initial configuration."""

    @staticmethod
    def create():
        scene = DrawingScene()

        # Keep a large centered world so scroll/pan remains available at low zoom.
        scene.setSceneRect(-50000.0, -50000.0, 100000.0, 100000.0)

        return scene