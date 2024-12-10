"""Main game logic and user interactions."""
from dataclasses import dataclass

import desper
import pyglet
from pyglet.math import Vec2, clamp
from pyglet.sprite import Sprite

from . import physics
from . import constants

MAX_MOUSE_INTERTIA_SPEED = 1000


@dataclass
class Item:
    """Represents an in game item."""
    base: bool = False
    hooked: int | None = None

    def contains(self, world: desper.World, ):
        """Check if chain of items contains the given id."""


def itemchain_contains(start_entity: int, target: int, world: desper.World) -> int:
    """Check if chain of items contains the given entity."""
    current_entity = start_entity
    while current_entity is not None:
        if current_entity == target:
            return True

        current_entity = world.get_component(current_entity, Item).hooked

    return False


@desper.event_handler('on_mouse_game_press', 'on_mouse_game_motion', 'on_mouse_game_release')
class ItemDragProcessor(desper.Processor):
    """When clicked, drag items."""
    dragged: desper.Controller | None = None
    offset: Vec2 = Vec2()
    last_delta: Vec2 = Vec2()
    last_dt: float = 1.
    _next_top_value: int = 1000

    def on_mouse_game_press(self, point: Vec2, buttons: int, mod):
        """Event: handle mouse."""
        if pyglet.window.mouse.LEFT & buttons:
            self.begin_drag(point)

    def on_mouse_game_release(self, point: Vec2, buttons: int, mod):
        """Event: handle mouse."""
        if pyglet.window.mouse.LEFT & buttons:
            self.end_drag()

    def on_mouse_game_motion(self, mouse_position: Vec2, delta: Vec2):
        """If something is being dragged, drag it."""
        if self.dragged is None:        # Nothing to drag
            return

        transform = self.dragged.get_component(desper.Transform2D)
        transform.position = desper.math.Vec2(*(mouse_position - self.offset))
        self.last_delta = delta

    def begin_drag(self, point: Vec2):
        """On mouse press, find intersecting items and grab one."""
        # TODO: pixel perfect check
        # Find top item
        top_item = None
        top_order = -1
        for item_entity, _ in self.world.get(Item):
            item_controller = desper.controller(item_entity, self.world)
            sprite: Sprite = item_controller.get_component(Sprite)
            if physics.point_collision(point, item_controller) and top_order < sprite.group.order:
                top_item = item_controller
                top_order = sprite.group.order

        if top_item is None:            # Nothing to drag
            return

        # Save current item and mouse offset for dragging
        self.dragged = top_item
        self.offset = point - top_item.get_component(desper.Transform2D).position
        top_item.remove_component(physics.Velocity)
        # Bring on top globally
        top_item.get_component(Sprite).group = pyglet.graphics.Group(self.get_next_top_value())

    def get_next_top_value(self) -> int:
        """Return next top z value and increase it."""
        next_value = self._next_top_value
        self._next_top_value += 1
        return next_value

    def end_drag(self):
        """If something is being dragged, release it."""
        if self.dragged is None:        # Nothing to release
            return

        # Handle item hooking
        hooked = False
        for entity, _ in self.world.get(physics.CollisionRectangle):
            if entity == self.dragged.entity:       # Don't self collide
                continue

            # Hook things that overlap, prevent hooking into a loop
            if (physics.rectangle_collision(self.dragged, desper.controller(entity, self.world))
                    and not itemchain_contains(entity, self.dragged.entity, self.world)):
                self.dragged.get_component(Item).hooked = entity
                hooked = True

        # Apply an eventual inertia from the mouse, if not hooked
        if not hooked and self.last_delta.mag > 0.5:
            self.dragged.add_component(physics.Velocity(*(self.last_delta / self.last_dt)
                                                        .limit(MAX_MOUSE_INTERTIA_SPEED)))

        self.dragged = None
        self.offset = Vec2()

    def process(self, dt: float):
        """Reset mouse delta and keep track of dt."""
        self.last_delta = Vec2()
        self.last_dt = clamp(dt, constants.MIN_DT, constants.MAX_DT)


def get_next_top_value(world: desper.World) -> int:
    """Retrieve next top value for items in world and increase it."""
    drag_processor = world.get_processor(ItemDragProcessor)
    return drag_processor.get_next_top_value()


class HookedProcessor(desper.Processor):
    """Process hooked items.

    Hooked items mirror their parent's positions. and should be on
    top of them.
    """

    def process(self, _):
        for entity, item in self.world.get(Item):
            if item.hooked is None:
                continue

            # Adjust position according to parent
            transform = self.world.get_component(entity, desper.Transform2D)
            parent_transform = self.world.get_component(item.hooked, desper.Transform2D)
            transform.position = parent_transform.position

            # Check ordering
            sprite = self.world.get_component(entity, Sprite)
            parent_sprite = self.world.get_component(item.hooked, Sprite)
            if sprite.group.order <= parent_sprite.group.order:
                sprite.group = pyglet.graphics.Group(get_next_top_value(self.world))
