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
    return ((x - viewport[0]) * (gameport[0] / viewport[2]),
            (y - viewport[1]) * (gameport[1] / viewport[3]))


@desper.event_handler('on_mouse_press')
@desper.event_handler('on_mouse_motion')
class MouseToGameSpace(desper.Controller):
    """Map mouse events from window space to game space."""

    def __init__(self):
        self.window: Window = next(iter(pyglet.app.windows))

    def on_mouse_motion(self, x, y, dx, dy):
        return self.world.dispatch('on_mouse_game_motion',
                                   _point_to_gamespace(x, y, self.window.viewport,
                                                       (constants.VIEW_W, constants.VIEW_H)))

    def on_mouse_press(self, x, y):
        return self.world.dispatch('on_mouse_game_press',
                                   _point_to_gamespace(x, y, self.window.viewport,
                                                       (constants.VIEW_W, constants.VIEW_H)))


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


def axis_collision(axis_pos: SupportsFloat, index: int,
                   collision_controller: desper.Controller) -> bool:
    """Check if axis collides with entity.

    use ``index == 0`` for a vertical axis. ``index == 1`` for a
    horizontal axis.
    """
    coll_rectangle: CollisionRectangle = collision_controller.get_component(CollisionRectangle)
    transform: desper.Transform2D = collision_controller.get_component(desper.Transform2D)

    rect_start = transform.position - coll_rectangle.offset
    rect_end = rect_start + coll_rectangle.size
    rect = (*rect_start, *rect_end)

    return rect[index] < axis_pos < rect[2 + index]


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


@desper.event_handler('on_mouse_game_motion')
class PointCheckDebug(desper.Controller):
    """Debug: find and log all objects found."""

    def __init__(self):
        self.window: Window = next(iter(pyglet.app.windows))
        self.game_ratio = constants.VIEW_W / constants.VIEW_H

    def on_mouse_game_motion(self, mouse_position):
        collided = False
        for entity, _ in self.world.get(CollisionRectangle):
            if point_collision(mouse_position, desper.controller(entity, self.world)):
                print(entity)
                collided |= True

        if not collided:
            print('No coll')
