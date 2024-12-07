"""Basic physics and collisions."""
from dataclasses import dataclass
from typing import SupportsFloat

import desper
import pyglet
from pyglet.sprite import Sprite
from pyglet.window import Window

from . import constants


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


@desper.event_handler('on_add')
class BBox(desper.Controller):
    """Generate a collision rectangle based on Sprite."""
    sprite = desper.ComponentReference(Sprite)

    def on_add(self, entity: int, world: desper.World):
        super().on_add(entity, world)

        self.add_component(CollisionRectangle((self.sprite.width, self.sprite.height),
                                              (self.sprite.image.anchor_x,
                                               self.sprite.image.anchor_x)))


@desper.event_handler('on_mouse_motion')
class PointCheckDebug(desper.Controller):
    """Debug: find and log all objects found."""

    def __init__(self):
        self.window: Window = next(iter(pyglet.app.windows))
        self.game_ratio = constants.VIEW_W / constants.VIEW_H

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        game_space_point = ((x - self.window.viewport[0])
                            * (constants.VIEW_W / self.window.viewport[2]),
                            (y - self.window.viewport[1] * self.game_ratio)
                            * (constants.VIEW_H / self.window.viewport[3]))

        collided = False
        for entity, _ in self.world.get(CollisionRectangle):
            if point_collision(game_space_point, desper.controller(entity, self.world)):
                print(entity)
                collided |= True

        if not collided:
            print('No coll')
