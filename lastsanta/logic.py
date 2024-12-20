"""Main game logic and user interactions."""
import operator
from dataclasses import dataclass, field
from collections.abc import Collection
from typing import Any

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
    hook_offset: Vec2 = field(default_factory=Vec2)

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


def find_root(start_entity: int, world: desper.World) -> int:
    """Find root entity of a chain."""
    last_entity = start_entity
    current_entity = start_entity
    while current_entity is not None:
        last_entity = current_entity
        current_entity = world.get_component(current_entity, Item).hooked

    return last_entity


@desper.event_handler('on_mouse_game_press', 'on_mouse_game_motion', 'on_mouse_game_release')
class ItemDragProcessor(desper.Processor):
    """When clicked, drag items."""
    dragged: desper.Controller | None = None
    offset: Vec2 = Vec2()
    last_delta: Vec2 = Vec2()
    last_dt: float = 1.
    pickup_position = desper.math.Vec2()
    _next_top_value: int = 1000

    def on_mouse_game_press(self, point: Vec2, buttons: int, mod):
        """Event: handle mouse."""
        during_drag = self.dragged is not None

        # On left button, if during a grab, attach object,
        # if not during a grab, grab entire composite objects
        if pyglet.window.mouse.LEFT & buttons:
            if during_drag:
                self.end_drag()
            else:
                self.begin_drag_chain(point)
        # On right button, if during a grab, attach object.
        # If not during a grab, grab a single part.
        elif pyglet.window.mouse.RIGHT & buttons:
            if during_drag:
                self.end_drag()
            else:
                self.begin_drag(point)

    def on_mouse_game_release(self, point: Vec2, buttons: int, mod):
        """Event: handle mouse."""
        if (pyglet.window.mouse.LEFT | pyglet.window.mouse.RIGHT) & buttons:
            self.end_drag(to_hook=False)

    def on_mouse_game_motion(self, mouse_position: Vec2, delta: Vec2):
        """If something is being dragged, drag it."""
        if self.dragged is None:        # Nothing to drag
            return

        transform = self.dragged.get_component(desper.Transform2D)
        transform.position = desper.math.Vec2(*(mouse_position - self.offset))
        self.last_delta = delta

    def find_drag(self, point: Vec2) -> desper.Controller | None:
        """Given a point, find an item to grab."""
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

        return top_item

    def begin_drag(self, point: Vec2):
        """On mouse press, find intersecting items and grab one."""
        top_item = self.find_drag(point)
        if top_item is None:            # Nothing to grab
            return

        self.world.dispatch('on_pickup')

        # Save current item and mouse offset for dragging
        self.dragged = top_item
        self.pickup_position = top_item.get_component(desper.Transform2D).position
        self.offset = point - self.pickup_position
        top_item.remove_component(physics.Velocity)

        top_item.get_component(Item).hooked = None          # Unhook

        # Bring on top globally
        top_item.get_component(Sprite).group = pyglet.graphics.Group(self.get_next_top_value())

    def begin_drag_chain(self, point: Vec2):
        """On mouse press, find intersecting items and grab one.

        If the intersecting object is part of a chain, the entire
        composite object will be moved (the root is grabbed).
        """
        top_item = self.find_drag(point)
        if top_item is None:            # Nothing to grab
            return

        self.world.dispatch('on_pickup')

        # Save current item and mouse offset for dragging
        top_item = desper.controller(find_root(top_item.entity, top_item.world), top_item.world)
        self.dragged = top_item
        self.pickup_position = top_item.get_component(desper.Transform2D).position
        self.offset = point - self.pickup_position
        top_item.remove_component(physics.Velocity)

        # Bring on top globally
        top_item.get_component(Sprite).group = pyglet.graphics.Group(self.get_next_top_value())

    def get_next_top_value(self) -> int:
        """Return next top z value and increase it."""
        next_value = self._next_top_value
        self._next_top_value += 1
        return next_value

    def end_drag(self, to_hook=True):
        """If something is being dragged, release it."""
        if self.dragged is None:        # Nothing to release
            return

        dragged_transformed = self.dragged.get_component(desper.Transform2D)
        dragged_position = dragged_transformed.position

        # If colliding with some axis, snap back to original position
        snap = False
        for _, axis in self.world.get(physics.CollisionAxes):
            snap |= physics.axis_collision(axis.pos, axis.index, self.dragged)

        # HARDCODE: also snap if item is above the layout or outside view
        snap |= (dragged_position.y >= constants.HORIZONTAL_MAIN_SEPARATOR_Y
                 or dragged_position.y < 0 or dragged_position.x > constants.VIEW_W
                 or dragged_position.x < 0)

        if snap:
            self.world.dispatch('on_drop')
            dragged_transformed.position = self.pickup_position

            # Cleanup
            self.dragged = None
            self.offset = Vec2()
            return

        # Handle item hooking
        hooked = False
        dragged_item = self.dragged.get_component(Item)
        for entity, _ in self.world.get(physics.CollisionRectangle):
            if entity == self.dragged.entity:       # Don't self collide
                continue

            # Hook things that overlap, prevent hooking into a loop
            if (to_hook
                and physics.rectangle_collision(self.dragged,
                                                desper.controller(entity, self.world))
                    and not itemchain_contains(entity, self.dragged.entity, self.world)):
                dragged_item.hooked = entity
                dragged_item.hook_offset = (self.world.get_component(entity,
                                                                     desper.Transform2D).position
                                            - dragged_position)
                hooked = True

        # Apply an eventual inertia from the mouse, if not hooked
        if not hooked and self.last_delta.mag > 0.5:
            self.dragged.add_component(physics.Velocity(*(self.last_delta / self.last_dt)
                                                        .limit(MAX_MOUSE_INTERTIA_SPEED)))

        if hooked:
            self.world.dispatch('on_hook')
        else:
            self.world.dispatch('on_drop')

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

            # Delete entities part of a non-existing chain
            if not self.world.entity_exists(item.hooked):
                self.world.delete_entity(entity)
                continue

            # Adjust position according to parent
            transform = self.world.get_component(entity, desper.Transform2D)

            parent_transform = self.world.get_component(item.hooked, desper.Transform2D)
            parent_gift_part = self.world.get_component(item.hooked, GiftPart)
            transform.position = parent_transform.position - item.hook_offset

            # If parent has no gift part, remove part as well
            if parent_gift_part is None:
                self.world.remove_component(entity, GiftPart)

            # Check ordering
            sprite = self.world.get_component(entity, Sprite)
            parent_sprite = self.world.get_component(item.hooked, Sprite)
            if sprite.group.order <= parent_sprite.group.order:
                sprite.group = pyglet.graphics.Group(get_next_top_value(self.world))


@dataclass(frozen=True)
class GiftPart:
    """Represent a gift part."""
    name: str


def find_major_gift(world: desper.World) -> tuple[int, list[GiftPart]]:
    """Return the major gift from the world."""
    # Build all gifts in the scene
    gifts = {}
    explored = set()
    for entity, item in world.get(Item):
        if entity in explored:
            continue

        # Populate candidate gift
        last_entity = entity
        current_entity = entity
        current_chain = []
        while current_entity is not None:
            last_entity = current_entity
            # Don't add parts more than once
            if current_entity not in explored:
                current_chain.append(world.get_component(current_entity, GiftPart))
                explored.add(current_entity)
            current_entity = world.get_component(current_entity, Item).hooked

        gifts.setdefault(last_entity, [])
        gifts[last_entity] += current_chain

    return max(gifts.items(), key=lambda kv: len(kv[1]))


class Constraint:
    """Base class for gift composition constraints."""

    def check(self, items: Collection[GiftPart]) -> tuple[int, list[Any]]:
        """Override to describe specific constraint check logic.

        Return number of errors and list of reasons.
        """


class JointConstraint(Constraint):
    """Conjunction between constraints."""

    def __init__(self, *constraints: Constraint):
        self.constraints = constraints

    def check(self, items: Collection[GiftPart]) -> tuple[int, list[Any]]:
        """Return sum of errors of joint subconstraints.

        Reason list is a concatenation of all sublists.
        """
        all_checks = [constraint.check(items) for constraint in self.constraints]
        return (sum(map(operator.itemgetter(0), all_checks)),
                sum(map(operator.itemgetter(1), all_checks), start=[]))


class ItemSetConstraint(Constraint):
    """Constrant: the gift contains a certain amount of gift parts, from a given set."""

    def __init__(self, count: int, *names: str):
        self.allowed_set = set(names)
        self.count = count

    def check(self, items: Collection[GiftPart]) -> tuple[int, list[Any]]:
        """Return number of missing items to reach given count.

        Return self as reason, if there are errors.
        """
        total_checks = 0
        for item in items:
            total_checks += item.name in self.allowed_set

        errors = max(self.count - total_checks, 0)
        reason = []
        if errors:
            reason = [self]

        return max(errors, 0), reason


class ItemsNumberConstraint(Constraint):
    """Constraint: check if total amount of parts is higher/lower than the given amount.

    Default strategy is "lower or equal".
    """

    def __init__(self, count: int, method=operator.le):
        self.count = count
        self.method = method

    def check(self, items: Collection[GiftPart]) -> tuple[int, list[Any]]:
        """Check if item count is higher/lower than the given amount.

        For simplicity, error number is limited to 1.
        Return self as reason, if there are errors.
        """
        errors = not self.method(len(items), self.count)
        reason = []
        if errors:
            reason = [self]

        return errors, reason


@dataclass
class GiftConstraint:
    """Encapsulate the level's current gift constraints."""
    constraint: Constraint
