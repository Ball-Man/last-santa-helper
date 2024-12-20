"""Basic physics and collisions."""
from dataclasses import dataclass
from typing import SupportsFloat

import desper
import pyglet
from pyglet.math import Vec2
from pyglet.sprite import Sprite
from pyglet.window import Window

from . import constants


def _point_to_gamespace(x, y, viewport, gameport) -> Vec2:
    """Transform point from window space to game space."""
    return Vec2((x - viewport[0]) * (gameport[0] / viewport[2]),
                (y - viewport[1]) * (gameport[1] / viewport[3]))


class DispatchLaterProcessor(desper.Processor):
    """Dispatch the given events on process."""

    def __init__(self):
        self._queue = []

    def dispatch(self, *event_parameters):
        """Schedule an event to be dispatched later."""
        self._queue.append(event_parameters)

    def process(self, _):
        old_queue = self._queue
        self._queue = []

        for event_tuple in old_queue:
            self.world.dispatch(*event_tuple)


@desper.event_handler('on_mouse_press', 'on_mouse_release')
@desper.event_handler('on_mouse_motion', on_mouse_drag='on_mouse_motion')
class MouseToGameSpace(desper.Controller):
    """Map mouse events from window space to game space."""
    dispatch_later = desper.ProcessorReference(DispatchLaterProcessor)

    def __init__(self):
        self.window: Window = next(iter(pyglet.app.windows))

    def on_mouse_motion(self, x, y, dx, dy, *args):
        return self.world.dispatch('on_mouse_game_motion',
                                   _point_to_gamespace(x, y, self.window.viewport,
                                                       (constants.VIEW_W, constants.VIEW_H)),
                                   _point_to_gamespace(dx, dy,
                                                       (0, 0, self.window.viewport[2],
                                                        self.window.viewport[3]),
                                                       (constants.VIEW_W, constants.VIEW_H)))

    def on_mouse_press(self, x, y, buttons, mod):
        return self.dispatch_later.dispatch('on_mouse_game_press',
                                            _point_to_gamespace(x, y, self.window.viewport,
                                                                (constants.VIEW_W,
                                                                 constants.VIEW_H)),
                                            buttons, mod)

    def on_mouse_release(self, x, y, buttons, mod):
        return self.dispatch_later.dispatch('on_mouse_game_release',
                                            _point_to_gamespace(x, y, self.window.viewport,
                                                                (constants.VIEW_W,
                                                                 constants.VIEW_H)),
                                            buttons, mod)


@dataclass
class CollisionRectangle:
    """Rectangle used for collision detection."""
    size: tuple[SupportsFloat, SupportsFloat]
    offset: tuple[SupportsFloat, SupportsFloat] = 0., 0.


def point_collision(point: tuple[SupportsFloat, SupportsFloat],
                    collision_controller: desper.Controller) -> bool:
    """Check if point collides with entity."""
    x, y = point

    coll_rectangle: CollisionRectangle = collision_controller.get_component(CollisionRectangle)
    transform: desper.Transform2D = collision_controller.get_component(desper.Transform2D)

    rect_start = transform.position - coll_rectangle.offset
    rect_end = rect_start + coll_rectangle.size

    return (x > rect_start.x and x < rect_end.x
            and y > rect_start.y and y < rect_end.y)


def axis_to_rectangle(axis_pos: SupportsFloat, index: int, coll_rectangle: CollisionRectangle,
                      position: tuple[SupportsFloat, SupportsFloat]) -> bool:
    """Explicitly check if axis collides with rectangle, given position.

    See :func:`axis_collision`.
    """
    rect_start = (position[0] - coll_rectangle.offset[0], position[1] - coll_rectangle.offset[1])
    rect_end = (rect_start[0] + coll_rectangle.size[0], rect_start[1] + coll_rectangle.size[1])
    rect = (rect_start[0], rect_start[1], rect_end[0], rect_end[1])

    return rect[index] < axis_pos < rect[2 + index]


def axis_collision(axis_pos: SupportsFloat, index: int,
                   collision_controller: desper.Controller) -> bool:
    """Check if axis collides with entity.

    use ``index == 0`` for a vertical axis. ``index == 1`` for a
    horizontal axis.
    """
    coll_rectangle: CollisionRectangle = collision_controller.get_component(CollisionRectangle)
    transform: desper.Transform2D = collision_controller.get_component(desper.Transform2D)

    return axis_to_rectangle(axis_pos, index, coll_rectangle, transform.position)


def rectangle_collision(collision_controller1: desper.Controller,
                        collision_controller2: desper.Controller) -> bool:
    """Check if two entities (their bbox) collide."""
    transform1 = collision_controller1.get_component(desper.Transform2D)
    rect1_coll = collision_controller1.get_component(CollisionRectangle)
    transform2 = collision_controller2.get_component(desper.Transform2D)
    rect2_coll = collision_controller2.get_component(CollisionRectangle)

    rect1_start = transform1.position - rect1_coll.offset
    rect2_start = transform2.position - rect2_coll.offset

    return (rect1_start.x < rect2_start.x + rect2_coll.size[0]
            and rect1_start.x + rect1_coll.size[0] > rect2_start.x
            and rect1_start.y < rect2_start.y + rect2_coll.size[1]
            and rect1_start.y + rect1_coll.size[1] > rect2_start.y)


@desper.event_handler('on_add')
class BBox(desper.Controller):
    """Generate a collision rectangle based on Sprite."""
    sprite = desper.ComponentReference(Sprite)

    def on_add(self, entity: int, world: desper.World):
        super().on_add(entity, world)

        self.add_component(CollisionRectangle((self.sprite.width, self.sprite.height),
                                              (self.sprite.image.anchor_x,
                                               self.sprite.image.anchor_x)))


class Velocity(Vec2):
    """Velocity component."""


class VelocityProcessor(desper.Processor):
    """Update ``Transform2D`` components using :class:`Velocity`."""

    def process(self, dt):
        for entity, velocity in self.world.get(Velocity):
            transform = self.world.get_component(entity, desper.Transform2D)
            transform.position += velocity * dt


@dataclass
class CollisionAxes:
    """An axes collider.

    Use ``index == 0`` for a vertical axis. ``index == 1`` for a
    horizontal axis.
    """
    pos: SupportsFloat
    index: int


class RectangleToAxisProcessor(desper.Processor):
    """Handle collisions between rectangles and lines.

    This is a simplified simulation that let rectangles
    (main dynamic entities) bounce on axis.
    """

    def process(self, dt):
        axis_entities = self.world.get(CollisionAxes)

        for dynamic_entity, velocity in self.world.get(Velocity):
            coll_rectangle = self.world.get_component(dynamic_entity, CollisionRectangle)
            if coll_rectangle is None:
                continue
            norm_velocity = velocity.normalize()

            # Check collisions with all axis
            reflection = Vec2()
            for _, axes in axis_entities:
                reflection += self._resolve(
                    dt, coll_rectangle, self.world.get_component(dynamic_entity,
                                                                 desper.Transform2D),
                    velocity, norm_velocity, axes)

            # Change velocity (bounce)
            if reflection.x > 0.1:
                velocity.x = -velocity.x

            if reflection.y > 0.1:
                velocity.y = -velocity.y

    def _resolve(self, dt: float, coll_rectangle: CollisionRectangle,
                 dynamic_transform: desper.Transform2D,
                 dynamic_velocity: Velocity, norm_velocity: Velocity, axes: CollisionAxes):
        """Apply velocity and resolve collision with axes."""
        position = dynamic_transform.position
        position = position + dynamic_velocity * dt
        collided = False

        # Adjust collision
        while axis_to_rectangle(axes.pos, axes.index, coll_rectangle, position):
            collided = True
            position = position - norm_velocity

        # If a collision happened, return a vector accordingly
        reflection_axis = [0, 0]
        reflection_axis[axes.index] = 1 * collided

        # If no collision, reset position
        if collided:
            dynamic_transform.position = position

        return Vec2(*reflection_axis)


@desper.event_handler('on_mouse_game_motion')
class PointCheckDebug(desper.Controller):
    """Debug: find and log all objects found."""

    def __init__(self):
        self.window: Window = next(iter(pyglet.app.windows))
        self.game_ratio = constants.VIEW_W / constants.VIEW_H

    def on_mouse_game_motion(self, mouse_position, delta):
        collided = False
        for entity, _ in self.world.get(CollisionRectangle):
            if point_collision(mouse_position, desper.controller(entity, self.world)):
                print(entity)
                collided |= True

        if not collided:
            print('No coll')
