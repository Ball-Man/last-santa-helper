import desper
import pyglet_desper as pdesper
from ddesigner import from_file, DialogueData, Dialogue
from ddesigner.default_model import ShowMessageNode, WaitNode
from pyglet.text import Label
from pyglet.math import Mat4

from . import constants
from . import physics
from . import graphics
from . import game
from . import gifts

LANG_ITA = 'ITA'
GIFT_NAME_DIALOGUE_VAR = 'gift_name'
LETTER_NAME_DIALOGUE_VAR = 'letter_name'
BACK_DIALOGUE_VAR = 'back'


class DialogueHandle(desper.Handle[DialogueData]):
    """Handle for dialogue resources."""

    def __init__(self, filename):
        self.filename = filename

    def load(self) -> DialogueData:
        with open(self.filename) as fin:
            return from_file(fin)


def continue_dialogue(dialogue: Dialogue, switch_function=desper.switch, language=LANG_ITA):
    """Get next dialogue node, build a world accoringly and switch.

    TODO
    """
    stop = False
    while not stop:
        new_node = dialogue.next()

        match new_node:
            case None:
                print('End of dialogue file, what do we do?')
                stop = True

            # If it's a dialogue line, build a new world handle and
            # switch to it.
            case ShowMessageNode():
                # Keep track of game world handle
                current_world = desper.default_loop.current_world
                passthrough_handle = None
                if current_world is not None:
                    _, passthrough_handle = current_world.get(desper.WorldHandle)[0]

                new_handle = desper.WorldHandle()
                new_handle.transform_functions.append(pdesper.init_graphics_transformer)
                new_handle.transform_functions.append(
                    DialogueWorldTransformer(new_node.text.get(language, '-- no text')))
                new_handle.transform_functions.append(
                    DialogueMachineTransfomer(dialogue, passthrough_handle))
                switch_function(new_handle)
                stop = True

            # On wait, get back to new game
            case WaitNode():
                # Retrieve metadata for game world
                gift = gifts.gifts[dialogue[GIFT_NAME_DIALOGUE_VAR]]
                go_back = dialogue[BACK_DIALOGUE_VAR]
                letter_name = dialogue[LETTER_NAME_DIALOGUE_VAR]

                # Find set of gifts that may be generated
                normal_items = set(desper.resource_map[game.TOYS_RESOURCE_PATH]
                                         .handles.keys()).difference(gifts.CRITICAL_ITEMS)

                # Get back to the previous world vs create a new one
                current_world = desper.default_loop.current_world
                handle = desper.WorldHandle()
                if go_back and current_world is not None:
                    _, handle = current_world.get(desper.WorldHandle)[0]
                    # Apply gift and letter transformer directly
                    game.GiftTransformer(gift)(handle, handle())
                    game.LetterTransformer(letter_name, dialogue.variables)(handle, handle())
                    pass

                # New world, build from scratch
                else:
                    handle.transform_functions.append(pdesper.init_graphics_transformer)
                    handle.transform_functions.append(
                        game.MainGameTransformer(dialogue, tuple(normal_items)))
                    handle.transform_functions.append(game.GiftTransformer(gift))
                    handle.transform_functions.append(game.LetterTransformer(letter_name,
                                                                             dialogue.variables))

                switch_function(handle)
                stop = True


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

    def __init__(self, dialogue: Dialogue, previous: desper.WorldHandle):
        self.dialogue = dialogue
        self.previous = previous

    def __call__(self, _, world: desper.World):
        world.create_entity(physics.MouseToGameSpace())
        world.create_entity(DialogueTriggerOnClick(self.dialogue))
        world.create_entity(self.previous)
