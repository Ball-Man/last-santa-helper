"""Handle cameras and main graphical aspects of the game."""
import desper
import pyglet_desper as pdesper
import pyglet
from pyglet.window import Window
from typing import SupportsFloat


@desper.event_handler('on_draw')
class CameraProcessor(desper.Processor):

    def __init__(self):
        self.window = next(iter(pyglet.app.windows))

    def process(self, dt):
        pass

    def on_draw(self):
        self.window.clear()
        self.world.dispatch(pdesper.ON_CAMERA_DRAW_EVENT_NAME)


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


class SpriteSync(pdesper.SpriteSync):
    """Custom sprite sync with mild z support."""

    def on_position_change(self, new_position: desper.math.Vec2):
        """Event handler: update graphical component position.

        Ignore z.
        """
        sprite = self.get_component(self.component_type)
        sprite.position = (*new_position, sprite.z)


class LetterSize(desper.Controller):
    """Sync size of the underlying sprite according to text height."""
    sprite = desper.ComponentReference(pyglet.gui.NinePatch)
    label = desper.ComponentReference(pyglet.text.Label)

    def __init__(self, height_extra_offset: SupportsFloat = 100):
        self.height_extra_offset = height_extra_offset

    def on_add(self, *args):
        super().on_add(*args)
        self.sprite.height = self.label.content_height + self.height_extra_offset


class LetterPositionSync(pdesper.PositionSync2D):
    """Custom transform sync for letter objects (nine patch + label)."""
    sprite = desper.ComponentReference(pyglet.gui.NinePatch)
    label = desper.ComponentReference(pyglet.text.Label)

    def __init__(self, label_position_offset: tuple[SupportsFloat, SupportsFloat] = (25, 50)):
        super().__init__(None)

        self.label_position_offset = label_position_offset

    def on_position_change(self, new_position: desper.math.Vec2):
        sprite = self.sprite
        sprite.position = (*new_position, sprite.z)
        label = self.label
        label.position = (*(new_position + self.label_position_offset), label.z)
