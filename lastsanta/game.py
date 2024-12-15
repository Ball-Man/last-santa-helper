"""Main game world utilities."""
import desper
import pyglet_desper as pdesper
import pyglet
import pyglet.math as pmath
from pyglet.shapes import Line
from pyglet.sprite import Sprite
from pyglet.gui import NinePatch
from ddesigner import Dialogue

from . import graphics
from . import logic
from . import constants
from . import physics
from . import dialogue


@desper.event_handler('on_mouse_game_press')
class DeliveryButton(desper.Controller):
    """If clicked, deliver gift and progress game."""
    # collision_rectangle = desper.ComponentReference(physics.CollisionRectangle)

    def on_mouse_game_press(self, point: pmath.Vec2, buttons, *args):
        if buttons & pyglet.window.mouse.LEFT and physics.point_collision(point, self):
            self.deliver()

    def deliver(self):
        """Retrieve and deliver, major gift, check conformity."""
        # Don't do anything if there is not current order
        gift_constraint_query = self.world.get(logic.GiftConstraint)
        if not gift_constraint_query:
            return

        # Retrive gift and constraint
        major_gift = logic.find_major_gift(self.world)
        constraint_entity, constraint_container = gift_constraint_query[0]
        constraint: logic.Constraint = constraint_container.constraint

        self.world.delete_entity(constraint_entity)

        self.world.dispatch('on_delivery', constraint.check(major_gift))


@desper.event_handler('on_delivery', 'on_update')
class TheHandler(desper.Controller):
    """Move the handler in and out of the scene."""
    transform = desper.ComponentReference(desper.Transform2D)

    def __init__(self, target_x=1200, transition_time=1.):
        self.target_x = target_x
        self.dt = 1.
        self.transition_time = transition_time

    def on_update(self, dt):
        self.dt = pmath.clamp(dt, constants.MIN_DT, constants.MAX_DT)

    def _lerp_to_target(self, target_x):
        """Generator, can be used as coroutien to lerp to a target."""
        target_vec = desper.math.Vec2(target_x, self.transform.position.y)

        t = 0
        speed = 1 / self.transition_time
        while t < 0.99:
            t = min(1., t + self.dt * speed)
            self.transform.position = self.transform.position.lerp(target_vec, t)
            yield

    @desper.coroutine
    def on_delivery(self, *args):
        # A bit funky, we need dt somehow
        self.world.add_processor(desper.OnUpdateProcessor(), -1)
        start_pos = self.transform.position.x
        yield 0.1

        yield from self._lerp_to_target(self.target_x)          # Transition in
        # Wait a sec. Here, some other component shall switch to the
        # dialogue or whatever.
        yield 2
        yield from self._lerp_to_target(start_pos)              # Transition out


@desper.event_handler('on_delivery')
class DialogueManager:
    """Continue dialogue on delivery."""

    def __init__(self, dialogue: Dialogue, transition_time=2.):
        self.dialogue = dialogue
        self.transition_time = transition_time

    @desper.coroutine
    def on_delivery(self, *args):
        """Wait a bit and continue."""
        yield self.transition_time
        dialogue.continue_dialogue(self.dialogue)


class MainGameTransformer:
    """Populate a game level."""

    def __init__(self, story_dialogue: Dialogue):
        self.story_dialogue = story_dialogue

    def __call__(self, handle, world: desper.World):
        main_batch = pdesper.retrieve_batch(world)

        # General control
        world.add_processor(desper.CoroutineProcessor())
        world.add_processor(logic.ItemDragProcessor())
        world.create_entity(physics.MouseToGameSpace())
        # Add self handle as an entity, used later for retrieval
        world.create_entity(handle)

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

        # Handler coming in and out
        world.create_entity(Sprite(desper.resource_map['image/toys/base1'], batch=main_batch),
                            desper.Transform2D((constants.VIEW_W + 400,
                                                constants.HORIZONTAL_MAIN_SEPARATOR_Y)),
                            pdesper.SpriteSync(),
                            TheHandler())

        # Delivery button
        world.create_entity(Sprite(desper.resource_map['image/toys/base1'], batch=main_batch),
                            desper.Transform2D((300, constants.VIEW_H - 200)),
                            pdesper.SpriteSync(),
                            physics.BBox(),
                            DeliveryButton())

        world.create_entity(DialogueManager(self.story_dialogue))

        # Objects
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
                            logic.GiftPart('base1'))

        letter_image = desper.resource_map['image/letter']
        world.create_entity(
            desper.Transform2D(),
            physics.Velocity(300),
            NinePatch(letter_image,
                      width=letter_image.width, height=letter_image.height,
                      batch=main_batch, group=pyglet.graphics.Group(-10)),
            pyglet.text.Label('This is super shape. ' * 12,
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


class GiftTransformer:
    """Add given gift constraint to the world + TODO: some items."""

    def __init__(self, gift_constraint):
        self.gift_constraint = gift_constraint

    def __call__(self, _, world: desper.World):
        # Game elements and logic
        world.create_entity(logic.GiftConstraint(self.gift_constraint))
