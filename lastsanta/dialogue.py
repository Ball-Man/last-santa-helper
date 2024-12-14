import desper
import pyglet_desper as pdesper
from ddesigner import from_file, DialogueData
from pyglet.text import Label
from pyglet.math import Mat4

from . import constants
from . import physics
from . import graphics


class DialogueHandle(desper.Handle[DialogueData]):
    """Handle for dialogue resources."""

    def __init__(self, filename):
        self.filename = filename

    def load(self) -> DialogueData:
        with open(self.filename) as fin:
            return from_file(fin)


class DialogueWorldTransformer:
    """Populate world with a dialogue line."""

    def __init__(self, text: str, font_name='Mechanical', font_size=50):
        self.text = text
        self.font_name = font_name
        self.font_size = font_size

    def __call__(self, _, world: desper.World):
        main_batch = pdesper.retrieve_batch(world)

        # General control
        world.create_entity(physics.MouseToGameSpace())

        # Rendering
        world.add_processor(graphics.CameraProcessor())
        world.create_entity(
            graphics.BlackBarsViewportHandler(constants.VIEW_W, constants.VIEW_H),
            pdesper.Camera(main_batch,
                           projection=Mat4.orthogonal_projection(0, 1920, 0, 1080, 0, 1)))

        world.create_entity(Label(self.text, x=100, y=100, width=constants.VIEW_W - 100,
                                  multiline=True, anchor_y='bottom',
                                  color=constants.FG_COLOR, font_name=self.font_name,
                                  font_size=self.font_size, batch=main_batch))
