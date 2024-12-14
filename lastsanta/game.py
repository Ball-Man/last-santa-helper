"""Main game world utilities."""
import desper
import pyglet_desper as pdesper
import pyglet
import pyglet.math as pmath
from pyglet.shapes import Line
from pyglet.sprite import Sprite
from pyglet.gui import NinePatch

from . import graphics
from . import logic
from . import constants
from . import physics


def world_transformer(handle, world: desper.World):
    main_batch = pdesper.retrieve_batch(world)

    # General control
    world.add_processor(logic.ItemDragProcessor())
    world.create_entity(physics.MouseToGameSpace())

    # Rendering
    world.add_processor(graphics.CameraProcessor())
    world.create_entity(
        graphics.BlackBarsViewportHandler(constants.VIEW_W, constants.VIEW_H),
        pdesper.Camera(main_batch,
                       projection=pmath.Mat4.orthogonal_projection(0, 1920, 0, 1080, 0, 1)))

    # Physics
    world.add_processor(physics.RectangleToAxisProcessor())
    world.add_processor(physics.VelocityProcessor())
    world.add_processor(logic.HookedProcessor())

    # Layout
    world.create_entity(Line(0, constants.HORIZONTAL_MAIN_SEPARATOR_Y,
                             constants.VIEW_W, constants.HORIZONTAL_MAIN_SEPARATOR_Y,
                             batch=main_batch, color=constants.FG_COLOR,
                             width=constants.HORIZONTAL_MAIN_SEPARATOR_WIDTH),
                        physics.CollisionAxes(constants.HORIZONTAL_MAIN_SEPARATOR_Y, 1))
    world.create_entity(Line(constants.VERTICAL_MAIN_SEPARATOR_X, 0,
                             constants.VERTICAL_MAIN_SEPARATOR_X,
                             constants.HORIZONTAL_MAIN_SEPARATOR_Y,
                             batch=main_batch, color=constants.FG_COLOR,
                             width=constants.HORIZONTAL_MAIN_SEPARATOR_WIDTH),
                        physics.CollisionAxes(constants.VERTICAL_MAIN_SEPARATOR_X, 0))

    world.create_entity(Sprite(desper.resource_map['image/toys/lightbulb'], subpixel=True,
                               batch=main_batch, group=pyglet.graphics.Group(1)),
                        desper.Transform2D((1500., 500.)),
                        pdesper.SpriteSync(),
                        physics.BBox(),
                        physics.Velocity(-300, -300),
                        logic.Item(),
                        logic.GiftPart('lightbulb'))

    world.create_entity(Sprite(desper.resource_map['image/toys/base1'], subpixel=True,
                               batch=main_batch, group=pyglet.graphics.Group(0)),
                        desper.Transform2D((1600., 300.)),
                        pdesper.SpriteSync(),
                        physics.BBox(),
                        logic.Item(),
                        logic.GiftPart('base'))

    letter_image = desper.resource_map['image/letter']
    world.create_entity(
        desper.Transform2D(),
        physics.Velocity(300),
        NinePatch(letter_image,
                  width=letter_image.width, height=letter_image.height,
                  batch=main_batch, group=pyglet.graphics.Group(-10)),
        pyglet.text.Label('This is super shape, take this and that, tell me more, and more. ' * 6,
                          x=25, y=50,
                          anchor_y='bottom',
                          multiline=True,
                          width=letter_image.width - 50,
                          font_name='Super Shape', batch=main_batch,
                          font_size=20, color=constants.FG_COLOR),
        graphics.LetterSize(),
        graphics.LetterPositionSync())

    # Add borders to the whole view
    world.create_entity(physics.CollisionAxes(0., 1))                       # Horizontal zero
    world.create_entity(physics.CollisionAxes(0., 0))                       # Vertical zero
    world.create_entity(physics.CollisionAxes(constants.VIEW_W, 0))         # Vertical right

    if __debug__:
        world.create_entity(physics.PointCheckDebug())
