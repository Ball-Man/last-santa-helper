import desper
import pyglet_desper as pdesper
import pyglet
import pyglet.math as pmath
from pyglet.window import Window
from pyglet.sprite import Sprite
from pyglet.shapes import Line
from pyglet.gl import glClearColor

from . import constants
from . import graphics

# Setup main loop and window
interval = 1 / 60
loop = pdesper.Loop(interval)
desper.default_loop = loop
window = Window(960, 540)
loop.connect_window_events(window, 'on_draw', 'on_mouse_press', 'on_resize')


@desper.event_handler('on_draw')
class CameraProcessor(desper.Processor):

    def __init__(self):
        self.window = next(iter(pyglet.app.windows))

    def process(self, dt):
        pass

    def on_draw(self):
        self.window.clear()
        self.world.dispatch(pdesper.ON_CAMERA_DRAW_EVENT_NAME)


def world_transformer(handle, world: desper.World):
    main_batch = pdesper.retrieve_batch(world)

    # Rendering
    world.add_processor(CameraProcessor())
    world.create_entity(
        graphics.BlackBarsViewportHandler(constants.VIEW_W, constants.VIEW_H),
        pdesper.Camera(main_batch,
                       projection=pmath.Mat4.orthogonal_projection(0, 1920, 0, 1080, 0, 1)))

    # Layout
    world.create_entity(Line(0, constants.HORIZONTAL_MAIN_SEPARATOR_Y,
                             constants.VIEW_W, constants.HORIZONTAL_MAIN_SEPARATOR_Y,
                             batch=main_batch, color=constants.FG_COLOR,
                             width=constants.HORIZONTAL_MAIN_SEPARATOR_WIDTH))
    world.create_entity(Line(constants.VERTICAL_MAIN_SEPARATOR_X, 0,
                             constants.VERTICAL_MAIN_SEPARATOR_X,
                             constants.HORIZONTAL_MAIN_SEPARATOR_Y,
                             batch=main_batch, color=constants.FG_COLOR,
                             width=constants.HORIZONTAL_MAIN_SEPARATOR_WIDTH))

    world.create_entity(Sprite(desper.resource_map['image/test'],
                               batch=main_batch))


def main():
    glClearColor(*(constants.BG_COLOR / 255))

    pdesper.resource_populator(desper.resource_map, trim_extensions=True)

    handle = desper.WorldHandle()
    handle.transform_functions.append(pdesper.init_graphics_transformer)
    handle.transform_functions.append(world_transformer)
    loop.switch(handle)
    loop.loop()
