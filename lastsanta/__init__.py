import sys
from pathlib import Path

import desper
import pyglet_desper as pdesper
from pyglet.window import Window
from pyglet.gl import glClearColor
from ddesigner import Dialogue

from . import constants
from . import dialogue

# Setup main loop and window
interval = 1 / 60
loop = pdesper.Loop(interval)
desper.default_loop = loop
window = Window(960, 540)
loop.connect_window_events(window, 'on_draw', 'on_mouse_press', 'on_mouse_release', 'on_resize',
                           'on_mouse_motion', 'on_mouse_drag', 'on_key_press')


def main():
    glClearColor(*(constants.BG_COLOR / 255))

    # Change root of resources if the app is frozen
    if getattr(sys, 'frozen', False):
        # The application is frozen
        pdesper.resource_populator.root = str(Path(sys.executable).parent / 'resources')

    pdesper.resource_populator.add_rule(constants.DIAL_RESOURCES_PATH, dialogue.DialogueHandle)
    pdesper.resource_populator(desper.resource_map, trim_extensions=True)

    # Load fonts
    for font_handle in desper.resource_map['font'].handles:
        desper.resource_map['font'][font_handle]

    dialogue.continue_dialogue(Dialogue(desper.resource_map['dial/story']), loop.switch)
    loop.loop()
