import desper
import pyglet_desper as pdesper
from ddesigner import from_file, DialogueData, Dialogue
from ddesigner.default_model import ShowMessageNode, WaitNode
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


def continue_dialogue(dialogue: Dialogue):
    """Get next dialogue node, build a world accoringly and switch.

    TODO
    """
    new_node = dialogue.next()

    match new_node:
        case None:
            print('End of dialogue file, what do we do?')

        case ShowMessageNode():
            print('Show message')

        case WaitNode():
            print('Wait node')


@desper.event_handler('on_mouse_game_press')
class DialogueTriggerOnClick:
    """On click, continue dialogue."""

    def __init__(self, dialogue: Dialogue):
        self.dialogue = dialogue

    def on_mouse_game_press(self, *args, **kwargs):
        """Ignore all params, any click works."""
        continue_dialogue(self.dialogue)


class DialogueWorldTransformer:
    """Populate world with a dialogue line."""

    def __init__(self, text: str, font_name='Mechanical', font_size=50):
        self.text = text
        self.font_name = font_name
        self.font_size = font_size

    def __call__(self, _, world: desper.World):
        main_batch = pdesper.retrieve_batch(world)

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


class DialogueMachineTransfomer:
    """Given a dialogue state machine, add logic to transition forward."""

    def __init__(self, dialogue: Dialogue):
        self.dialogue = dialogue

    def __call__(self, _, world: desper.World):
        world.create_entity(physics.MouseToGameSpace())
        world.create_entity(DialogueTriggerOnClick(self.dialogue))
