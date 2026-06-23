from views.scene.drawing_scene import DrawingScene


class SceneFactory:
    """Creates drawing scene + initial configuration."""

    @staticmethod
    def create():
        scene = DrawingScene()

        # Default UI/graphics setup
        scene.setSceneRect(0, 0, 2000, 2000)

        return scene