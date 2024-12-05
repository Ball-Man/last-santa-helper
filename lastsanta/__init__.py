import desper
import pyglet_desper as pdesper
import pyglet
import pyglet.math as pmath
from pyglet.window import Window
from pyglet.sprite import Sprite

# Setup main loop and window
interval = 1 / 60
loop = pdesper.Loop(interval)
desper.default_loop = loop
window = Window(960, 540)
loop.connect_window_events(window, 'on_draw', 'on_mouse_press')


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
    world.add_processor(CameraProcessor())

    world.create_entity(
        pdesper.Camera(pdesper.retrieve_batch(world),
                       projection=pmath.Mat4.orthogonal_projection(0, 1920, 0, 1080, 0, 1)))

    world.create_entity(Sprite(desper.resource_map['image/test'],
                               batch=pdesper.retrieve_batch(world)))


def main():
    pdesper.resource_populator(desper.resource_map, trim_extensions=True)

    handle = desper.WorldHandle()
    handle.transform_functions.append(pdesper.init_graphics_transformer)
    handle.transform_functions.append(world_transformer)
    loop.switch(handle)
    loop.loop()
