"""Handle cameras and main graphical aspects of the game."""
import desper
import pyglet_desper as pdesper
import pyglet
from pyglet.window import Window


@desper.event_handler('on_resize')
class BlackBarsViewportHandler(desper.Controller):
    """On window resize, rescale and center camera's viewport.

    Aspect ratio is kept, if the window size does not match the game's
    one, black bars are shown.
    """
    camera = desper.ComponentReference(pdesper.Camera)

    def __init__(self, view_w, view_h):
        self.view_w = view_w
        self.view_h = view_h
        self.game_ratio = view_w / view_h
        self.window: Window = next(iter(pyglet.app.windows))

    def on_resize(self, new_width, new_height):
        """Event handler: window resized."""
        new_window_ratio = new_width / new_height

        # Black bars are horizontal
        if new_window_ratio >= self.game_ratio:
            actual_width = new_height * self.game_ratio
            self.camera.viewport = ((new_width - actual_width) / 2, 0, actual_width, new_height)

        # Black bars are vertical
        if new_window_ratio <= self.game_ratio:
            actual_height = new_width / self.game_ratio
            self.camera.viewport = (0, (new_height - actual_height) / 2, new_width, actual_height)
