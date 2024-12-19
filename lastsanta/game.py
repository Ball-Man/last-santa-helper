"""Main game world utilities."""
import random
from collections.abc import Iterable

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

LETTERS_RESOURCE_PATH = 'dial/letters'
TOYS_RESOURCE_PATH = 'image/toys'


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
        major_entity, major_gift = logic.find_major_gift(self.world)
        constraint_entity, constraint_container = gift_constraint_query[0]
        constraint: logic.Constraint = constraint_container.constraint

        self.world.delete_entity(constraint_entity)

        # Launch gift
        launch_gift(major_entity)

        self.world.dispatch('on_delivery', constraint.check(major_gift))


@desper.coroutine
def launch_gift(entity):
    """Launch given gift entity and delete it briefly after."""
    current_world = desper.default_loop.current_world
    # Remove collisions to make it go wooo, remove item to prevent dragging
    current_world.remove_component(entity, logic.Item)
    current_world.remove_component(entity, physics.CollisionRectangle)
    current_world.remove_component(entity, physics.Velocity)
    current_world.remove_component(entity, logic.GiftPart)
    current_world.add_component(entity, physics.Velocity(0, 1500.))
    # Make on top
    current_world.get_component(entity, Sprite).group = pyglet.graphics.Group(
        logic.get_next_top_value(current_world))
    yield 3
    current_world.delete_entity(entity)


@desper.event_handler('on_update')
class Slider(desper.Controller):
    """Move object in and out of the scene."""
    transform = desper.ComponentReference(desper.Transform2D)

    def __init__(self, target_x=1200, transition_time=1.):
        self.target_x = target_x
        self.dt = 1.
        self.transition_time = transition_time

    def on_add(self, *args):
        super().on_add(*args)
        self.start_pos = self.transform.position.x

    def on_update(self, dt):
        self.dt = pmath.clamp(dt, constants.MIN_DT, constants.MAX_DT)

    def lerp_to_target(self, target_x):
        """Generator, can be used as coroutien to lerp to a target."""
        target_vec = desper.math.Vec2(target_x, self.transform.position.y)

        t = 0
        speed = 1 / self.transition_time
        while t < 0.99:
            t = min(1., t + self.dt * speed)
            self.transform.position = self.transform.position.lerp(target_vec, t)
            yield

    @desper.coroutine
    def slide_in(self):
        yield from self._lerp_to_target(self.target_x)          # Transition in

    @desper.coroutine
    def slide_out(self):
        yield from self._lerp_to_target(self.start_pos)              # Transition out


@desper.event_handler('on_delivery')
class TheHandler(desper.Controller):
    """Slide the handler in and out of the scene."""
    slider = desper.ComponentReference(Slider)

    @desper.coroutine
    def on_delivery(self, *args):
        yield from self.slider.lerp_to_target(self.slider.target_x)

        # Wait a sec. Here, some other component shall switch to the
        # dialogue or whatever.
        yield 2

        yield from self.slider.lerp_to_target(self.slider.start_pos)


@desper.event_handler('on_delivery')
class TheLetter(desper.Controller):
    """Slide the letter in and out of the scene."""
    slider = desper.ComponentReference(Slider)

    def on_add(self, *args):
        """Slide in as soon as created."""
        super().on_add(*args)
        self.slide_in()

    @desper.coroutine
    def slide_in(self, *args):
        """Wait a second and slide in."""
        yield 1
        yield from self.slider.lerp_to_target(self.slider.target_x)

    @desper.coroutine
    def on_delivery(self, *args):
        """On delivery event, slide out."""
        yield from self.slider.lerp_to_target(self.slider.start_pos)


@desper.event_handler('on_delivery')
class DialogueManager:
    """Continue dialogue on delivery."""

    def __init__(self, dialogue: Dialogue, transition_time=2.):
        self.dialogue = dialogue
        self.transition_time = transition_time

    @desper.coroutine
    def on_delivery(self, constraint_check):
        """Wait a bit and continue."""
        self.dialogue.variables[dialogue.ERRORS_VAR] = 0
        if constraint_check:
            self.dialogue.variables[dialogue.ERRORS_VAR] = constraint_check[0]

        yield self.transition_time
        dialogue.continue_dialogue(self.dialogue)


class GiftPartProto(desper.Prototype):
    """Prototype for gift parts.

    Gift part category and sprite are selected automatically based on
    the given name.
    """
    component_types = (Sprite, desper.Transform2D, pdesper.SpriteSync, physics.BBox, logic.Item,
                       logic.GiftPart)

    def __init__(self, x, y, sprite_name: str, batch: pyglet.graphics.Batch,
                 group: pyglet.graphics.Group | None = None, z=0):
        self.x = x
        self.y = y
        self.z = z
        self.sprite_name = sprite_name
        self.batch = batch
        self.group = group

    def init_Sprite(self, component_type):
        return component_type(desper.resource_map[TOYS_RESOURCE_PATH][self.sprite_name],
                              z=self.z,
                              subpixel=True, batch=self.batch, group=self.group)

    def init_Transform2D(self, component_type):
        return component_type((self.x, self.y))

    def init_GiftPart(self, component_type):
        return component_type(self.sprite_name)


class MainGameTransformer:
    """Populate a game level."""

    def __init__(self, story_dialogue: Dialogue, plausible_parts: Iterable[str],
                 number_of_generated: int = 50):
        self.story_dialogue = story_dialogue
        self.plausible_parts = plausible_parts
        self.number_of_generated = number_of_generated

    def __call__(self, handle, world: desper.World):
        main_batch = pdesper.retrieve_batch(world)

        # General control
        world.add_processor(desper.OnUpdateProcessor())
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
                                 width=constants.HORIZONTAL_MAIN_SEPARATOR_WIDTH,
                                 group=pyglet.graphics.Group(-100)),
                            physics.CollisionAxes(constants.HORIZONTAL_MAIN_SEPARATOR_Y, 1))
        world.create_entity(Line(constants.VERTICAL_MAIN_SEPARATOR_X, 0,
                                 constants.VERTICAL_MAIN_SEPARATOR_X,
                                 constants.HORIZONTAL_MAIN_SEPARATOR_Y,
                                 batch=main_batch, color=constants.FG_COLOR,
                                 width=constants.HORIZONTAL_MAIN_SEPARATOR_WIDTH,
                                 group=pyglet.graphics.Group(-100)),
                            physics.CollisionAxes(constants.VERTICAL_MAIN_SEPARATOR_X, 0))

        # Handler coming in and out
        world.create_entity(Sprite(desper.resource_map['image/handler'], batch=main_batch),
                            desper.Transform2D((constants.VIEW_W + 400,
                                                constants.HORIZONTAL_MAIN_SEPARATOR_Y)),
                            pdesper.SpriteSync(),
                            Slider(),
                            TheHandler())

        # Delivery button
        world.create_entity(Sprite(desper.resource_map['image/delivery'], batch=main_batch),
                            desper.Transform2D((300, constants.VIEW_H - 200)),
                            pdesper.SpriteSync(),
                            physics.BBox(),
                            DeliveryButton())

        world.create_entity(DialogueManager(self.story_dialogue))

        # Objects
        for index in range(self.number_of_generated):
            # Sample part name and position
            part_name = random.choice(self.plausible_parts)
            part_image = desper.resource_map[TOYS_RESOURCE_PATH][part_name]
            x = random.uniform(constants.VERTICAL_MAIN_SEPARATOR_X + 10,
                               constants.VIEW_W - part_image.width - 10)
            y = random.uniform(10,
                               constants.HORIZONTAL_MAIN_SEPARATOR_Y - part_image.height - 200)
            world.create_entity(*GiftPartProto(x, y, part_name,
                                               batch=main_batch,
                                               group=pyglet.graphics.Group(index + 10)))

        # Add borders to the whole view
        world.create_entity(physics.CollisionAxes(0., 1))                       # Horizontal zero
        world.create_entity(physics.CollisionAxes(0., 0))                       # Vertical zero
        world.create_entity(physics.CollisionAxes(constants.VIEW_W, 0))         # Vertical right

        if __debug__:
            world.create_entity(physics.PointCheckDebug())


class GiftTransformer:
    """Add given gift constraint to the world + add some items."""

    def __init__(self, gift_constraint):
        self.gift_constraint = gift_constraint

    def __call__(self, _, world: desper.World):
        main_batch = pdesper.retrieve_batch(world)

        # Game elements and logic
        world.create_entity(logic.GiftConstraint(self.gift_constraint))

        # Find missing items for the constriant and create some of them
        # to make sure it is satisfiable.
        full_gift = [gift_part for _, gift_part in world.get(logic.GiftPart)]

        for reason_constraint in self.gift_constraint.check(full_gift)[1]:
            if type(reason_constraint) is logic.ItemSetConstraint:
                for _ in range(reason_constraint.count):
                    # Sample part name and position
                    part_name = random.choice(tuple(reason_constraint.allowed_set))
                    part_image = desper.resource_map[TOYS_RESOURCE_PATH][part_name]
                    x = random.uniform(constants.VERTICAL_MAIN_SEPARATOR_X + 10,
                                       constants.VIEW_W - part_image.width - 10)
                    y = random.uniform(10,
                                       constants.HORIZONTAL_MAIN_SEPARATOR_Y
                                       - part_image.height - 200)
                    group_order = logic.get_next_top_value(world)
                    world.create_entity(
                        *GiftPartProto(x, y, part_name,
                                       batch=main_batch,
                                       group=pyglet.graphics.Group(group_order)))


class LetterTransformer:
    """ """

    def __init__(self, letter_name: str, font_name: str, variables):
        self.letter_name = letter_name
        self.font_name = font_name
        self.variables = variables

    def __call__(self, _, world: desper.World):
        main_batch = pdesper.retrieve_batch(world)

        # Remove previously existing letters to prevent weird overlaps
        for old_letter_entity, _ in world.get(TheLetter):
            world.delete_entity(old_letter_entity)

        letter_dialogue_data = desper.resource_map[LETTERS_RESOURCE_PATH][self.letter_name]
        letter_text = Dialogue(letter_dialogue_data).next().parse_text(
            dialogue.LANG_ITA, self.variables)
        letter_image = desper.resource_map['image/letter']
        world.create_entity(
            desper.Transform2D((-letter_image.width - 50, 20)),
            NinePatch(letter_image,
                      width=letter_image.width, height=letter_image.height,
                      batch=main_batch, group=pyglet.graphics.Group(-10)),
            pyglet.text.Label(letter_text,
                              x=25, y=50,
                              anchor_y='bottom',
                              multiline=True,
                              width=letter_image.width - 50,
                              font_name=self.font_name, batch=main_batch,
                              font_size=20, color=constants.FG_COLOR),
            graphics.LetterSize(),
            graphics.LetterPositionSync(),
            Slider(20),
            TheLetter())
