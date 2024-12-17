"""Tools for hotkeys that handle user preferences."""
import desper
import pyglet.window.key as key

import lastsanta


@desper.event_handler('on_key_press')
class ToggleFullscreen:
    """On F, toggle fullscreen."""

    def on_key_press(self, code, mod):
        if code == key.F:
            lastsanta.window.set_fullscreen(not lastsanta.window.fullscreen)


@desper.event_handler('on_key_press')
class QuitGame:
    """On ESC, quit."""

    def on_key_press(self, code, mod):
        if code == key.ESCAPE:
            lastsanta.window.close()


def hotkeys_transformer(_, world: desper.World):
    """Add to the world hotkey event handlers."""
    world.create_entity(ToggleFullscreen(), QuitGame())
